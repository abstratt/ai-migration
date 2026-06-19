# Migration Comparison — kafka

**Repository migrated:** [apache/kafka](https://github.com/apache/kafka) (migrated via fork [abstratt/kafka](https://github.com/abstratt/kafka))

Comparison of the latest completed migration run for each distro pair. Data is taken exclusively from each run's `REPORT-*.md` and `MIGRATION_NOTES.md` on its migration branch.

| | **g94-to-PAPI-20260204** | **g951-to-PAPI-20260609** |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [gradle-10-migration/20260615-2138-g94-to-PAPI-20260204](https://github.com/abstratt/kafka/tree/gradle-10-migration/20260615-2138-g94-to-PAPI-20260204) | [gradle-10-migration/20260615-2121-g951-to-PAPI-20260609](https://github.com/abstratt/kafka/tree/gradle-10-migration/20260615-2121-g951-to-PAPI-20260609) |
| **Base branch** | `trunk` | `trunk` |
| **Report** | [REPORT-20260615-2138.md](https://github.com/abstratt/kafka/blob/gradle-10-migration/20260615-2138-g94-to-PAPI-20260204/REPORT-20260615-2138.md) | [REPORT-20260615-2121.md](https://github.com/abstratt/kafka/blob/gradle-10-migration/20260615-2121-g951-to-PAPI-20260609/REPORT-20260615-2121.md) |
| **Migration notes** | [MIGRATION_NOTES.md](https://github.com/abstratt/kafka/blob/gradle-10-migration/20260615-2138-g94-to-PAPI-20260204/MIGRATION_NOTES.md) (3 entries) | [MIGRATION_NOTES.md](https://github.com/abstratt/kafka/blob/gradle-10-migration/20260615-2121-g951-to-PAPI-20260609/MIGRATION_NOTES.md) (3 entries) |
| **Baseline Gradle version** | `9.4.0` (repo already on 9.4.1 — upgrade skipped) | `9.5.1` |
| **Files changed** | 3 | 3 |
| **Lines changed** | +34 / −19 (53 total) | +42 / −26 (68 total) |
| **Succeeded** | ✅ Yes (`help` + `assemble`) | ✅ Yes (`help` + `assemble`) |


## Adjusted: excluding unnecessary supported-operator rewrites

Gradle supports the Groovy `<<` and `+=` append operators on lazy `ListProperty`/`SetProperty`, and Kotlin's `+=` via the default-imported `plusAssign` extension. Rewriting `prop << x` / `prop += x` to `prop.add(x)` / `prop.addAll(x)` is therefore unnecessary — the operator form keeps compiling and behaving identically. Excluding those rewrites (and the now-incorrect “operator not supported on lazy properties” comments some runs added alongside them):

| | Run 1 | Run 2 |
|---|---|---|
| Unnecessary rewrite lines (excluded) | 30 | 31 |
| Build files that vanish entirely | 0 | 0 |
| **Files changed** (excl. artifacts): reported → adjusted | 2 → **2** | 2 → **2** |
| Source lines (excl. artifacts): reported → adjusted | 39 (+20/−19) → **9** (+5/−4) | 52 (+26/−26) → **21** (+10/−11) |

Rewrite kind: Groovy `<<`/`+=` → `.add(…)`/`.addAll(…)` in `*.gradle`. Baseline is source-only churn excluding the `MIGRATION_NOTES.md`/`REPORT` artifacts (this comparison's headline counts include them).

These rewrites are independent of which distribution each run targeted — the operator was supported in both preview distros — so excluding them isolates the genuine target-specific differences between the two runs.
