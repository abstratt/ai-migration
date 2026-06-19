# Comparison: spring-framework — `g94-to-PAPI-20260204` vs `g951-to-PAPI-20260609`

Repository migrated: [abstratt/spring-framework](https://github.com/abstratt/spring-framework)

| | Run 1 | Run 2 |
|---|---|---|
| Branch | [`gradle-10-migration/20260612-1544-g94-to-PAPI-20260204`](https://github.com/abstratt/spring-framework/tree/gradle-10-migration/20260612-1544-g94-to-PAPI-20260204) | [`gradle-10-migration/20260612-1501-g951-to-PAPI-20260609`](https://github.com/abstratt/spring-framework/tree/gradle-10-migration/20260612-1501-g951-to-PAPI-20260609) |
| Report | [REPORT-20260612-1544.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1544-g94-to-PAPI-20260204/REPORT-20260612-1544.md) | [REPORT-20260612-1501.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1501-g951-to-PAPI-20260609/REPORT-20260612-1501.md) |
| Migration notes | [MIGRATION_NOTES.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1544-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [MIGRATION_NOTES.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1501-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| Distro pair | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| Succeeded | Yes (`:spring-aspects` excluded) | Yes (`:spring-aspects` excluded) |
| Files changed | 15 | 9 |
| Lines changed | +252 / −75 | +228 / −64 |
| Files changed (excl. report + notes) | 13 | 7 |
| Lines changed (excl. report + notes) | +30 / −75 | +18 / −64 |

Change counts come from `git diff main...<branch>`. The "excl. report + notes" rows leave out the `MIGRATION_NOTES.md` and `REPORT-*.md` artifacts added by the migration runs themselves, so they reflect only the changes made to the repository's own files.




## Adjusted: excluding unnecessary supported-operator rewrites

Gradle supports the Groovy `<<` and `+=` append operators on lazy `ListProperty`/`SetProperty`, and Kotlin's `+=` via the default-imported `plusAssign` extension. Rewriting `prop << x` / `prop += x` to `prop.add(x)` / `prop.addAll(x)` is therefore unnecessary — the operator form keeps compiling and behaving identically. Excluding those rewrites (and the now-incorrect “operator not supported on lazy properties” comments some runs added alongside them):

| | Run 1 | Run 2 |
|---|---|---|
| Unnecessary rewrite lines (excluded) | 4 | 4 |
| Build files that vanish entirely | 1 | 1 |
| **Files changed** (excl. artifacts): reported → adjusted | 13 → **12** | 7 → **6** |
| Source lines (excl. artifacts): reported → adjusted | 105 (+30/−75) → **101** (+28/−73) | 82 (+18/−64) → **78** (+16/−62) |

Rewrite kind: Groovy `<<`/`+=` → `.add(…)`/`.addAll(…)` in `*.gradle`.

These rewrites are independent of which distribution each run targeted — the operator was supported in both preview distros — so excluding them isolates the genuine target-specific differences between the two runs.
