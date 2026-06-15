# Migration Comparison: groovy

**Repository:** [apache/groovy](https://github.com/apache/groovy) (migrated via fork [abstratt/groovy](https://github.com/abstratt/groovy))

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. All figures are taken from each run's `REPORT-*.md` and `MIGRATION_NOTES.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260615-1812-g94-to-PAPI-20260204`](https://github.com/abstratt/groovy/tree/gradle-10-migration/20260615-1812-g94-to-PAPI-20260204) | [`gradle-10-migration/20260615-1919-g951-to-PAPI-20260609`](https://github.com/abstratt/groovy/tree/gradle-10-migration/20260615-1919-g951-to-PAPI-20260609) |
| **Report** | [`REPORT-20260615-1812.md`](https://github.com/abstratt/groovy/blob/gradle-10-migration/20260615-1812-g94-to-PAPI-20260204/REPORT-20260615-1812.md) | [`REPORT-20260615-1919.md`](https://github.com/abstratt/groovy/blob/gradle-10-migration/20260615-1919-g951-to-PAPI-20260609/REPORT-20260615-1919.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/groovy/blob/gradle-10-migration/20260615-1812-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/groovy/blob/gradle-10-migration/20260615-1919-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** | 12 incl. artifacts (11 excl. `MIGRATION_NOTES.md`) | 9 incl. artifacts (8 excl. `MIGRATION_NOTES.md`) |
| **Lines changed** | +89 / −23 incl. artifacts (+50 / −23 excl. `MIGRATION_NOTES.md`) | +56 / −14 incl. artifacts (+15 / −14 excl. `MIGRATION_NOTES.md`) |
| **Migration notes entries** | 11 (all false positives) | 11 (all false positives) |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed |

## Notes

- Both runs reported the repository was already on Gradle 9.5.1, so the baseline-upgrade task made no change in either case (the `g94` baseline of 9.4.0 is below the repo's existing version, and `g951` matches it exactly).
- The `g94` run touches more files and lines (12 files, +89/−23) than the `g951` run (9 files, +56/−14). The `g94` run additionally disabled the Develocity/build-scans plugins in `settings.gradle` (a `NoSuchMethodError` against the older preview distribution) — a change not needed by the `g951` run against the newer distribution.
- Both runs handled the same core classes of construct (`list`-kind operator mutations, a `DirectoryProperty`/`dir` read, a `ConfigurableFileCollection` append, and the multi-value Javadoc `tag` option), and both ended with 11 false-positive entries in `MIGRATION_NOTES.md` (10 third-party Apache RAT `excludes` + 1 local Groovy list variable).
