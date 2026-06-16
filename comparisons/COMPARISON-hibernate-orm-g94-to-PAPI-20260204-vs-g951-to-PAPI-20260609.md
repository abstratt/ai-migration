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
