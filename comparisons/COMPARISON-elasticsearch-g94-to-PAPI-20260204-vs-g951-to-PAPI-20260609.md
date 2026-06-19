# Migration Comparison: elasticsearch

**Repository:** [elastic/elasticsearch](https://github.com/elastic/elasticsearch) (migrated via fork [abstratt/elasticsearch](https://github.com/abstratt/elasticsearch))

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260619-1036-g94-to-PAPI-20260204`](https://github.com/abstratt/elasticsearch/tree/gradle-10-migration/20260619-1036-g94-to-PAPI-20260204) | [`gradle-10-migration/20260619-1200-g951-to-PAPI-20260609`](https://github.com/abstratt/elasticsearch/tree/gradle-10-migration/20260619-1200-g951-to-PAPI-20260609) |
| **Base branch** | `main` | `main` |
| **Report** | [`REPORT-20260619-1036.md`](https://github.com/abstratt/elasticsearch/blob/gradle-10-migration/20260619-1036-g94-to-PAPI-20260204/REPORT-20260619-1036.md) | [`REPORT-20260619-1200.md`](https://github.com/abstratt/elasticsearch/blob/gradle-10-migration/20260619-1200-g951-to-PAPI-20260609/REPORT-20260619-1200.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/elasticsearch/blob/gradle-10-migration/20260619-1036-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/elasticsearch/blob/gradle-10-migration/20260619-1200-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 51 | 20 |
| **Total lines changed** (excl. artifacts) | +172 / −139 (311 total) | +51 / −31 (82 total) |
| − Formatting / whitespace | 16 | 0 |
| − Warnings-as-errors & deprecations | 3 (2 files) | 2 (2 files) |
| − Other infra relaxations | 5 (1 file) | 4 (1 file) |
| **= Core migration changes** | **287** | **76** |
| **Migration notes file** | 278-line file | 910-line file |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed (Docker image tasks excluded — no Docker daemon) | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed (Docker distribution projects excluded — no Docker daemon) |

## Notes

- Both runs were based on the same `main` commit (`7881a667`), both completed successfully, and both excluded the `:distribution:docker:…` image tasks for the same reason (no Docker daemon in the environment) — an environment limitation, not a migration gap.
- **Core migration churn differs substantially** — 287 lines over 51 files (g94) vs 76 lines over 20 files (g951). The `g94` run rewrote considerably more build logic under `build-tools-internal/`, `build-tools/`, and `build-conventions/`, whereas the `g951` run's source/build changes were smaller and more localized. The two runs target different baseline/target distributions (`9.4.0`→`PAPI-20260204` preview vs `9.5.1`→`PAPI-20260609` snapshot), which accounts for the differing transformation sets each had to apply.
- **Task 03 differed:** `g94` skipped the baseline upgrade (the wrapper was already on `9.5.0`, ≥ baseline), while `g951` ran the `Upgrade Baseline Gradle` step to `9.5.1`, which also updated the `build-conventions`/`build-tools` wrapper properties and the `minimumGradleVersion`.
- **Both runs made the same non-core relaxations:** `gradle.properties` deprecation warning-mode relaxed from `fail` → `none` (warnings bucket, with `ElasticsearchJavaModulePathPlugin.java`), and a blanket `trust file=".*[.]jar"` in `gradle/verification-metadata.xml` for the preview distribution's bundled artifacts (infra bucket). The `g94` run additionally carried 16 formatting-only lines; `g951` had none.
- **The `MIGRATION_NOTES.md` file is larger for `g951` (910 lines) than `g94` (278 lines)**, despite `g951` having far fewer code changes — i.e. the relative weight of deferred-site / scanner-hit documentation versus applied changes is inverted between the two runs.

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs. Preview-only relaxations not matching these patterns land in `core`.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn).


## Adjusted: excluding unnecessary supported-operator rewrites

Gradle supports the Groovy `<<` and `+=` append operators on lazy `ListProperty`/`SetProperty`, and Kotlin's `+=` via the default-imported `plusAssign` extension. Rewriting `prop << x` / `prop += x` to `prop.add(x)` / `prop.addAll(x)` is therefore unnecessary — the operator form keeps compiling and behaving identically. Excluding those rewrites (and the now-incorrect “operator not supported on lazy properties” comments some runs added alongside them):

| | Run 1 | Run 2 |
|---|---|---|
| Unnecessary rewrite lines (excluded) | 22 | 22 |
| Build files that vanish entirely | 7 | 7 |
| **Files changed** (excl. artifacts): reported → adjusted | 51 → **44** | 20 → **13** |
| **Core migration changes**: reported → adjusted | 287 → **265** | 76 → **54** |

Rewrite kind: Groovy `<<`/`+=` → `.add(…)`/`.addAll(…)` in `*.gradle`.

These rewrites are independent of which distribution each run targeted — the operator was supported in both preview distros — so excluding them isolates the genuine target-specific differences between the two runs.
