#!/usr/bin/env python3
"""
Scan a Gradle project for all usages that need migration to the Gradle 10
lazy Provider API, using migration-data.json as the source of truth.

Usage:
    python3 scan_usages.py <project-dir> [migration-data.json]

Outputs a grouped list of every hit across three categories:
  A. Removed accessors (set*, is* found in removed_accessors)
  B. Changed-return-type getters (get<Prop> used without .get()/.set()/etc.)
  C. Groovy DSL operator mutations (-=, +=, << on list/set/map properties)

Exit code: 0 if no hits, 1 if hits found.
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

JAVA_EXTS   = (".java", ".kt", ".groovy")
DSL_EXTS    = (".gradle", ".gradle.kts")
ALL_EXTS    = JAVA_EXTS + DSL_EXTS
EXCLUDE_DIRS = {".gradle", "build", ".git", "node_modules", "__pycache__"}

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


def load_lookups(data_file: Path):
    """
    Returns three dicts keyed by bare method/property name:
      removed_accessors: {name -> [entry, ...]}   (Category A)
      getter_names:      {name -> [entry, ...]}   (Category B)
      dsl_props:         {name -> [entry, ...]}   (Category C, list/set/map only)
    """
    with open(data_file) as f:
        data = json.load(f)

    removed_accessors = defaultdict(list)
    getter_names = defaultdict(list)
    dsl_props = defaultdict(list)

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

    return removed_accessors, getter_names, dsl_props


def build_patterns(removed_accessors, getter_names, dsl_props):
    a_names = "|".join(re.escape(n) for n in sorted(removed_accessors))
    cat_a_re = re.compile(r"\b(" + a_names + r")\s*\(") if a_names else None

    b_names = "|".join(re.escape(n) for n in sorted(getter_names))
    cat_b_re = re.compile(r"\b(" + b_names + r")\s*\(\)") if b_names else None

    if dsl_props:
        c_names = "|".join(re.escape(n) for n in sorted(dsl_props))
        cat_c_re = re.compile(r"\b(" + c_names + r")\s*(\+=|-=|<<)")
    else:
        cat_c_re = None

    return cat_a_re, cat_b_re, cat_c_re


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
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
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
        candidates = [cls] + e.get("also_known_as", [])
        for c in candidates:
            if c in gradle_imports:
                simple = cls.rsplit(".", 1)[-1]
                if simple not in confirmed:
                    confirmed.append(simple)
                break
    return confirmed


def scan_file(path: Path, cat_a_re, cat_b_re, cat_c_re,
              removed_accessors, getter_names, dsl_props,
              is_dsl: bool, is_test: bool = False):
    """Scan a single file for all three categories in one pass."""
    hits_a, hits_b, hits_c = [], [], []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return hits_a, hits_b, hits_c

    lines = content.splitlines()
    gradle_imports = extract_gradle_imports(lines) if not is_dsl else set()

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
                    confirmed = confirmed_classes(entries, gradle_imports)
                    hits_a.append({
                        "category": "A",
                        "file": path,
                        "line": lineno,
                        "text": stripped,
                        "method": name,
                        "entries": entries,
                        "confirmed": confirmed,
                    })

        # Category B: changed-return-type getters — skip declarations and test files
        if cat_b_re and not is_decl and not is_test:
            for m in cat_b_re.finditer(line):
                name = m.group(1)
                entries = getter_names.get(name, [])
                if entries:
                    after = line[m.end():]
                    if PROVIDER_CHAIN_RE.match(after):
                        continue  # already chained — ok
                    confirmed = confirmed_classes(entries, gradle_imports)
                    hits_b.append({
                        "category": "B",
                        "file": path,
                        "line": lineno,
                        "text": stripped,
                        "method": name,
                        "entries": entries,
                        "confirmed": confirmed,
                    })

        # Category C: DSL operator mutations (only in DSL files)
        if is_dsl and cat_c_re:
            for m in cat_c_re.finditer(line):
                name = m.group(1)
                entries = dsl_props.get(name, [])
                if entries:
                    hits_c.append({
                        "category": "C",
                        "file": path,
                        "line": lineno,
                        "text": stripped,
                        "method": name,
                        "entries": entries,
                        "confirmed": [],  # DSL files don't have typed imports
                    })

    return hits_a, hits_b, hits_c


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
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <project-dir> [migration-data.json]", file=sys.stderr)
        sys.exit(2)

    project_root = Path(sys.argv[1]).resolve()
    data_file = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        Path(__file__).parent / "migration-data.json"
    )

    if not project_root.is_dir():
        print(f"ERROR: {project_root} is not a directory", file=sys.stderr)
        sys.exit(2)
    if not data_file.exists():
        print(f"ERROR: {data_file} not found", file=sys.stderr)
        sys.exit(2)

    removed_accessors, getter_names, dsl_props = load_lookups(data_file)
    cat_a_re, cat_b_re, cat_c_re = build_patterns(removed_accessors, getter_names, dsl_props)

    all_files, dsl_set, test_set = find_files(project_root)

    n_java = len(all_files) - len(dsl_set)
    n_test = len(test_set)
    print(f"Scanning {len(all_files)} candidate files "
          f"({n_java} Gradle-API Java/Kotlin/Groovy [{n_test} test], "
          f"{len(dsl_set)} DSL) in {project_root}")
    print(f"Patterns: {len(removed_accessors)} Cat-A names, "
          f"{len(getter_names)} Cat-B getters, {len(dsl_props)} Cat-C DSL props")

    all_a, all_b, all_c = [], [], []
    for path in all_files:
        is_dsl = path in dsl_set
        is_test = path in test_set
        ha, hb, hc = scan_file(
            path, cat_a_re, cat_b_re, cat_c_re,
            removed_accessors, getter_names, dsl_props, is_dsl, is_test
        )
        all_a.extend(ha)
        all_b.extend(hb)
        all_c.extend(hc)

    total = len(all_a) + len(all_b) + len(all_c)
    print(f"Results: {len(all_a)} Cat-A, {len(all_b)} Cat-B, {len(all_c)} Cat-C  ({total} total)")
    print("=" * 72)

    print(f"\n## Category A — Removed accessors ({len(all_a)} hits)")
    print_hits(all_a, project_root)

    print(f"\n## Category B — Changed-return-type getters ({len(all_b)} hits)")
    print_hits(all_b, project_root)

    print(f"\n## Category C — Groovy DSL operator mutations ({len(all_c)} hits)")
    print_hits(all_c, project_root)

    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
