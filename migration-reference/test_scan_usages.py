#!/usr/bin/env python3
"""Tests for the scanner's detection categories (C-in-source, D, E) and apply_migrations'
Cat-D detect-only policy.

Pytest-style: `def test_*` functions with plain asserts (no `import pytest` needed to define
them). Run either way:
    python3 -m pytest test_scan_usages.py        # if pytest is installed
    python3 test_scan_usages.py                  # standalone fallback runner (no deps)

Must be run from the migration-reference/ directory (imports scan_usages / apply_migrations).
"""
import json
import tempfile
from pathlib import Path

from scan_usages import load_lookups, build_patterns, scan_file
from apply_migrations import classify_hit

# Minimal migration data covering one entry per relevant kind.
DATA = [
    {"class": "org.gradle.process.BaseExecSpec", "property": "standardOutput", "kind": "other",
     "removed_accessors": ["setStandardOutput(java.io.OutputStream)"], "inheriting_subtypes": []},
    {"class": "org.gradle.api.tasks.compile.CompileOptions", "property": "encoding", "kind": "scalar",
     "removed_accessors": [], "inheriting_subtypes": []},
    {"class": "org.gradle.process.ExecSpec", "property": "args", "kind": "list",
     "removed_accessors": [], "inheriting_subtypes": []},
    {"class": "org.gradle.process.ProcessForkOptions", "property": "environment", "kind": "map",
     "removed_accessors": [], "inheriting_subtypes": []},
    {"class": "org.gradle.api.tasks.testing.Test", "property": "classpath", "kind": "file_collection",
     "removed_accessors": [], "inheriting_subtypes": []},
    {"class": "org.gradle.caching.local.DirectoryBuildCache", "property": "directory", "kind": "dir",
     "removed_accessors": [], "inheriting_subtypes": []},
    # Task-only: must be excluded from Cat-D assignment detection.
    {"class": "org.gradle.api.Task", "property": "description", "kind": "scalar",
     "removed_accessors": [], "inheriting_subtypes": []},
]

_tmp = tempfile.TemporaryDirectory()
_TMP = Path(_tmp.name)
_data_file = _TMP / "migration-data.json"
_data_file.write_text(json.dumps(DATA))
_LOOKUPS = load_lookups(_data_file)
_PATS = build_patterns(*_LOOKUPS)


def scan(src: str, ext: str = ".kt", is_dsl=False, is_test=False):
    """Write a snippet to a temp file and return its scan hits."""
    f = _TMP / f"snippet{ext}"
    f.write_text(src)
    return scan_file(f, *_PATS, *_LOOKUPS, is_dsl, is_test)


def cat(hits, category):
    return [h for h in hits if h["category"] == category]


def mkD(method, kind, confirmed):
    cls = next(e["class"] for e in DATA if e["property"] == method)
    return {"category": "D", "method": method, "confirmed": confirmed,
            "entries": [{"class": cls, "property": method, "kind": kind}]}


# --- Cat-D: property assignment (import-confirmed only) ---

def test_cat_d_detects_confirmed_assignment():
    d = cat(scan("import org.gradle.api.tasks.compile.CompileOptions\n"
                 "fun f(o: CompileOptions) { o.encoding = \"UTF-8\" }\n"), "D")
    assert len(d) == 1 and d[0]["method"] == "encoding"


def test_cat_d_confirmed_via_import():
    d = cat(scan("import org.gradle.api.tasks.compile.CompileOptions\n"
                 "fun f(o: CompileOptions) { o.encoding = \"UTF-8\" }\n"), "D")
    assert d and d[0]["confirmed"] == ["CompileOptions"]


def test_cat_d_detects_confirmed_file_collection():
    d = cat(scan("import org.gradle.api.tasks.testing.Test\n"
                 "fun f(t: Test){ t.classpath = files(x) }\n"), "D")
    assert any(h["method"] == "classpath" for h in d)


def test_cat_d_suppresses_unconfirmed_bare_assignment():
    # No import of the owning type -> unconfirmed -> not reported.
    assert not cat(scan("standardOutput = out\n"), "D")


def test_cat_d_ignores_declaration():
    assert not cat(scan("import org.gradle.api.tasks.compile.CompileOptions\nval encoding = \"x\"\n"), "D")


def test_cat_d_ignores_equality_comparison():
    assert not cat(scan("import org.gradle.api.tasks.compile.CompileOptions\nif (o.encoding == \"x\") {}\n"), "D")


def test_cat_d_ignores_longer_identifier():
    assert not cat(scan("import org.gradle.api.tasks.compile.CompileOptions\nmyEncoding = \"x\"\n"), "D")


def test_cat_d_excludes_task_only_property():
    assert not cat(scan("description = \"x\"\n"), "D")


def test_cat_d_skipped_in_test_source():
    src = "import org.gradle.api.tasks.compile.CompileOptions\no.encoding = \"x\"\n"
    assert not cat(scan(src, is_test=True), "D")


# --- Cat-C: operator mutation in .kt source (not just DSL) ---

def test_cat_c_in_kotlin_source():
    c = cat(scan("args += listOf(\"a\")\n"), "C")
    assert len(c) == 1 and c[0]["op"] == "+="


def test_cat_c_plusassign_not_also_cat_d():
    assert not cat(scan("args += listOf(\"a\")\n"), "D")


# --- Cat-E: collection ops absent on lazy properties ---

def test_cat_e_filter_keys():
    e = cat(scan("environment.filterKeys { it != 1 }\n"), "E")
    assert any(h["op"] == "filterKeys" for h in e)


def test_cat_e_remove():
    e = cat(scan("environment.remove(\"X\")\n"), "E")
    assert any(h["op"] == "remove" for h in e)


# --- comment guard ---

def test_comment_line_skipped():
    assert not scan("// o.encoding = \"x\"\n")


# --- apply_migrations: Cat-D is detect-only (always deferred) ---

def test_classify_defers_confirmed_cat_d():
    assert classify_hit(mkD("encoding", "scalar", ["CompileOptions"]))[0] == "defer"


def test_classify_defers_unconfirmed_cat_d():
    assert classify_hit(mkD("encoding", "scalar", []))[0] == "defer"


def _run_standalone() -> int:
    """Minimal runner so the file also works without pytest installed."""
    tests = sorted(n for n, v in globals().items() if n.startswith("test_") and callable(v))
    failed = []
    for name in tests:
        try:
            globals()[name]()
            print(f"PASS: {name}")
        except Exception as ex:  # noqa: BLE001 - report any failure
            failed.append(name)
            print(f"FAIL: {name}: {ex!r}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
