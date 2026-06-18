# Migration Comparison: kotest

**Repository:** [kotest/kotest](https://github.com/kotest/kotest) (migrated via fork [abstratt/kotest](https://github.com/abstratt/kotest))

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260618-1017-g94-to-PAPI-20260204`](https://github.com/abstratt/kotest/tree/gradle-10-migration/20260618-1017-g94-to-PAPI-20260204) | [`gradle-10-migration/20260618-0925-g951-to-PAPI-20260609`](https://github.com/abstratt/kotest/tree/gradle-10-migration/20260618-0925-g951-to-PAPI-20260609) |
| **Base branch** | `master` | `master` |
| **Report** | [`REPORT-20260618-1017.md`](https://github.com/abstratt/kotest/blob/gradle-10-migration/20260618-1017-g94-to-PAPI-20260204/REPORT-20260618-1017.md) | [`REPORT-20260618-0925.md`](https://github.com/abstratt/kotest/blob/gradle-10-migration/20260618-0925-g951-to-PAPI-20260609/REPORT-20260618-0925.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/kotest/blob/gradle-10-migration/20260618-1017-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/kotest/blob/gradle-10-migration/20260618-0925-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 3 | 3 |
| **Total lines changed** (excl. artifacts) | +16 / −16 (32 total) | +20 / −11 (31 total) |
| − Formatting / whitespace | 0 | 0 |
| − Warnings-as-errors & deprecations | 0 | 0 |
| − Other infra relaxations | 6 (1 file) | 0 |
| **= Core migration changes** | **26** | **31** |
| **Migration notes entries** | 6 bullet entries (37-line file) | 4 bullet entries (27-line file) |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed |

## Notes

- **Core migration churn is small and close between runs** — 26 lines (g94) vs 31 lines (g951), each spread over 3 files (wrapper properties + one source file + one build/settings script). Both runs found that task 06's automated rewriter emitted **zero** mechanical changes; all Provider-API source fixes surfaced as `assemble` compile errors (the scanner's documented Kotlin type-resolution blind spot) and were fixed by hand in tasks 07/08.
- **The two runs fixed different source files**, reflecting the different baseline and target distributions:
  - `g94` touched `buildSrc/src/main/kotlin/publishingUtils.kt` — `GenerateMavenPom.getDestination()` changed from `File` to `RegularFileProperty` (`.map → .flatMap`, `.get().asFile` resolution in the task action).
  - `g951` touched `kotest-framework-plugin-gradle/.../KotestPlugin.kt` — `boolean`/`set`/`file_collection` accessor renames (`ignoreExitValue`, `failOnNoMatchingTests`, `includePatterns`/`excludePatterns`, `classpath`) plus an `import org.gradle.kotlin.dsl.assign` to preserve the `=` assignment forms.
- **Neither run made formatting-only or warnings-as-errors changes** (both buckets are 0).
- **The infra bucket differs because of which relaxation each run needed:**
  - `g94`'s 6 infra lines are the removal of the incompatible `com.gradle.develocity` plugin and its `develocity { }` block from `settings.gradle.kts` (matched by the `develocity` content heuristic).
  - `g951` instead disabled IntelliJ `instrumentCode` in `kotest-intellij-plugin/build.gradle.kts` (an ASM `NoSuchMethodError` from the preview distribution). This is also a preview-only relaxation, but it is **not** matched by the infra heuristic, so it falls into `g951`'s **core** count — accounting for part of the 31-vs-26 gap. Adjusting for it, the genuine Provider-API work is comparable between the two runs.
- Both runs left `validateDistributionUrl=false` and their respective plugin relaxations as preview-only workarounds to be reverted against a released Gradle 10, and both documented the same **6 residual scanner hits across 4 files** (2 Cat-B `TestEngine` false positives, 2 Cat-C surviving operator forms, 2 Cat-D `classpath` assignment hits) as curated false positives / operator-preserved sites.

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs. Note that preview-only relaxations not matching these patterns (e.g. the `g951` `instrumentCode = false` change) are not separately bucketed and land in `core`.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn).
