# Migration Comparison: gradle

**Repository:** [gradle/gradle](https://github.com/gradle/gradle) (migrated via fork [abstratt/gradle](https://github.com/abstratt/gradle))

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

> **Scope note:** `gradle/gradle` *is* the Gradle build tool, so only its **build logic** (`build-logic*`, `build-logic-settings`, and product `*.gradle.kts` scripts) runs against the preview Provider-API distribution and was migrated. The product/test source under `subprojects/**` and `platforms/**` compiles against sibling in-repo modules carrying the **old** API names — never the wrapper distribution — so its ~2,650–2,900 scanner hits are out-of-scope false positives and were intentionally left unchanged. Both runs made the same scope decision.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260618-1204-g94-to-PAPI-20260204`](https://github.com/abstratt/gradle/tree/gradle-10-migration/20260618-1204-g94-to-PAPI-20260204) | [`gradle-10-migration/20260618-1106-g951-to-PAPI-20260609`](https://github.com/abstratt/gradle/tree/gradle-10-migration/20260618-1106-g951-to-PAPI-20260609) |
| **Base branch** | `master` | `master` |
| **Report** | [`REPORT-20260618-1204.md`](https://github.com/abstratt/gradle/blob/gradle-10-migration/20260618-1204-g94-to-PAPI-20260204/REPORT-20260618-1204.md) | [`REPORT-20260618-1106.md`](https://github.com/abstratt/gradle/blob/gradle-10-migration/20260618-1106-g951-to-PAPI-20260609/REPORT-20260618-1106.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/gradle/blob/gradle-10-migration/20260618-1204-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/gradle/blob/gradle-10-migration/20260618-1106-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 30 (4 warnings, 2 infra) | 19 (all core) |
| **Total lines changed** (excl. artifacts) | +100 / −68 (168 total) | +62 / −36 (98 total) |
| − Formatting / whitespace | 2 | 0 |
| − Warnings-as-errors & deprecations | 11 (4 files) | 0 |
| − Other infra relaxations | 11 (2 files) | 0 |
| **= Core migration changes** | **144** | **98** |
| **Migration notes** | 94-line hand-written grouped false-positive analysis | 148-line hand-curated false-positive analysis |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed |

## Notes

- **Core migration churn is larger for g94 (144 lines) than g951 (98 lines)**, across more files (30 vs 19). Both runs found that task 06's automated rewriter applied **zero** mechanical changes — every confirmed scanner hit in the in-scope build logic was a false positive (the scanner matched a property *name* against an unrelated Gradle class while the real receiver was `java.io.File`, the docs plugin's own model types, japicmp/javassist, non-lazy `Project`/`Task` accessors, etc.). All genuine Provider-API breakages surfaced as `help`/`assemble` compile errors (the scanner's documented Kotlin type-resolution blind spot) and were fixed by hand in tasks 07/08.
- **The gap is partly accounting, not just work.** g94's diff includes a separately-bucketed **11-line warnings-as-errors** relaxation (disabling `org.gradle.kotlin.dsl.allWarningsAsErrors` in `gradle.properties` plus three Kotlin convention sources) and an **11-line infra** relaxation (a blanket `<trust .../>` in `verification-metadata.xml` and disabling the binary-incompatible Develocity plugin). g951 needed **none** of these — `validateDistributionUrl`/`verify-metadata` were already relaxed in the fork's checked-in state, and its target distribution did not trip the Develocity `NoSuchMethodError` or the warnings-as-errors deprecation failures. So part of g94's higher total is preview-scaffolding that g951 simply did not require.
- **Both runs fixed the same families of Provider-API breakages** in build logic — `boolean` accessor renames (`ignoreExitValue`, `failOnNoMatchingTests`), `read_only` `commandLine`/`javaVersion` providers, `map` `systemProperties` (`MapProperty`), `set` `includePatterns`/`commandLineIncludePatterns` (`SetProperty`), and the dominant **operator/assignment-overload rule** (adding `import org.gradle.kotlin.dsl.assign` / `.*` to preserve `=`/`+=`/`mapProp[k]` forms in plain `.kt` convention sources rather than rewriting to method calls). Overlapping files include `BuildEnvironmentService.kt`, `TestType.kt`, `gradlebuild.cross-version-tests.gradle.kts`, `platforms/documentation/docs/build.gradle.kts`, and the two `platforms/**` `build.gradle.kts` scripts.
- **g94 carried extra internal-API drift fixes** beyond the Provider-API patterns (e.g. `DependencyFactory.createProjectDependency` → `dependencies.project(...)`, removing a `Test.setClasspath` override and relocating the kotlin-daemon-client reorder), which g951 did not report — another contributor to g94's larger core count.
- **Neither run modified product source** under `subprojects/**` or `platforms/**`; both confirmed the build-logic-only scope by a green `./gradlew assemble`. Both left `validateDistributionUrl=false` and their respective relaxations as preview-only workarounds to be reverted against a released Gradle 10.

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs. Preview-only relaxations not matching these patterns are not separately bucketed and land in `core`.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn). For reference, g94's report quotes "31 files, +194/−68" and g951's quotes "20 files, +210/−36" — both inclusive of the artifacts excluded here.
