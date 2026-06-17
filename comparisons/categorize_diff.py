#!/usr/bin/env python3
"""
Categorize the diff of one migration run into buckets so the `/g10-compare`
skill can report the *core* migration churn separately from non-migration noise.

Usage:
    python3 categorize_diff.py <repo-dir> --base <ref> --branch <ref> [--markdown]

Computes `git diff <base>...<branch>` (three-dot, the same form the REPORT files
use) inside an already-fetched clone, with the generated artifacts
(MIGRATION_NOTES.md, REPORT-*.md) excluded, and splits the changed *lines*
(additions + deletions) into four disjoint buckets that sum exactly to the total:

  formatting  — whitespace/indent/blank-line-only churn (exact, via `git diff -w`)
  warnings    — warnings-as-errors & deprecation-suppression flag changes (pattern)
  infra       — other throwaway-preview relaxations: verification-metadata blanket
                trust, Develocity/build-scan disabling (path + pattern)
  core        — everything left = the genuine Provider-API migration work

`formatting` is exact (the delta between the normal diff and a whitespace-ignoring
diff). `warnings` and `infra` are content/path *heuristics* — see the PATTERNS
constants below; they are echoed in the JSON output so a reader can audit exactly
what matched. `core` is the residual, so the four buckets always reconcile to the
report-compatible total.

Outputs JSON to stdout (or a markdown table fragment with --markdown).
Exit code: 0 on success, non-zero on git/usage errors.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Configuration — tune these against real diffs; they are emitted in
# the JSON so every comparison can show exactly what was matched.
# ------------------------------------------------------------------

# Artifacts the migration itself generates — never count them as migration churn.
ARTIFACT_PATHSPECS = [":(exclude)MIGRATION_NOTES.md", ":(exclude)REPORT-*.md"]

# Warnings-as-errors flips and deprecation suppressions (case-insensitive).
WARNINGS_PATTERNS = [
    r"allWarningsAsErrors",
    r"warningsAsErrors",
    r"-?Werror\b",
    r"\bwerror\b",
    r"disable\.werror",
    r"deprecation",
]

# Path that is, by its nature, always an infra relaxation when touched.
INFRA_PATHS = ["gradle/verification-metadata.xml"]

# Other throwaway-preview infra relaxations, matched by content (case-insensitive):
# Develocity / build-scan disabling.
INFRA_PATTERNS = [
    r"develocity",
    r"gradle-?[eE]nterprise",
    r"buildScan",
    r"build-scan",
]

_WARNINGS_RE = re.compile("|".join(WARNINGS_PATTERNS), re.IGNORECASE)
_INFRA_RE = re.compile("|".join(INFRA_PATTERNS), re.IGNORECASE)


# ------------------------------------------------------------------
# git plumbing
# ------------------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    """Run a git command in `repo` and return stdout (text)."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"ERROR: git {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout


def _range(base: str, branch: str) -> str:
    return f"{base}...{branch}"


def numstat(repo: Path, base: str, branch: str, ignore_ws: bool):
    """Return (files, added, deleted) from --numstat over the diff, artifacts excluded.

    Binary files (numstat emits '-' for counts) contribute 0 lines but still count
    as a changed file.
    """
    args = ["diff", "--numstat"]
    if ignore_ws:
        args += ["-w", "--ignore-blank-lines"]
    args += [_range(base, branch), "--", ".", *ARTIFACT_PATHSPECS]
    files = added = deleted = 0
    for line in _git(repo, *args).splitlines():
        if not line.strip():
            continue
        a, d, _path = line.split("\t", 2)
        files += 1
        if a != "-":
            added += int(a)
        if d != "-":
            deleted += int(d)
    return files, added, deleted


def classify_lines(repo: Path, base: str, branch: str):
    """Per-line pass over the whitespace-ignoring diff.

    Returns dict with line counts and the set of files touched per category,
    for the warnings / infra buckets. The whitespace-ignoring diff is used so
    that whitespace-only lines are already excluded here (they are accounted for
    separately as `formatting`).
    """
    args = ["diff", "-w", "--ignore-blank-lines",
            _range(base, branch), "--", ".", *ARTIFACT_PATHSPECS]
    out = _git(repo, *args)

    warnings = infra = total_w = 0
    warnings_files: set[str] = set()
    infra_files: set[str] = set()
    cur_file = None

    for line in out.splitlines():
        # File headers first (so their +++/--- prefixes are never miscounted).
        if line.startswith("+++ b/"):
            cur_file = line[6:]
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        # Count only content lines: a single leading + or - (not an empty line).
        if not line or line[0] not in "+-":
            continue
        total_w += 1
        path = cur_file or ""
        content = line[1:]
        # Precedence: infra-by-path > warnings > infra-by-content > core.
        if any(path == p or path.endswith("/" + p) for p in INFRA_PATHS):
            infra += 1
            infra_files.add(path)
        elif _WARNINGS_RE.search(content):
            warnings += 1
            warnings_files.add(path)
        elif _INFRA_RE.search(content):
            infra += 1
            infra_files.add(path)
        # else: core — counted as the residual below.

    return {
        "warnings": warnings,
        "infra": infra,
        "total_w": total_w,
        "warnings_files": sorted(warnings_files),
        "infra_files": sorted(infra_files),
    }


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def categorize(repo: Path, base: str, branch: str) -> dict:
    files_incl, add_incl, del_incl = numstat(repo, base, branch, ignore_ws=False)
    total = add_incl + del_incl

    # Whitespace-ignoring totals → formatting is the exact difference.
    _f, add_w, del_w = numstat(repo, base, branch, ignore_ws=True)
    total_w = add_w + del_w
    formatting = max(0, total - total_w)

    cls = classify_lines(repo, base, branch)
    warnings = cls["warnings"]
    infra = cls["infra"]
    # Core is the residual of the non-whitespace churn, so the four buckets
    # always reconcile to `total` even if the textual and numstat -w counts
    # differ by an edge-case line or two.
    core = max(0, total_w - warnings - infra)
    # Absorb any reconciliation drift into core so buckets sum to total exactly.
    core += total - (formatting + warnings + infra + core)

    return {
        "base": base,
        "branch": branch,
        "files_changed": files_incl,
        "lines": {
            "total": total,
            "added": add_incl,
            "deleted": del_incl,
            "core": core,
            "formatting": formatting,
            "warnings": warnings,
            "infra": infra,
        },
        "files_touched": {
            "warnings": cls["warnings_files"],
            "infra": cls["infra_files"],
        },
        "patterns": {
            "warnings": WARNINGS_PATTERNS,
            "infra_paths": INFRA_PATHS,
            "infra_content": INFRA_PATTERNS,
            "artifacts_excluded": ARTIFACT_PATHSPECS,
        },
    }


def to_markdown(r: dict) -> str:
    L = r["lines"]
    return "\n".join([
        f"| **Files changed (excl. artifacts)** | {r['files_changed']} |",
        f"| **Total lines changed** | +{L['added']} / −{L['deleted']} ({L['total']} total) |",
        f"| − Formatting / whitespace | {L['formatting']} |",
        f"| − Warnings-as-errors & deprecations | {L['warnings']} "
        f"({len(r['files_touched']['warnings'])} files) |",
        f"| − Other infra relaxations | {L['infra']} "
        f"({len(r['files_touched']['infra'])} files) |",
        f"| **= Core migration changes** | **{L['core']}** |",
    ])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", type=Path, help="path to an already-fetched clone")
    ap.add_argument("--base", required=True, help="base ref (e.g. origin/main)")
    ap.add_argument("--branch", required=True, help="migration branch ref")
    ap.add_argument("--markdown", action="store_true",
                    help="emit a markdown table fragment instead of JSON")
    args = ap.parse_args()

    if not (args.repo / ".git").exists():
        sys.exit(f"ERROR: {args.repo} is not a git clone")

    result = categorize(args.repo, args.base, args.branch)
    if args.markdown:
        print(to_markdown(result))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
