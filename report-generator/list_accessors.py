#!/usr/bin/env python3
"""List all removed accessor method names from migration-data.json."""
import json
import pathlib

data = json.loads((pathlib.Path(__file__).parent / "migration-data.json").read_text())
accessors = set()
for entry in data:
    for acc in entry.get("removed_accessors", []):
        method = acc.split("(")[0]
        if method.startswith(("set", "is", "get")):
            accessors.add(method)
for a in sorted(accessors):
    print(a)
