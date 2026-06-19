# Comparison: junit-framework — `g94-to-PAPI-20260204` vs `g951-to-PAPI-20260609`

Repository migrated: [abstratt/junit-framework](https://github.com/abstratt/junit-framework)

| | Run 1 | Run 2 |
|---|---|---|
| Branch | [`gradle-10-migration/20260612-1607-g94-to-PAPI-20260204`](https://github.com/abstratt/junit-framework/tree/gradle-10-migration/20260612-1607-g94-to-PAPI-20260204) | [`gradle-10-migration/20260612-1536-g951-to-PAPI-20260609`](https://github.com/abstratt/junit-framework/tree/gradle-10-migration/20260612-1536-g951-to-PAPI-20260609) |
| Report | [REPORT-20260612-1607.md](https://github.com/abstratt/junit-framework/blob/gradle-10-migration/20260612-1607-g94-to-PAPI-20260204/REPORT-20260612-1607.md) | [REPORT-20260612-1536.md](https://github.com/abstratt/junit-framework/blob/gradle-10-migration/20260612-1536-g951-to-PAPI-20260609/REPORT-20260612-1536.md) |
| Migration notes | [MIGRATION_NOTES.md](https://github.com/abstratt/junit-framework/blob/gradle-10-migration/20260612-1607-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | none (all deferrals applied; file deleted) |
| Distro pair | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| Succeeded | Yes | Yes |
| Files changed | 15 | 11 |
| Lines changed | +161 / −53 | +104 / −42 |
| Files changed (excl. report + notes) | 13 | 10 |
| Lines changed (excl. report + notes) | +64 / −53 | +45 / −42 |

Change counts come from `git diff main...<branch>`. The "excl. report + notes" rows leave out the `MIGRATION_NOTES.md` and `REPORT-*.md` artifacts added by the migration runs themselves, so they reflect only the changes made to the repository's own files. The branches are local only (the workflow does not push), so the links above resolve once the branches are pushed to the fork.



## Adjusted: excluding unnecessary supported-operator rewrites

Gradle supports the Groovy `<<` and `+=` append operators on lazy `ListProperty`/`SetProperty`, and Kotlin's `+=` via the default-imported `plusAssign` extension. Rewriting `prop << x` / `prop += x` to `prop.add(x)` / `prop.addAll(x)` is therefore unnecessary — the operator form keeps compiling and behaving identically. Excluding those rewrites (and the now-incorrect “operator not supported on lazy properties” comments some runs added alongside them):

| | Run 1 | Run 2 |
|---|---|---|
| Unnecessary rewrite lines (excluded) | 46 | 46 |
| Build files that vanish entirely | 2 | 3 |
| **Files changed** (excl. artifacts): reported → adjusted | 13 → **11** | 10 → **7** |
| Source lines (excl. artifacts): reported → adjusted | 117 (+64/−53) → **71** (+41/−30) | 87 (+45/−42) → **41** (+22/−19) |

Rewrite kind: Kotlin `+=` → `.add(…)`/`.addAll(…)` in `*.gradle.kts`.

These rewrites are independent of which distribution each run targeted — the operator was supported in both preview distros — so excluding them isolates the genuine target-specific differences between the two runs.
