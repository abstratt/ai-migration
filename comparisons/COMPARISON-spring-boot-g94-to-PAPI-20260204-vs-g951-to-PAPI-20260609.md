# Comparison: spring-boot — `g94-to-PAPI-20260204` vs `g951-to-PAPI-20260609`

Repository migrated: [abstratt/spring-boot](https://github.com/abstratt/spring-boot)

| | Run 1 | Run 2 |
|---|---|---|
| Branch | [`gradle-10-migration/20260611-1620-g94-to-PAPI-20260204`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260611-1620-g94-to-PAPI-20260204) | [`gradle-10-migration/20260611-1536-g951-to-PAPI-20260609`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260611-1536-g951-to-PAPI-20260609) |
| Report | [REPORT-20260611-1620.md](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260611-1620-g94-to-PAPI-20260204/REPORT-20260611-1620.md) | [REPORT-20260611-1536.md](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260611-1536-g951-to-PAPI-20260609/REPORT-20260611-1536.md) |
| Migration notes | [MIGRATION_NOTES.md](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260611-1620-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [MIGRATION_NOTES.md](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260611-1536-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| Distro pair | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| Succeeded | Yes | Yes |
| Files changed | 39 | 24 |
| Lines changed | +1428 / −61 | +1273 / −34 |
| Files changed (excl. report + notes) | 37 | 22 |
| Lines changed (excl. report + notes) | +76 / −61 | +57 / −34 |

Change counts come from the GitHub compare API (`main...<branch>`). The "excl. report + notes" rows leave out the `MIGRATION_NOTES.md` and `REPORT-*.md` artifacts added by the migration runs themselves, so they reflect only the changes made to the repository's own files.



## Adjusted: excluding unnecessary supported-operator rewrites

Gradle supports the Groovy `<<` and `+=` append operators on lazy `ListProperty`/`SetProperty`, and Kotlin's `+=` via the default-imported `plusAssign` extension. Rewriting `prop << x` / `prop += x` to `prop.add(x)` / `prop.addAll(x)` is therefore unnecessary — the operator form keeps compiling and behaving identically. Excluding those rewrites (and the now-incorrect “operator not supported on lazy properties” comments some runs added alongside them):

| | Run 1 | Run 2 |
|---|---|---|
| Unnecessary rewrite lines (excluded) | 24 | 24 |
| Build files that vanish entirely | 11 | 11 |
| **Files changed** (excl. artifacts): reported → adjusted | 37 → **26** | 22 → **11** |
| Source lines (excl. artifacts): reported → adjusted | 137 (+76/−61) → **113** (+64/−49) | 91 (+57/−34) → **67** (+45/−22) |

Rewrite kind: Groovy `<<`/`+=` → `.add(…)`/`.addAll(…)` in `*.gradle`.

These rewrites are independent of which distribution each run targeted — the operator was supported in both preview distros — so excluding them isolates the genuine target-specific differences between the two runs.
