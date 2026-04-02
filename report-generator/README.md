# Gradle 10 Migration Report Generator

Generates `gradle-10-migration-report.md` by comparing a Gradle 10 preview distribution against Gradle 9.4.0 to find all `@ReplacesEagerProperty`-annotated properties under `org.gradle.api.*`.

## How it works

1. **Download** both distributions
2. **Extract** all `org.gradle.api.*` classes from every JAR (including `lib/plugins/`)
3. **Binary grep** (`grep -rla`) the `.class` files for the string `ReplacesEagerProperty` to identify annotated classes
4. **`javap -v`** on annotated classes to get annotation details (Gradle 10)
5. **`javap -public`** on the same classes in both versions to get clean method signatures for comparison
6. **`generate_report.py`** parses both outputs and produces the markdown report

## Files

| File | Description |
|------|-------------|
| `extract_data.sh` | Downloads Gradle distributions and extracts javap data |
| `generate_report.py` | Python script that parses javap data and produces the report |
| `gradle-10-migration-report.md` | The generated output |
| `g10-javap-v2.txt` | Cached `javap -v` output for annotated classes in Gradle 10 |
| `comparison-v2.txt` | Cached `javap -public` output for both versions side-by-side |
| `annotated-classes-v2.txt` | List of annotated `.class` files |

## Regenerating the report from cached data

If you only need to tweak the report format or examples:

```bash
python3 generate_report.py > gradle-10-migration-report.md
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
python3 generate_report.py > gradle-10-migration-report.md
```
