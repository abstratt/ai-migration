# Task: Build Distro Mapping Bundle

Generate the **distro mapping bundle** for a distro pair — the directory `migration-reference/distro-pairs/<pair-id>/` holding the javap caches, `migration-data.json`, and the human-readable report. This runs the `generator/` pipeline, which downloads both distributions in the pair and runs `javap` over them.

The pair must already exist in `distro-pairs.json` (add one by hand — a new object in the `pairs[]` array with `id`, `label`, `baseline_url`, `target_url`). See `generator/README.md` for the manifest format and details on what each output file is.

## Input

The argument is the **pair id** to build. If no argument is given, **ask the user to pick** from the pairs defined in `distro-pairs.json` (see step 1) — do not silently fall back to the manifest default.

## Prerequisites

- **Java 21+** on `PATH` (for `javap` to read Gradle 10 class files) — check `javap -version`. If older, install/switch via SDKMAN (`sdk use java 21.0.10-tem` or similar).
- **python3**, **curl**, **unzip** available.
- Network access to the pair's `baseline_url` and `target_url`.

## Instructions

1. **Determine the pair id to build.**

   **If a pair id was given as the argument**, confirm it exists in the manifest:
   ```bash
   python3 - "<pair-id>" <<'PY'
   import json, sys
   d = json.load(open("distro-pairs.json"))
   p = next((x for x in d["pairs"] if x["id"] == sys.argv[1]), None)
   if p is None:
       raise SystemExit(f"ERROR: distro pair '{sys.argv[1]}' not found in distro-pairs.json")
   print("PAIR_ID=" + p["id"])
   PY
   ```

   **If no argument was given**, list the defined pairs and **ask the user which one to build** (use the `AskUserQuestion` tool, one option per pair). Show enough to choose — id, label, and whether a bundle already exists — and mark the manifest `default`:
   ```bash
   python3 - <<'PY'
   import json, os
   d = json.load(open("distro-pairs.json"))
   for p in d.get("pairs", []):
       pid = p["id"]
       tag = " (default)" if pid == d.get("default") else ""
       built = "built" if os.path.exists(os.path.join("migration-reference","distro-pairs",pid,"migration-data.json")) else "no bundle yet"
       print(f"{pid}{tag} — {p.get('label','')} [{built}]")
   PY
   ```
   If the chosen pair already shows `built`, warn the user that rebuilding will overwrite the existing bundle, and confirm before proceeding.

   Use the resolved pair id as `<pair-id>` below.

2. **Extract the javap data.** Creates `migration-reference/distro-pairs/<pair-id>/` and writes the four cached `.txt` files into it:
   ```bash
   generator/extract_data.sh <pair-id>
   ```
   This downloads both distributions, extracts public-API classes, and runs `javap`. It can take several minutes. The script prints the exact `generate_report.py` command for the next step when it finishes.

3. **Generate the report and `migration-data.json`** into the same bundle:
   ```bash
   python3 generator/generate_report.py <pair-id> \
     > migration-reference/distro-pairs/<pair-id>/gradle-10-migration-report.md
   ```

4. **Verify** the bundle is complete:
   ```bash
   ls -1 migration-reference/distro-pairs/<pair-id>/
   ```
   Expect: `annotated-classes-v2.txt`, `comparison-v2.txt`, `g10-javap-v2.txt`, `hierarchy-v2.txt`, `migration-data.json`, `gradle-10-migration-report.md`.

## Done when

- `migration-reference/distro-pairs/<pair-id>/` exists and contains all six files above.
- `migration-data.json` is valid JSON (e.g. `python3 -c 'import json;json.load(open("migration-reference/distro-pairs/<pair-id>/migration-data.json"))'` succeeds).
- The user has been told the pair is now ready to migrate with: set it as the manifest `default` (or `export DISTRO_PAIR=<pair-id>`), then run `/g10-migrate <repo-url>`.
