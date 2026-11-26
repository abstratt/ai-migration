#!/usr/bin/env python3
"""Group the differences between two task-dump JSON files by kind, to help assign reason mnemonics.

Usage: classify_diffs.py before.json after.json [control.json]

Prints, per kind of difference, the number of tasks and up to three task paths:
  outcome / deps / input value / input or output files (with the changed file names) / property errors.
Also prints how many input values the after build read through an eager-getter adapter.
With a control dump (a second run of the baseline build), also prints which output files, input
values and outcomes differ baseline-vs-control and control-vs-after, to separate run-to-run
variance from differences caused by the Gradle distribution.
"""
import collections
import json
import sys


def load(p):
    return json.load(open(p))


def classify(bt, at):
    kinds = collections.defaultdict(list)
    for t in bt:
        x, y = bt[t], at.get(t)
        if y is None:
            kinds[("only-before", x["type"])].append(t)
            continue
        ty = x["type"].split(".")[-1]
        if x["outcome"] != y["outcome"]:
            kinds[("outcome", ty, x["outcome"] + " -> " + y["outcome"])].append(t)
        if x.get("dependsOn") != y.get("dependsOn"):
            kinds[("dependsOn", ty)].append(t)
        ib, ia = x.get("inputProperties", {}), y.get("inputProperties", {})
        for k in set(ib) | set(ia):
            if ib.get(k, "<absent>") != ia.get(k, "<absent>"):
                kinds[("input", ty, k, json.dumps(ib.get(k, "<absent>"))[:90] + " -> " + json.dumps(ia.get(k, "<absent>"))[:90])].append(t)
        for kind in ("inputFiles", "outputFiles"):
            fb, fa = x.get(kind, {}), y.get(kind, {})
            for k in set(fb) | set(fa):
                if fb.get(k) == fa.get(k):
                    continue
                if not (k in fb and k in fa):
                    kinds[(kind + "-only-" + ("before" if k in fb else "after"), ty, k)].append(t)
                    continue
                pb, pa = fb[k].get("files", {}), fa[k].get("files", {})
                ch = sorted(p for p in set(pb) | set(pa) if pb.get(p) != pa.get(p))
                names = sorted(set(p.rsplit("/", 1)[-1] for p in ch))
                kinds[(kind, ty, k, ", ".join(names[:6]) + (" …%d" % len(names) if len(names) > 6 else ""))].append(t)
        if sorted(x.get("propertyErrors") or []) != sorted(y.get("propertyErrors") or []):
            kinds[("propertyErrors", ty)].append(t)
    for t in at:
        if t not in bt:
            kinds[("only-after", at[t]["type"])].append(t)
    return kinds


def changed_outputs(x, y):
    r = set()
    for t in x:
        if t not in y:
            continue
        fb, fa = x[t].get("outputFiles", {}), y[t].get("outputFiles", {})
        for k in set(fb) | set(fa):
            pb = (fb.get(k) or {}).get("files", {})
            pa = (fa.get(k) or {}).get("files", {})
            r |= {p for p in set(pb) | set(pa) if pb.get(p) != pa.get(p)}
    return r


def file_summary(paths):
    c = collections.Counter()
    for p in paths:
        n = p.rsplit("/", 1)[-1]
        c["*.class" if n.endswith(".class") else n] += 1
    return dict(c.most_common())


def changed_inputs(x, y):
    return sorted({(t, k) for t in x if t in y
                   for k in set(x[t].get("inputProperties", {})) | set(y[t].get("inputProperties", {}))
                   if x[t].get("inputProperties", {}).get(k, "<a>") != y[t].get("inputProperties", {}).get(k, "<a>")})


def main():
    B, A = load(sys.argv[1]), load(sys.argv[2])
    bt, at = B["tasks"], A["tasks"]
    print("tasks before/after:", len(bt), len(at), "| execution order same:", B.get("executionOrder") == A.get("executionOrder"))
    print("outcomes before:", dict(collections.Counter(r["outcome"] for r in bt.values())))
    print("outcomes after: ", dict(collections.Counter(r["outcome"] for r in at.values())))
    via = [(t, r["inputPropertiesViaAdapter"]) for t, r in at.items() if r.get("inputPropertiesViaAdapter")]
    print("read via adapter (after):", sum(len(v) for _, v in via), "values in", len(via), "tasks")
    kinds = classify(bt, at)
    differing = {t for v in kinds.values() for t in v}
    common = set(bt) & set(at)
    print("differing tasks:", len(differing & common), "of", len(common),
          "| added:", len(set(at) - set(bt)), "| removed:", len(set(bt) - set(at)))
    print()
    for k, v in sorted(kinds.items(), key=lambda kv: str(kv[0])):
        print(len(v), k, v[:3])
    # Which differing inputs were read through an adapter on the after side
    adapter_diffs = sorted({(t, k[2]) for k, v in kinds.items() if k[0] == "input" for t in v
                            if k[2] in (at.get(t, {}).get("inputPropertiesViaAdapter") or [])})
    if adapter_diffs:
        print("\ndiffering inputs that WERE read through an adapter (real eager-API differences):")
        for t, p in adapter_diffs:
            print("  ", t, p)
    if len(sys.argv) > 3:
        C = load(sys.argv[3])["tasks"]
        print("\n== control (second baseline run)")
        print("outputs  before vs after:  ", file_summary(changed_outputs(bt, at)))
        print("outputs  before vs control:", file_summary(changed_outputs(bt, C)))
        print("outputs  control vs after: ", file_summary(changed_outputs(C, at)))
        print("inputs   before vs control:", changed_inputs(bt, C)[:10])
        print("inputs   control vs after: ", changed_inputs(C, at)[:10])
        print("outcomes before vs control:", [(t, bt[t]["outcome"], C[t]["outcome"]) for t in C if t in bt and C[t]["outcome"] != bt[t]["outcome"]][:10])
        print("outcomes control vs after: ", [(t, C[t]["outcome"], at[t]["outcome"]) for t in C if t in at and C[t]["outcome"] != at[t]["outcome"]][:10])


if __name__ == "__main__":
    main()
