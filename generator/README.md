# Gradle 10 Migration Report Generator

Generates a `gradle-10-migration-report.md` by comparing a Gradle 10 preview ("target") distribution against a baseline Gradle release to find all `@ReplacesEagerProperty`-annotated properties across all [public API packages](https://docs.gradle.org/current/userguide/public_apis.html).

## Distro pairs

A migration is defined by a **pair** of distributions — a *baseline* (e.g. Gradle 9.4.0) and a *target* (a Gradle 10 preview). Pairs are declared in [`../distro-pairs.json`](../distro-pairs.json):

```json
{
  "default": "g94-to-PAPI-20260204",
  "pairs": [
    {
      "id": "g94-to-PAPI-20260204",
      "label": "Gradle 9.4.0 → asodja provider-api preview (2026-02-04)",
      "baseline_url": "https://downloads.gradle.org/distributions/gradle-9.4.0-bin.zip",
      "target_url": "https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip",
      "notes": "Free-text description of the pair."
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `default` | The pair `id` used when no pair is named on the command line. |
| `pairs[].id` | Unique identifier. **Becomes the distro mapping bundle directory name** (`migration-reference/distro-pairs/<id>/`) and the suffix of the migration branch name (`gradle-10-migration/<timestamp>-<id>`), so keep it filesystem-safe and git-ref-safe. |
| `pairs[].label` | Human-readable name; appears in the generated report header. |
| `pairs[].baseline_url` | Download URL for the baseline distribution. |
| `pairs[].target_url` | Download URL for the target (Gradle 10 preview) distribution. |
| `pairs[].notes` | Free-text notes. Not consumed by tooling. |

Every script takes an optional pair `id`; with no argument they fall back to the manifest's `default`.

## Prerequisites

- **Java 21+** — required for `javap` to read Gradle 10 class files. Use [SDKMAN](https://sdkman.io/) to install/switch: `sdk use java 21.0.10-tem`
- **Python 3** — for `generate_report.py` (also used to parse the manifest in `extract_data.sh`, so there is no `jq` dependency)
- **curl**, **unzip** — for downloading and extracting distributions

## How it works

1. **Resolve** the baseline/target URLs and output directory from the selected pair in `../distro-pairs.json`
2. **Download** both distributions
3. **Extract** classes from all public API packages out of every JAR (including `lib/plugins/`)
4. **Binary grep** (`grep -rla`) the `.class` files for the string `ReplacesEagerProperty` to identify annotated classes
5. **`javap -v`** on annotated classes to get annotation details (target)
6. **`javap -public`** on the same classes in both versions to get clean method signatures for comparison
7. **`generate_report.py`** parses both outputs and produces the markdown report

## Creating a new distro pair

1. **Add an entry** to the `pairs[]` array in [`../distro-pairs.json`](../distro-pairs.json) with a unique `id`, the `baseline_url`, and the `target_url`.

2. **Extract the javap data** — pass the pair id:

   ```bash
   ./extract_data.sh <pair-id>
   ```

   This resolves the URLs from the manifest and writes the cached artifacts into `../migration-reference/distro-pairs/<pair-id>/` (the directory is created if needed).

3. **Generate the report** — `extract_data.sh` prints the exact command at the end; it is:

   ```bash
   python3 generate_report.py <pair-id> \
     > ../migration-reference/distro-pairs/<pair-id>/gradle-10-migration-report.md
   ```

4. **Use it in a migration** — either set `"default"` in the manifest to the new id, or select it explicitly when applying migrations:

   ```bash
   python3 ../migration-reference/apply_migrations.py <project-dir> --distro-pair <pair-id>
   ```

## Regenerating the report from cached data

If you only need to tweak the report format or examples (the `distro-pairs/<id>/` distro mapping bundle already exists):

```bash
# default pair
python3 generate_report.py > ../migration-reference/distro-pairs/<default-pair-id>/gradle-10-migration-report.md

# a specific pair
python3 generate_report.py <pair-id> > ../migration-reference/distro-pairs/<pair-id>/gradle-10-migration-report.md
```

## Files

This directory (`generator/`) holds only pipeline source — the hand-written scripts and docs.

| File | Description |
|------|-------------|
| `extract_data.sh` | Resolves a pair from `../distro-pairs.json`, downloads the distributions, and extracts javap data into `../migration-reference/distro-pairs/<pair-id>/` |
| `generate_report.py` | Parses the javap data for a pair and produces the report + JSON in `../migration-reference/distro-pairs/<pair-id>/` |

The manifest lives one level up at `../distro-pairs.json`.

### Per-pair generated artifacts (the distro mapping bundle)

Each pair gets its own **distro mapping bundle** — a directory at `../migration-reference/distro-pairs/<pair-id>/` holding all the generated outputs for that pair:

| File | Description |
|------|-------------|
| `gradle-10-migration-report.md` | Generated human-readable report |
| `migration-data.json` | Generated structured lookup table (consumed by migration runs) |
| `g10-javap-v2.txt` | Cached `javap -v` output for annotated classes in the target distribution |
| `comparison-v2.txt` | Cached `javap -public` output for both versions side-by-side |
| `annotated-classes-v2.txt` | Cached list of annotated `.class` files |
| `hierarchy-v2.txt` | Cached class declarations for all public API classes |

### Shared consumer-side files

These hand-written files live at the `../migration-reference/` top level and apply across all pairs:

| File | Description |
|------|-------------|
| `MIGRATION_RULES.md` | Hand-written transformation rules (consumed by migration runs) |
| `apply_migrations.py` | Applies mechanical rewrites to a target project; selects a pair's data via `--distro-pair` |
| `scan_usages.py` | Hand-written scanner invoked by task 06 |
