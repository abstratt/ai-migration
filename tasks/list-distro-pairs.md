# Task: List Distro Pairs

List the distro pairs declared in `distro-pairs.json` at the repo root, showing each pair's `id`, `label`, `baseline_url`, and `target_url`. Mark which pair is the manifest `default`, and whether its distro mapping bundle has been built yet.

## Instructions

Run this from the repo root and show the user the output verbatim:

```bash
python3 - <<'PY'
import json, os
d = json.load(open("distro-pairs.json"))
default = d.get("default")
pairs = d.get("pairs", [])
print(f"{len(pairs)} distro pair(s) in distro-pairs.json (default: {default})\n")
for p in pairs:
    pid = p.get("id", "?")
    is_default = " (default)" if pid == default else ""
    bundle = os.path.join("migration-reference", "distro-pairs", pid, "migration-data.json")
    built = "built" if os.path.exists(bundle) else "no bundle yet"
    print(f"- {pid}{is_default}  [{built}]")
    print(f"    label:    {p.get('label', '')}")
    print(f"    baseline: {p.get('baseline_url', '')}")
    print(f"    target:   {p.get('target_url', '')}")
PY
```

If a pair shows `no bundle yet`, note that it must be built with `/g10-build-bundle <id>` before it can be migrated against.

## Done when

- Every pair in `distro-pairs.json` has been listed with its `id`, `label`, `baseline_url`, and `target_url`.
- The `default` pair is marked, and each pair's bundle status (built / not built) is shown.
