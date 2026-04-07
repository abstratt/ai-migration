#!/usr/bin/env python3
"""Look up migration entries for classes matching a keyword.

Usage: python3 lookup_class.py <keyword>
Example: python3 lookup_class.py Test
"""
import json
import pathlib
import sys

keyword = sys.argv[1] if len(sys.argv) > 1 else ""
data = json.loads((pathlib.Path(__file__).parent / "migration-data.json").read_text())
for e in data:
    if keyword.lower() in e["class"].lower():
        accessors = ", ".join(e.get("removed_accessors", [])) or "(none)"
        print(f"{e['class']} | {e['property']} | {e['kind']} | {accessors}")
