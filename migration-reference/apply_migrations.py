#!/usr/bin/env python3
"""
Apply mechanical Cat-A rewrites to a Gradle project, driven by migration-data.json.

Only safe, unambiguous hits are rewritten in place:
  * Category A only (removed accessors)
  * [CONFIRMED] hits where exactly one class matched the file's imports
  * Kinds: boolean, scalar, list, set, map, dir, file, file_collection, other
  * setX(...) call must be fully contained on one line
  * For file_collection: argument must not reference getX() / .x (circular ref)
  * isX() boolean reads are always deferred (read context is ambiguous)

Everything else — Category B, Category C, unconfirmed hits, ambiguous multi-match hits,
read_only kinds, multi-line calls, circular-ref file_collection setters — is deferred
and appended to MIGRATION_NOTES.md at the project root. Weaker models should run this
tool first and then handle only the deferrals.

Usage:
    python3 apply_migrations.py <project-dir> [--dry-run] [--migration-data PATH]
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_usages import (  # noqa: E402
    build_patterns,
    find_files,
    load_lookups,
    scan_file,
)


REWRITE_KINDS = {"boolean", "scalar", "list", "set", "map", "dir", "file", "other"}
FILE_COLLECTION_KIND = "file_collection"


def cap_first(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def find_paren_end(line: str, open_col: int) -> int | None:
    depth = 0
    i = open_col
    in_str = None
    while i < len(line):
        c = line[i]
        if in_str:
            if c == "\\" and i + 1 < len(line):
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in ("'", '"'):
            in_str = c
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def find_method_call(line: str, method: str) -> tuple[int, int, int] | None:
    """Locate the first `.<method>(...)` call fully closed on this line."""
    needle = "." + method + "("
    idx = 0
    while True:
        idx = line.find(needle, idx)
        if idx < 0:
            return None
        open_col = idx + 1 + len(method)
        close_col = find_paren_end(line, open_col)
        if close_col is not None:
            return (idx, open_col, close_col)
        idx += 1


def rewrite_call(line: str, hit_method: str, new_method: str) -> str | None:
    located = find_method_call(line, hit_method)
    if not located:
        return None
    dot_col, open_col, close_col = located

    if hit_method.startswith("set"):
        prop = hit_method[3:]
    elif hit_method.startswith("is"):
        prop = hit_method[2:]
    else:
        return None
    if not prop or not prop[0].isupper():
        return None

    getter = "get" + prop
    arg = line[open_col + 1 : close_col]
    replacement = f".{getter}().{new_method}({arg})"
    return line[:dot_col] + replacement + line[close_col + 1 :]


def argument_references_property(arg: str, prop: str) -> bool:
    getter = "get" + cap_first(prop)
    return (getter + "(") in arg or ("." + prop) in arg


def classify_hit(hit: dict) -> tuple[str, dict | None, str]:
    if hit["category"] != "A":
        return ("defer", None, f"category {hit['category']} is out of scope for this tool")

    confirmed = hit.get("confirmed") or []
    if len(confirmed) == 0:
        return ("defer", None, "unconfirmed receiver — no matching import")
    if len(confirmed) > 1:
        return ("defer", None, f"ambiguous receiver (matched {len(confirmed)} classes)")

    simple = confirmed[0]
    entry = next(
        (e for e in hit["entries"] if e["class"].rsplit(".", 1)[-1] == simple),
        None,
    )
    if entry is None:
        return ("defer", None, "confirmed class has no matching data entry")

    method = hit["method"]
    if method.startswith("is"):
        return ("defer", entry, f"{method}() boolean read: context-dependent rewrite")

    if entry.get("read_only"):
        return ("defer", entry, "read_only property has no setter to rewrite")

    kind = entry["kind"]
    if kind == FILE_COLLECTION_KIND:
        return ("apply", entry, "file_collection setter")
    if kind in REWRITE_KINDS:
        return ("apply", entry, f"{kind} setter")

    return ("defer", entry, f"kind '{kind}' has no mechanical rewrite")


def _class_prop(hit: dict) -> str:
    entries = hit.get("entries") or []
    if not entries:
        return "?"
    e = entries[0]
    return f"{e['class']}.{e['property']}"


def _make_deferral(path: Path, hit: dict, reason: str) -> dict:
    return {
        "file": path,
        "line": hit["line"],
        "method": hit["method"],
        "text": hit["text"],
        "reason": reason,
        "class_prop": _class_prop(hit),
        "category": hit["category"],
    }


def apply_hits_to_file(path: Path, hits: list[dict], dry_run: bool) -> tuple[int, list[dict]]:
    try:
        original = path.read_text(encoding="utf-8", errors="replace")
    except OSError as ex:
        return 0, [_make_deferral(path, h, f"could not read file: {ex}") for h in hits]

    lines = original.splitlines(keepends=True)
    deferrals: list[dict] = []
    applied = 0

    for hit in sorted(hits, key=lambda h: -h["line"]):
        decision, entry, reason = classify_hit(hit)
        if decision == "defer":
            deferrals.append(_make_deferral(path, hit, reason))
            continue

        idx = hit["line"] - 1
        if idx < 0 or idx >= len(lines):
            deferrals.append(_make_deferral(path, hit, "line number out of range"))
            continue

        raw = lines[idx]
        original_line = raw.rstrip("\n").rstrip("\r")
        newline_suffix = raw[len(original_line):]

        kind = entry["kind"]
        prop = entry["property"]

        if kind == FILE_COLLECTION_KIND:
            located = find_method_call(original_line, hit["method"])
            if not located:
                deferrals.append(_make_deferral(path, hit, "setter call not found or spans multiple lines"))
                continue
            _, open_col, close_col = located
            arg = original_line[open_col + 1 : close_col]
            if argument_references_property(arg, prop):
                deferrals.append(_make_deferral(
                    path, hit, "file_collection argument references same property (possible circular ref)"
                ))
                continue
            new_line = rewrite_call(original_line, hit["method"], "setFrom")
        else:
            new_line = rewrite_call(original_line, hit["method"], "set")

        if new_line is None:
            deferrals.append(_make_deferral(path, hit, "setter call not found or spans multiple lines"))
            continue
        if new_line == original_line:
            deferrals.append(_make_deferral(path, hit, "rewrite produced no change"))
            continue

        lines[idx] = new_line + newline_suffix
        applied += 1

    if applied > 0 and not dry_run:
        path.write_text("".join(lines), encoding="utf-8")

    return applied, deferrals


NOTES_HEADER = (
    "# Migration Notes\n\n"
    "Deferred hits logged by `apply_migrations.py`. For each entry, look the class "
    "and property up in `migration-reference/migration-data.json`, apply the rule from "
    "`migration-reference/MIGRATION_RULES.md`, then remove the entry from this file.\n"
)


def write_migration_notes(project_root: Path, deferrals: list[dict], dry_run: bool) -> Path | None:
    if not deferrals:
        return None
    notes_path = project_root / "MIGRATION_NOTES.md"
    existing = notes_path.read_text(encoding="utf-8") if notes_path.exists() else NOTES_HEADER

    by_file: dict[str, list[dict]] = defaultdict(list)
    for d in deferrals:
        try:
            rel = str(d["file"].relative_to(project_root))
        except ValueError:
            rel = str(d["file"])
        by_file[rel].append(d)

    section = ["", "## apply_migrations.py deferrals", ""]
    for rel in sorted(by_file):
        section.append(f"### `{rel}`")
        for d in sorted(by_file[rel], key=lambda x: x["line"]):
            section.append(
                f"- line {d['line']} [Cat-{d['category']}]: `{d['method']}` "
                f"on `{d['class_prop']}` — {d['reason']}"
            )
            section.append(f"  - source: `{d['text']}`")
        section.append("")

    new_content = existing + "\n".join(section) + "\n"
    if not dry_run:
        notes_path.write_text(new_content, encoding="utf-8")
    return notes_path


def main() -> int:
    ap = argparse.ArgumentParser(description=(
        "Apply mechanical Cat-A rewrites to a Gradle project, driven by migration-data.json. "
        "Safe hits are rewritten in place; everything else is deferred to MIGRATION_NOTES.md."
    ))
    ap.add_argument("project_dir", type=Path, help="Path to the cloned repository being migrated")
    ap.add_argument("--migration-data", type=Path,
                    default=Path(__file__).resolve().parent / "migration-data.json")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would change; do not modify files")
    args = ap.parse_args()

    project_root = args.project_dir.resolve()
    if not project_root.is_dir():
        print(f"ERROR: {project_root} is not a directory", file=sys.stderr)
        return 2
    if not args.migration_data.exists():
        print(f"ERROR: {args.migration_data} not found", file=sys.stderr)
        return 2

    removed_accessors, getter_names, dsl_props = load_lookups(args.migration_data)
    cat_a_re, cat_b_re, cat_c_re = build_patterns(removed_accessors, getter_names, dsl_props)

    all_files, dsl_set, test_set = find_files(project_root)

    hits_by_file: dict[Path, list[dict]] = defaultdict(list)
    for path in all_files:
        is_dsl = path in dsl_set
        is_test = path in test_set
        ha, hb, hc = scan_file(
            path, cat_a_re, cat_b_re, cat_c_re,
            removed_accessors, getter_names, dsl_props, is_dsl, is_test,
        )
        hits_by_file[path].extend(ha + hb + hc)

    total_applied = 0
    total_deferrals: list[dict] = []
    for path, hits in hits_by_file.items():
        applied, deferrals = apply_hits_to_file(path, hits, args.dry_run)
        total_applied += applied
        total_deferrals.extend(deferrals)

    notes_path = write_migration_notes(project_root, total_deferrals, args.dry_run)

    mode = "dry run" if args.dry_run else "applied"
    print(f"apply_migrations.py — {mode}")
    print(f"  files scanned:    {len(all_files)}")
    print(f"  rewrites applied: {total_applied}")
    print(f"  deferrals:        {len(total_deferrals)}")
    if notes_path:
        print(f"  deferrals logged: {notes_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
