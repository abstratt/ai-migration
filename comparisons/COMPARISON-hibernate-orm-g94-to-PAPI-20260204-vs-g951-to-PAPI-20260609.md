# Migration Comparison — hibernate-orm

**Repository migrated:** [hibernate/hibernate-orm](https://github.com/hibernate/hibernate-orm) (migrated via fork [abstratt/hibernate-orm](https://github.com/abstratt/hibernate-orm))

Comparison of the latest completed migration run for each distro pair. Data is taken exclusively from each run's `REPORT-*.md` and `MIGRATION_NOTES.md` on its migration branch.

| | **g94-to-PAPI-20260204** | **g951-to-PAPI-20260609** |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [gradle-10-migration/20260615-2259-g94-to-PAPI-20260204](https://github.com/abstratt/hibernate-orm/tree/gradle-10-migration/20260615-2259-g94-to-PAPI-20260204) | [gradle-10-migration/20260615-2349-g951-to-PAPI-20260609](https://github.com/abstratt/hibernate-orm/tree/gradle-10-migration/20260615-2349-g951-to-PAPI-20260609) |
| **Base branch** | `main` | `main` |
| **Report** | [REPORT-20260615-2259.md](https://github.com/abstratt/hibernate-orm/blob/gradle-10-migration/20260615-2259-g94-to-PAPI-20260204/REPORT-20260615-2259.md) | [REPORT-20260615-2349.md](https://github.com/abstratt/hibernate-orm/blob/gradle-10-migration/20260615-2349-g951-to-PAPI-20260609/REPORT-20260615-2349.md) |
| **Migration notes** | [MIGRATION_NOTES.md](https://github.com/abstratt/hibernate-orm/blob/gradle-10-migration/20260615-2259-g94-to-PAPI-20260204/MIGRATION_NOTES.md) (76 entries) | [MIGRATION_NOTES.md](https://github.com/abstratt/hibernate-orm/blob/gradle-10-migration/20260615-2349-g951-to-PAPI-20260609/MIGRATION_NOTES.md) (73 entries) |
| **Baseline Gradle version** | `9.4.0` (wrapper already at 9.5.1 — upgrade skipped) | `9.5.1` |
| **Files changed** | 8 (7 excluding `MIGRATION_NOTES.md`) | 6 (5 excluding `MIGRATION_NOTES.md`) |
| **Lines changed** | +259 / −49 (308 total) | +229 / −13 (242 total) |
| **Succeeded** | ✅ Yes (`help` + `assemble`) | ✅ Yes (`help` + `assemble`) |


## Adjusted: excluding unnecessary supported-operator rewrites

Gradle supports the Groovy `<<` and `+=` append operators on lazy `ListProperty`/`SetProperty`, and Kotlin's `+=` via the default-imported `plusAssign` extension. Rewriting `prop << x` / `prop += x` to `prop.add(x)` / `prop.addAll(x)` is therefore unnecessary — the operator form keeps compiling and behaving identically. Excluding those rewrites (and the now-incorrect “operator not supported on lazy properties” comments some runs added alongside them):

| | Run 1 | Run 2 |
|---|---|---|
| Unnecessary rewrite lines (excluded) | 18 | 18 |
| Build files that vanish entirely | 1 | 2 |
| **Files changed** (excl. artifacts): reported → adjusted | 7 → **6** | 5 → **3** |
| Source lines (excl. artifacts): reported → adjusted | 82 (+33/−49) → **64** (+24/−40) | 27 (+14/−13) → **9** (+5/−4) |

Rewrite kind: Groovy `<<`/`+=` → `.add(…)`/`.addAll(…)` in `*.gradle`. Baseline is source-only churn (excludes the `MIGRATION_NOTES.md` artifact, whose lines are folded into this comparison's headline “Lines changed” row).

These rewrites are independent of which distribution each run targeted — the operator was supported in both preview distros — so excluding them isolates the genuine target-specific differences between the two runs.
