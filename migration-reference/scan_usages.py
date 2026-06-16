#!/usr/bin/env python3
"""
Scan a Gradle project for all usages that need migration to the Gradle 10
lazy Provider API, using migration-data.json as the source of truth.

Usage:
    python3 scan_usages.py <project-dir> [--distro-pair ID] [--migration-data PATH]

Outputs a grouped list of every hit across these categories:
  A. Removed accessors (set*, is* found in removed_accessors)
  B. Changed-return-type getters (get<Prop> used without .get()/.set()/etc.)
  C. Operator mutations (-=, +=, << on list/set/map properties) — DSL *and* source files
  D. Property assignments (`prop = value` to a now-lazy property) — import-confirmed only
     (bare names are too noisy to report unconfirmed)
  E. Collection ops absent on lazy properties (.remove/.removeAll on list/set/map;
     .filterKeys/.filterValues on map)

Categories C–E catch the Kotlin/Groovy assignment/operator forms that the call-syntax
scanners (A/B) miss. Reads consumed as plain values (`obj.prop` where the getter now
returns Provider<T>), `!boolProp`, and `.map{}`→`.flatMap{}` are intentionally NOT detected:
without real receiver/consumer type analysis they cannot be distinguished from ordinary
code by regex, so they remain compile-error-driven fixes in the verify tasks.

Exit code: 0 if no hits, 1 if hits found.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def resolve_pair(want: str | None = None) -> dict:
    """Resolve a distro pair from ../distro-pairs.json. Returns the pair dict.

    `want` is a pair id; when falsy the manifest's "default" pair is used. The
    manifest lives at the repo root (one level above migration-reference/).
    Shared by apply_migrations.py, which imports this function.
    """
    manifest = Path(__file__).resolve().parent.parent / "distro-pairs.json"
    with open(manifest) as f:
        data = json.load(f)
    pid = want or data["default"]
    pair = next((p for p in data["pairs"] if p["id"] == pid), None)
    if pair is None:
        sys.exit(f"ERROR: distro pair '{pid}' not found in {manifest}")
    return pair


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

JAVA_EXTS   = (".java", ".kt", ".groovy")
DSL_EXTS    = (".gradle", ".gradle.kts")
ALL_EXTS    = JAVA_EXTS + DSL_EXTS

# Exact-name exclusions applied at every depth.
EXCLUDE_DIRS = {".gradle", ".git", "node_modules", "__pycache__"}

# `build` is a special case: it's a Gradle output directory at the root of a
# Gradle project, but it's also a legitimate Java package name (e.g.
# `org.springframework.boot.build` in Spring Boot's buildSrc sources). Exclude
# it only when the parent directory looks like a Gradle project — i.e. it
# contains a Gradle build or settings script.
GRADLE_PROJECT_MARKERS = frozenset({
    "build.gradle", "build.gradle.kts",
    "settings.gradle", "settings.gradle.kts",
})

# Test source path segments — Cat-B is excluded from these (too many false positives
# from test code calling getOutput(), getName() etc. on non-Gradle types).
TEST_PATH_SEGMENTS = {"/test/", "/dockerTest/", "/integrationTest/", "/systemTest/"}

# Accessor names that belong to org.gradle.api.Task or other non-migrated base types.
# These appear in migration-data.json only because a *different* class has a property
# with the same name (e.g. PluginDeclaration.description), so they produce false
# positives whenever task.setDescription(...) / task.setGroup(...) is called.
# These Task methods are NOT migrated to lazy properties in Gradle 10.
TASK_ONLY_ACCESSORS = {
    "setDescription", "setGroup", "setEnabled", "setDependsOn",
    "setOnlyIf", "setActions", "setFinalizedBy", "setMustRunAfter",
    "setShouldRunAfter", "setTimeout", "setDidWork",
}

# getX() is fine when chained with any of these Provider API methods
PROVIDER_CHAIN_RE = re.compile(
    r"\s*\.\s*(?:get|getOrNull|getOrElse|set|from|setFrom|add|addAll|"
    r"put|putAll|isPresent|map|flatMap|orElse|zip|convention|value|"
    r"filter|forUseAtConfigurationTime)\s*[(\[]"
)

# A line that is a method *declaration* (not a call site) — skip for Cat-A/B.
# Handles annotations before or after access modifiers, e.g.:
#   "public void setFoo("
#   "public @Nullable FileCollection getClasspath() {"
#   "@Override protected boolean isFoo() {"
MODIFIERS = (
    r"(?:(?:@\w+(?:\([^)]*\))?\s+)*"            # zero or more annotations
    r"(?:public|protected|private|default|static|final|"
    r"abstract|synchronized|native|strictfp)\s+)*"
    r"(?:@\w+(?:\([^)]*\))?\s+)*"               # annotations after modifiers
)
RETURN_TYPES = (
    r"(?:void|boolean|int|long|double|float|short|byte|char|"
    r"String|File|List|Set|Map|Collection|Iterable|"
    r"Property|Provider|ListProperty|SetProperty|MapProperty|"
    r"DirectoryProperty|RegularFileProperty|ConfigurableFileCollection|"
    r"\w+(?:<[^>]*>)?)\s+"
)
METHOD_DECL_RE = re.compile(
    r"^\s*" + MODIFIERS + RETURN_TYPES + r"(?:set|get|is)\w+\s*\("
)

# Single-line comments — skip entirely
COMMENT_LINE_RE = re.compile(r"^\s*(?://|/?\*)")


# ------------------------------------------------------------------
# Load and build lookup tables
# ------------------------------------------------------------------

def cap_first(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


# Property names that belong to org.gradle.api.Task (or other non-migrated base
# types) and are therefore NOT lazy-migrated. Derived from TASK_ONLY_ACCESSORS so
# Category D (assignment) doesn't flag `task.description = ...`, `task.group = ...`, etc.
TASK_ONLY_PROPS = {acc[3].lower() + acc[4:] for acc in TASK_ONLY_ACCESSORS}  # setFoo -> foo

# Kinds that can appear on the left of an assignment (everything except read_only).
ASSIGNABLE_KINDS = {
    "boolean", "scalar", "list", "set", "map", "dir", "file", "file_collection", "other",
}


def load_lookups(data_file: Path):
    """
    Returns dicts keyed by bare method/property name:
      removed_accessors: {name -> [entry, ...]}   (Category A — set*/is* call removed)
      getter_names:      {name -> [entry, ...]}   (Category B — get<Prop>() call, return type changed)
      dsl_props:         {name -> [entry, ...]}   (Category C — +=/-=/<< operator, list/set/map)
      assign_props:      {prop -> [entry, ...]}   (Category D — `prop = value` assignment, assignable kinds)
      coll_props:        {prop -> [entry, ...]}   (Category E — .remove()/.removeAll() on list/set/map)
      map_props:         {prop -> [entry, ...]}   (Category E — .filterKeys/.filterValues on map)
    """
    with open(data_file) as f:
        data = json.load(f)

    removed_accessors = defaultdict(list)
    getter_names = defaultdict(list)
    dsl_props = defaultdict(list)
    assign_props = defaultdict(list)
    coll_props = defaultdict(list)
    map_props = defaultdict(list)

    for entry in data:
        prop = entry["property"]
        kind = entry["kind"]

        for acc in entry.get("removed_accessors", []):
            name = acc.split("(")[0]
            if name:
                removed_accessors[name].append(entry)

        getter_name = "get" + cap_first(prop)
        getter_names[getter_name].append(entry)

        if kind in ("list", "set", "map"):
            dsl_props[prop].append(entry)
            coll_props[prop].append(entry)
        if kind == "map":
            map_props[prop].append(entry)

        # Category D: assignment `prop = value` to a now-lazy property. Exclude Task-only
        # property names (description/group/enabled/...) which are not lazy-migrated.
        if kind in ASSIGNABLE_KINDS and prop not in TASK_ONLY_PROPS:
            assign_props[prop].append(entry)

    return removed_accessors, getter_names, dsl_props, assign_props, coll_props, map_props


def build_patterns(removed_accessors, getter_names, dsl_props, assign_props, coll_props, map_props):
    a_names = "|".join(re.escape(n) for n in sorted(removed_accessors))
    cat_a_re = re.compile(r"\b(" + a_names + r")\s*\(") if a_names else None

    b_names = "|".join(re.escape(n) for n in sorted(getter_names))
    cat_b_re = re.compile(r"\b(" + b_names + r")\s*\(\)") if b_names else None

    if dsl_props:
        c_names = "|".join(re.escape(n) for n in sorted(dsl_props))
        cat_c_re = re.compile(r"\b(" + c_names + r")\s*(\+=|-=|<<)")
    else:
        cat_c_re = None

    # Category D: `prop = value` (single `=`, not ==/!=/<=/>=/+=/-=/etc.). The name is
    # preceded by a non-word char (start, whitespace, `.` for `recv.prop`, `(`), so a
    # dotted receiver matches but a longer identifier (`myEncoding`) does not.
    if assign_props:
        d_names = "|".join(re.escape(n) for n in sorted(assign_props))
        cat_d_re = re.compile(r"(?<!\w)(" + d_names + r")\s*=(?!=)")
    else:
        cat_d_re = None

    # Category E: collection ops that don't exist on lazy properties.
    if coll_props:
        e_coll_names = "|".join(re.escape(n) for n in sorted(coll_props))
        cat_e_coll_re = re.compile(r"(?<!\w)(" + e_coll_names + r")\s*\.\s*(remove|removeAll)\s*\(")
    else:
        cat_e_coll_re = None
    if map_props:
        e_map_names = "|".join(re.escape(n) for n in sorted(map_props))
        cat_e_map_re = re.compile(r"(?<!\w)(" + e_map_names + r")\s*\.\s*(filterKeys|filterValues)\s*[({]")
    else:
        cat_e_map_re = None

    return cat_a_re, cat_b_re, cat_c_re, cat_d_re, cat_e_coll_re, cat_e_map_re


# ------------------------------------------------------------------
# File collection
# ------------------------------------------------------------------

def find_files(root: Path) -> tuple[list[Path], set[Path], set[Path]]:
    """
    Returns (all_candidate_files, dsl_set, test_set).

    For Java/Kotlin/Groovy files: only include files that contain 'org.gradle'.
    All build scripts (*.gradle, *.gradle.kts) are always included.

    test_set: files under test source directories (Cat-B excluded for these).
    """
    java_files = []
    dsl_files = []
    test_files = set()

    for dirpath, dirnames, filenames in os.walk(root):
        is_gradle_project_dir = any(f in GRADLE_PROJECT_MARKERS for f in filenames)
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS
            and not (d == "build" and is_gradle_project_dir)
        ]
        for fname in filenames:
            path = Path(dirpath) / fname
            path_str = str(path)
            if fname.endswith(DSL_EXTS):
                dsl_files.append(path)
            elif fname.endswith(JAVA_EXTS):
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    if "org.gradle" in content:
                        java_files.append(path)
                        if any(seg in path_str for seg in TEST_PATH_SEGMENTS):
                            test_files.add(path)
                except OSError:
                    pass

    all_files = java_files + dsl_files
    return all_files, set(dsl_files), test_files


# ------------------------------------------------------------------
# Single-pass file scanner
# ------------------------------------------------------------------

IMPORT_RE = re.compile(r"^\s*import\s+(org\.gradle[\w.]+)")


def extract_gradle_imports(lines: list[str]) -> set[str]:
    """Return set of fully-qualified org.gradle class names imported by the file."""
    imports = set()
    for line in lines:
        m = IMPORT_RE.match(line)
        if m:
            imports.add(m.group(1).rstrip(";"))
    return imports


def confirmed_classes(entries: list[dict], gradle_imports: set[str]) -> list[str]:
    """
    Return simple class names from the entries whose FQN (or that of a
    known_also_as subtype) appears in the file's gradle imports.

    An empty list means no import match was found — hit is likely a
    false positive, but still show it for human review.
    """
    confirmed = []
    for e in entries:
        cls = e["class"]
        candidates = [cls] + e.get("inheriting_subtypes", [])
        for c in candidates:
            if c in gradle_imports:
                simple = cls.rsplit(".", 1)[-1]
                if simple not in confirmed:
                    confirmed.append(simple)
                break
    return confirmed


# A property name on the left of an assignment is a *declaration* (a new local),
# not a property mutation, when directly preceded by val/var/def/const val.
DECL_BEFORE_RE = re.compile(r"\b(?:val|var|def|const\s+val)\s+$")


def scan_file(path: Path, cat_a_re, cat_b_re, cat_c_re, cat_d_re, cat_e_coll_re, cat_e_map_re,
              removed_accessors, getter_names, dsl_props, assign_props, coll_props, map_props,
              is_dsl: bool, is_test: bool = False) -> list[dict]:
    """Scan a single file for all categories in one pass. Returns a flat list of hit dicts,
    each tagged with its `category` (A–E).

    Category D (`prop = value` assignment) matches bare property names and would be very noisy
    on real code (most matches are unrelated locals/named-args), so only *import-confirmed*
    Cat-D hits are emitted."""
    hits: list[dict] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return hits

    lines = content.splitlines()
    gradle_imports = extract_gradle_imports(lines) if not is_dsl else set()

    def add(cat, lineno, stripped, name, entries, *, op=None, confirmed=None):
        if confirmed is None:
            # DSL files have no typed imports, so confirmation is import-based only for source.
            confirmed = confirmed_classes(entries, gradle_imports) if not is_dsl else []
        hit = {
            "category": cat,
            "file": path,
            "line": lineno,
            "text": stripped,
            "method": name,
            "entries": entries,
            "confirmed": confirmed,
        }
        if op is not None:
            hit["op"] = op
        hits.append(hit)

    for lineno, line in enumerate(lines, 1):
        stripped = line.rstrip()
        # Skip comment lines — avoids false positives from migration notes
        if COMMENT_LINE_RE.match(line):
            continue
        is_decl = bool(METHOD_DECL_RE.match(line))

        # Category A: removed accessors — skip declarations and known Task-only methods
        if cat_a_re and not is_decl:
            for m in cat_a_re.finditer(line):
                name = m.group(1)
                if name in TASK_ONLY_ACCESSORS:
                    continue
                entries = removed_accessors.get(name, [])
                if entries:
                    add("A", lineno, stripped, name, entries)

        # Category B: changed-return-type getters — skip declarations and test files
        if cat_b_re and not is_decl and not is_test:
            for m in cat_b_re.finditer(line):
                name = m.group(1)
                entries = getter_names.get(name, [])
                if entries:
                    if PROVIDER_CHAIN_RE.match(line[m.end():]):
                        continue  # already chained — ok
                    add("B", lineno, stripped, name, entries)

        # Category C: operator mutations (+=/-=/<<). Now scanned in source files too
        # (not just DSL) — e.g. `jvmArgumentProviders += x` in a .kt convention plugin.
        if cat_c_re and not is_decl:
            for m in cat_c_re.finditer(line):
                name = m.group(1)
                entries = dsl_props.get(name, [])
                if entries:
                    add("C", lineno, stripped, name, entries, op=m.group(2))

        # Category D: `prop = value` assignment to a now-lazy property (the Kotlin/Groovy
        # property-assignment form the call-syntax scanners miss). Skip declarations and tests.
        # Bare-name matching is noisy, so emit only import-confirmed hits.
        if cat_d_re and not is_decl and not is_test:
            for m in cat_d_re.finditer(line):
                if DECL_BEFORE_RE.search(line[:m.start()]):
                    continue  # `val prop = ...` — a new local, not a property mutation
                name = m.group(1)
                entries = assign_props.get(name, [])
                if not entries:
                    continue
                conf = confirmed_classes(entries, gradle_imports) if not is_dsl else []
                if conf:
                    add("D", lineno, stripped, name, entries, op="=", confirmed=conf)

        # Category E: collection ops absent on lazy properties (.remove/.removeAll on
        # list/set/map; .filterKeys/.filterValues on map). Skip tests.
        if not is_test:
            if cat_e_coll_re:
                for m in cat_e_coll_re.finditer(line):
                    name = m.group(1)
                    entries = coll_props.get(name, [])
                    if entries:
                        add("E", lineno, stripped, name, entries, op=m.group(2))
            if cat_e_map_re:
                for m in cat_e_map_re.finditer(line):
                    name = m.group(1)
                    entries = map_props.get(name, [])
                    if entries:
                        add("E", lineno, stripped, name, entries, op=m.group(2))

    return hits


# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------

def format_context(entries):
    seen = set()
    parts = []
    for e in entries:
        key = f"{e['class']}.{e['property']}"
        if key not in seen:
            seen.add(key)
            parts.append(f"{key} ({e['kind']})")
    return " | ".join(parts)


def print_hits(hits: list[dict], project_root: Path):
    if not hits:
        print("  (none)")
        return

    by_file = defaultdict(list)
    for h in hits:
        try:
            rel = str(h["file"].relative_to(project_root))
        except ValueError:
            rel = str(h["file"])
        by_file[rel].append(h)

    for rel_path in sorted(by_file):
        print(f"\n  {rel_path}")
        for h in sorted(by_file[rel_path], key=lambda x: x["line"]):
            confirmed = h.get("confirmed", [])
            # Mark confirmed hits (import found) vs unconfirmed (possible false positive)
            marker = f"[CONFIRMED: {', '.join(confirmed)}]" if confirmed else "[unconfirmed - check type]"
            print(f"    line {h['line']:4d}: {h['text'].strip()}")
            print(f"             {marker}")
            print(f"             → {format_context(h['entries'])}")


def main():
    ap = argparse.ArgumentParser(description=(
        "Scan a Gradle project for usages that need migration to the lazy Provider API, "
        "driven by a distro pair's migration-data.json."
    ))
    ap.add_argument("project_dir", type=Path, help="Path to the Gradle project to scan")
    ap.add_argument("--distro-pair", default=None,
                    help="Distro pair id from distro-pairs.json (default: the manifest's \"default\" pair)")
    ap.add_argument("--migration-data", type=Path, default=None,
                    help="Override the migration-data.json path (default: derived from the distro pair)")
    args = ap.parse_args()

    # The migration data is selected per distro pair and lives under
    # migration-reference/distro-pairs/<pair-id>/. --migration-data overrides this.
    if args.migration_data is not None:
        data_file = args.migration_data
    else:
        pair = resolve_pair(args.distro_pair)
        data_file = Path(__file__).resolve().parent / "distro-pairs" / pair["id"] / "migration-data.json"

    project_root = args.project_dir.resolve()

    if not project_root.is_dir():
        print(f"ERROR: {project_root} is not a directory", file=sys.stderr)
        sys.exit(2)
    if not data_file.exists():
        print(f"ERROR: {data_file} not found", file=sys.stderr)
        sys.exit(2)

    removed_accessors, getter_names, dsl_props, assign_props, coll_props, map_props = load_lookups(data_file)
    pats = build_patterns(removed_accessors, getter_names, dsl_props, assign_props, coll_props, map_props)

    all_files, dsl_set, test_set = find_files(project_root)

    n_java = len(all_files) - len(dsl_set)
    n_test = len(test_set)
    print(f"Scanning {len(all_files)} candidate files "
          f"({n_java} Gradle-API Java/Kotlin/Groovy [{n_test} test], "
          f"{len(dsl_set)} DSL) in {project_root}")
    print(f"Patterns: {len(removed_accessors)} Cat-A names, {len(getter_names)} Cat-B getters, "
          f"{len(dsl_props)} Cat-C operator props, {len(assign_props)} Cat-D assignable props, "
          f"{len(coll_props)} Cat-E collection props")

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for path in all_files:
        is_dsl = path in dsl_set
        is_test = path in test_set
        for h in scan_file(path, *pats, removed_accessors, getter_names, dsl_props,
                           assign_props, coll_props, map_props, is_dsl, is_test):
            by_cat[h["category"]].append(h)

    total = sum(len(v) for v in by_cat.values())
    counts = "  ".join(f"{len(by_cat[c])} Cat-{c}" for c in "ABCDE")
    print(f"Results: {counts}  ({total} total)")
    print("=" * 72)

    sections = [
        ("A", "Removed accessors (set*/is* call removed)"),
        ("B", "Changed-return-type getters (get<Prop>() used as a plain value)"),
        ("C", "Operator mutations (+=/-=/<< on list/set/map)"),
        ("D", "Property assignments (`prop = value`; import-confirmed only)"),
        ("E", "Collection ops absent on lazy properties (.remove/.filterKeys/...)"),
    ]
    for cat, title in sections:
        print(f"\n## Category {cat} — {title} ({len(by_cat[cat])} hits)")
        print_hits(by_cat[cat], project_root)

    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
