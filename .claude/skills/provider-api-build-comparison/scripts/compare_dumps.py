#!/usr/bin/env python3
"""Compare two task-dump.init.gradle JSON files (before vs after).

Usage: compare_dumps.py before.json after.json [--verbose]
"""
import json
import sys


def short(v, n=110):
    s = json.dumps(v, sort_keys=True) if not isinstance(v, str) else v
    return s if len(s) <= n else s[: n - 3] + "..."


def diff_map(a, b):
    """Return (only_a, only_b, changed) key lists for two dicts."""
    a, b = a or {}, b or {}
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return only_a, only_b, changed


def full(v):
    return v if isinstance(v, str) else json.dumps(v, sort_keys=True)


def window(s, at, n):
    """The n characters of s around position at, with ellipses where cut."""
    start = max(0, min(at - n // 3, len(s) - n))
    end = min(len(s), start + n)
    return ("..." if start > 0 else "") + s[start:end] + ("..." if end < len(s) else "")


def pair(a, b, n):
    """Display forms of two different values that are guaranteed to look different.

    Values are always compared in full; only the display is shortened. When the
    shortened forms would be equal, show the text around the first difference.
    """
    fa, fb = full(a), full(b)
    sa, sb = short(fa, n), short(fb, n)
    if sa != sb:
        return sa, sb, ""
    at = next((i for i, (x, y) in enumerate(zip(fa, fb)) if x != y), min(len(fa), len(fb)))
    note = f" (first difference at char {at}; length {len(fa)} -> {len(fb)})"
    return window(fa, at, n), window(fb, at, n), note


def diff_value(a, b, indent):
    """Describe how two property values differ, element-wise for lists."""
    lines = []
    if isinstance(a, list) and isinstance(b, list):
        fa, fb = [full(x) for x in a], [full(x) for x in b]
        # Multiset difference on the full text, so duplicates and long elements count.
        rest_b = list(fb)
        removed = []
        for x in fa:
            if x in rest_b:
                rest_b.remove(x)
            else:
                removed.append(x)
        added = rest_b
        # Pair up removed/added elements that would print the same when shortened.
        for x in list(removed):
            twin = next((y for y in added if short(y, 200) == short(x, 200)), None)
            if twin is not None:
                removed.remove(x)
                added.remove(twin)
                wa, wb, note = pair(x, twin, 200)
                lines.append(f"{indent}~ element changed{note}:")
                lines.append(f"{indent}  - {wa}")
                lines.append(f"{indent}  + {wb}")
        lines += [f"{indent}- {short(x, 200)}" for x in removed]
        lines += [f"{indent}+ {short(x, 200)}" for x in added]
        if not lines:
            lines.append(f"{indent}(same elements, different order)")
    elif isinstance(a, dict) and isinstance(b, dict):
        oa, ob, ch = diff_map(a, b)
        lines += [f"{indent}- {k}: {short(a[k])}" for k in oa]
        lines += [f"{indent}+ {k}: {short(b[k])}" for k in ob]
        for k in ch:
            wa, wb, note = pair(a[k], b[k], 60)
            lines.append(f"{indent}~ {k}: {wa} -> {wb}{note}")
    else:
        wa, wb, note = pair(a, b, 200)
        lines.append(f"{indent}- {wa}")
        lines.append(f"{indent}+ {wb}{note}")
    return lines


def diff_files(kind, a, b, out, verbose):
    """a/b: {property: {attrs, files{path: hash}}}."""
    oa, ob, ch = diff_map(a, b)
    for k in oa:
        out.append(f"    {kind} property only before: {k} ({len(a[k]['files'])} files)")
    for k in ob:
        out.append(f"    {kind} property only after:  {k} ({len(b[k]['files'])} files)")
    for k in ch:
        pa, pb = a[k], b[k]
        if pa.get("attrs") != pb.get("attrs"):
            out.append(f"    {kind} {k}: attrs {pa.get('attrs')} -> {pb.get('attrs')}")
        fa, fb, fc = diff_map(pa["files"], pb["files"])
        if fa or fb or fc:
            out.append(f"    {kind} {k}: {len(fa)} removed, {len(fb)} added, {len(fc)} content-changed")
            limit = None if verbose else 6
            for p in fa[:limit]:
                out.append(f"      - {p}")
            for p in fb[:limit]:
                out.append(f"      + {p}")
            for p in fc[:limit]:
                out.append(f"      ~ {p}")
            hidden = sum(max(0, len(x) - 6) for x in (fa, fb, fc)) if not verbose else 0
            if hidden:
                out.append(f"      ... {hidden} more (use --verbose)")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--verbose" in sys.argv
    before, after = (json.load(open(p)) for p in args[:2])
    tb, ta = before["tasks"], after["tasks"]

    print(f"Gradle: {before['gradleVersion']} -> {after['gradleVersion']}")
    print(f"Tasks in graph: {len(tb)} -> {len(ta)}")
    only_b, only_a, _ = diff_map(tb, ta)
    print("\n== Task graph ==")
    for p in only_b:
        print(f"  only before: {p} ({tb[p]['type']}, {tb[p]['outcome']})")
    for p in only_a:
        print(f"  only after:  {p} ({ta[p]['type']}, {ta[p]['outcome']})")
    common = sorted(set(tb) & set(ta))
    ob = [p for p in before["executionOrder"] if p in ta]
    oa = [p for p in after["executionOrder"] if p in tb]
    print(f"  execution order of common tasks: {'same' if ob == oa else 'DIFFERENT'}")
    if ob != oa and verbose:
        print("    before:", " ".join(ob))
        print("    after: ", " ".join(oa))

    print("\n== Per-task differences ==")
    identical = []
    for p in common:
        b, a = tb[p], ta[p]
        out = []
        for field in ("type", "outcome"):
            if b[field] != a[field]:
                out.append(f"    {field}: {b[field]} -> {a[field]}")
        if b["dependsOn"] != a["dependsOn"]:
            rem = sorted(set(b["dependsOn"]) - set(a["dependsOn"]))
            add = sorted(set(a["dependsOn"]) - set(b["dependsOn"]))
            out.append(f"    dependsOn: -{rem} +{add}")
        ib, ia = b.get("inputProperties"), a.get("inputProperties")
        if ib is None or ia is None:
            ib, ia = b.get("publicInputProperties", {}), a.get("publicInputProperties", {})
            if "propertyWalkError" in b or "propertyWalkError" in a:
                out.append("    (property walk failed; using public-API aggregates)")
        o1, o2, ch = diff_map(ib, ia)
        for k in o1:
            out.append(f"    input only before: {k} = {short(ib[k])}")
        for k in o2:
            out.append(f"    input only after:  {k} = {short(ia[k])}")
        for k in ch:
            out.append(f"    input {k}:")
            out += diff_value(ib[k], ia[k], "      ")
        if "inputFiles" in b and "inputFiles" in a:
            diff_files("input files", b["inputFiles"], a["inputFiles"], out, verbose)
            diff_files("output files", b["outputFiles"], a["outputFiles"], out, verbose)
        else:
            for kind, key in (("input files", "allInputFiles"), ("output files", "allOutputFiles")):
                diff_files(kind, {"*": {"files": b.get(key, {})}}, {"*": {"files": a.get(key, {})}}, out, verbose)
        eb, ea = b.get("propertyErrors", []), a.get("propertyErrors", [])
        if eb != ea:
            out.append(f"    property query errors: before={eb} after={ea}")
        if out:
            print(f"  {p}")
            print("\n".join(out))
        else:
            identical.append(p)
    print(f"\n== Differing tasks: {len(common) - len(identical)} of {len(common)} ==")
    print(f"\n== Identical tasks ({len(identical)}) ==")
    print("  " + " ".join(identical))


if __name__ == "__main__":
    main()
