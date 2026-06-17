# Migration Comparison: kotlin

**Repository:** [JetBrains/kotlin](https://github.com/JetBrains/kotlin) (migrated via fork [abstratt/kotlin](https://github.com/abstratt/kotlin))

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. All figures are taken from each run's `REPORT-*.md` and `MIGRATION_NOTES.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260616-1745-g94-to-PAPI-20260204`](https://github.com/abstratt/kotlin/tree/gradle-10-migration/20260616-1745-g94-to-PAPI-20260204) | [`gradle-10-migration/20260616-1916-g951-to-PAPI-20260609`](https://github.com/abstratt/kotlin/tree/gradle-10-migration/20260616-1916-g951-to-PAPI-20260609) |
| **Report** | [`REPORT-20260616-1745.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260616-1745-g94-to-PAPI-20260204/REPORT-20260616-1745.md) | [`REPORT-20260616-1916.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260616-1916-g951-to-PAPI-20260609/REPORT-20260616-1916.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260616-1745-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260616-1916-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** | 75 incl. artifacts (74 excl. `MIGRATION_NOTES.md`) | 69 incl. artifacts (68 excl. `MIGRATION_NOTES.md`) |
| **Lines changed** | +417 / −154 incl. artifacts (+163 / −154 excl. `MIGRATION_NOTES.md`) | +470 / −131 incl. artifacts (+157 / −131 excl. `MIGRATION_NOTES.md`) |
| **Migration notes entries** | 147 bullet entries under 9 root-cause headings (148 files flagged, all documented) | 180 bullet entries under 17 root-cause headings (145 files flagged, all documented) |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed |

## Notes

- Both runs reported the repository's wrapper was already at Gradle `9.5.1`, so the baseline-upgrade task (03) made no change in either case (the `g94` baseline of 9.4.0 is below the existing version, and `g951` matches it exactly).
- The two runs are close in total churn but split differently. The `g94` run touches **more files and more source/config lines** (74 files, +163 excl. notes) than the `g951` run (68 files, +157 excl. notes); the `g951` run's larger raw insertion total (+470) is mostly its bigger `MIGRATION_NOTES.md` (313 lines vs 254).
- Both runs applied the same families of Provider-API transformations (`list`/`set`/`map`/`scalar`/`file_collection`/`dir`/`boolean`/`other`) across the build-conventions plugins, the `kotlin-native/build-tools` included build, and a similar set of subproject build scripts, and both flipped the same 15 convention-plugin `allWarningsAsErrors.set(true)` → `false`.
- Both runs needed the same throwaway-preview infrastructure relaxations (blanket jar trust in `verification-metadata.xml`, warnings-as-errors disabled). The `g94` run additionally disabled build-scan/Develocity-related settings against the older preview; the `g951` run instead needed a child-first classloader fix in `InstrumentJava.kt` (a `NoSuchMethodError` in the preview distro's bundled ASM).
- Both runs intentionally left the Kotlin Gradle Plugin source unmigrated (it compiles against a pinned Gradle API 7.6) and limited verification to `help` + `assemble`. The residual `MIGRATION_NOTES.md` entries in both are characterized as genuine false positives, dominated by the repo-local `Provider<RegularFile|Directory>.getFile()` extension and `Named.getName()`-style overrides; canonical-boilerplate count `0` and coverage check `OK` in both.
