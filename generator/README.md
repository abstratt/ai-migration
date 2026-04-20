# Gradle 10 Migration Report Generator

Generates `gradle-10-migration-report.md` by comparing a Gradle 10 preview distribution against Gradle 9.4.0 to find all `@ReplacesEagerProperty`-annotated properties across all [public API packages](https://docs.gradle.org/current/userguide/public_apis.html).

## Prerequisites

- **Java 21+** — required for `javap` to read Gradle 10 class files. Use [SDKMAN](https://sdkman.io/) to install/switch: `sdk use java 21.0.10-tem`
- **Python 3** — for `generate_report.py`
- **curl**, **unzip** — for downloading and extracting distributions

## How it works

1. **Download** both distributions
2. **Extract** classes from all public API packages out of every JAR (including `lib/plugins/`)
3. **Binary grep** (`grep -rla`) the `.class` files for the string `ReplacesEagerProperty` to identify annotated classes
4. **`javap -v`** on annotated classes to get annotation details (Gradle 10)
5. **`javap -public`** on the same classes in both versions to get clean method signatures for comparison
6. **`generate_report.py`** parses both outputs and produces the markdown report

## Files

This directory (`generator/`) holds only pipeline source — the hand-written scripts and docs.

| File | Description |
|------|-------------|
| `extract_data.sh` | Downloads Gradle distributions and extracts javap data into `../migration-reference/` |
| `generate_report.py` | Parses the javap data in `../migration-reference/` and produces the report + JSON there |

All generated outputs and consumer-side artifacts live in the sibling `../migration-reference/` directory:

| File | Description |
|------|-------------|
| `gradle-10-migration-report.md` | Generated human-readable report |
| `migration-data.json` | Generated structured lookup table (consumed by migration runs) |
| `MIGRATION_RULES.md` | Hand-written transformation rules (consumed by migration runs) |
| `scan_usages.py` | Hand-written scanner invoked by task 06 |
| `g10-javap-v2.txt` | Cached `javap -v` output for annotated classes in Gradle 10 |
| `comparison-v2.txt` | Cached `javap -public` output for both versions side-by-side |
| `annotated-classes-v2.txt` | Cached list of annotated `.class` files |
| `hierarchy-v2.txt` | Cached class declarations for all public API classes |

## Regenerating the report from cached data

If you only need to tweak the report format or examples:

```bash
python3 generate_report.py > ../migration-reference/gradle-10-migration-report.md
```

## Regenerating from scratch (new Gradle versions)

```bash
# With defaults (current URLs baked into the script)
./extract_data.sh

# With a different Gradle 10 preview
./extract_data.sh "https://github.com/asodja/gradle-dev-distributions/releases/download/v2.0.0/gradle-new-preview.zip"

# With both overridden
./extract_data.sh "https://new-g10-url.zip" "https://downloads.gradle.org/distributions/gradle-9.5.0-bin.zip"

# Then regenerate the report
python3 generate_report.py > ../migration-reference/gradle-10-migration-report.md
```
