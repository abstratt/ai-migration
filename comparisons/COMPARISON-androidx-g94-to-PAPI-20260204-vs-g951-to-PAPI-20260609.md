# Comparison: androidx — `g94-to-PAPI-20260204` vs `g951-to-PAPI-20260609`

Repository migrated: [abstratt/androidx](https://github.com/abstratt/androidx)

| | Run 1 | Run 2 |
|---|---|---|
| Pull request | [#2](https://github.com/abstratt/androidx/pull/2) | [#3](https://github.com/abstratt/androidx/pull/3) |
| Branch | [`gradle-10-migration/20260615-1426-g94-to-PAPI-20260204`](https://github.com/abstratt/androidx/tree/gradle-10-migration/20260615-1426-g94-to-PAPI-20260204) | [`gradle-10-migration/20260615-1527-g951-to-PAPI-20260609`](https://github.com/abstratt/androidx/tree/gradle-10-migration/20260615-1527-g951-to-PAPI-20260609) |
| Base branch | `androidx-main` | `androidx-main` |
| Report | [REPORT-20260615-1426.md](https://github.com/abstratt/androidx/blob/gradle-10-migration/20260615-1426-g94-to-PAPI-20260204/REPORT-20260615-1426.md) | [REPORT-20260615-1527.md](https://github.com/abstratt/androidx/blob/gradle-10-migration/20260615-1527-g951-to-PAPI-20260609/REPORT-20260615-1527.md) |
| Migration notes | [MIGRATION_NOTES.md](https://github.com/abstratt/androidx/blob/gradle-10-migration/20260615-1426-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [MIGRATION_NOTES.md](https://github.com/abstratt/androidx/blob/gradle-10-migration/20260615-1527-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| Distro pair | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| Succeeded | Yes | Yes |
| Files changed | 32 | 35 |
| Lines changed | +334 / −84 | +347 / −77 |
| Files changed (excl. report + notes) | 30 | 33 |
| Lines changed (excl. report + notes) | +95 / −84 | +98 / −77 |

Change counts are GitHub's authoritative per-file figures for each pull request (`repos/abstratt/androidx/pulls/<n>/files`). The "excl. report + notes" rows leave out the `MIGRATION_NOTES.md` and `REPORT-*.md` artifacts added by the migration runs themselves, so they reflect only the changes made to the repository's own files. Both reports record status "Migrated" (build-logic migrated and verified by `./gradlew help`; `./gradlew assemble` blocked by environment, unrelated to the Provider API migration).
