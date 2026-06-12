# Comparison: spring-framework — `g94-to-PAPI-20260204` vs `g951-to-PAPI-20260609`

Repository migrated: [abstratt/spring-framework](https://github.com/abstratt/spring-framework)

| | Run 1 | Run 2 |
|---|---|---|
| Branch | [`gradle-10-migration/20260612-1544-g94-to-PAPI-20260204`](https://github.com/abstratt/spring-framework/tree/gradle-10-migration/20260612-1544-g94-to-PAPI-20260204) | [`gradle-10-migration/20260612-1501-g951-to-PAPI-20260609`](https://github.com/abstratt/spring-framework/tree/gradle-10-migration/20260612-1501-g951-to-PAPI-20260609) |
| Report | [REPORT-20260612-1544.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1544-g94-to-PAPI-20260204/REPORT-20260612-1544.md) | [REPORT-20260612-1501.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1501-g951-to-PAPI-20260609/REPORT-20260612-1501.md) |
| Migration notes | [MIGRATION_NOTES.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1544-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [MIGRATION_NOTES.md](https://github.com/abstratt/spring-framework/blob/gradle-10-migration/20260612-1501-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| Distro pair | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| Succeeded | Yes (`:spring-aspects` excluded) | Yes (`:spring-aspects` excluded) |
| Duration | 15m 16s | 34m 58s |
| Files changed | 15 | 9 |
| Lines changed | +252 / −75 | +228 / −64 |
| Files changed (excl. report + notes) | 13 | 7 |
| Lines changed (excl. report + notes) | +30 / −75 | +18 / −64 |

Change counts come from `git diff main...<branch>`. The "excl. report + notes" rows leave out the `MIGRATION_NOTES.md` and `REPORT-*.md` artifacts added by the migration runs themselves, so they reflect only the changes made to the repository's own files.
