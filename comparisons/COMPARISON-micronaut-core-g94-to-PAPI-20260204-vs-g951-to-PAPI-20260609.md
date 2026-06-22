# Migration Comparison: micronaut-core

**Repository:** [abstratt/micronaut-core](https://github.com/abstratt/micronaut-core) (fork of `micronaut-projects/micronaut-core`; migration branches pushed to the `abstratt` fork)

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260619-1827-g94-to-PAPI-20260204`](https://github.com/abstratt/micronaut-core/tree/gradle-10-migration/20260619-1827-g94-to-PAPI-20260204) | [`gradle-10-migration/20260619-1844-g951-to-PAPI-20260609`](https://github.com/abstratt/micronaut-core/tree/gradle-10-migration/20260619-1844-g951-to-PAPI-20260609) |
| **Base branch** | `main` | `main` |
| **Report** | [`REPORT-20260619-1827.md`](https://github.com/abstratt/micronaut-core/blob/gradle-10-migration/20260619-1827-g94-to-PAPI-20260204/REPORT-20260619-1827.md) | [`REPORT-20260619-1844.md`](https://github.com/abstratt/micronaut-core/blob/gradle-10-migration/20260619-1844-g951-to-PAPI-20260609/REPORT-20260619-1844.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/micronaut-core/blob/gradle-10-migration/20260619-1827-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/micronaut-core/blob/gradle-10-migration/20260619-1844-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 2 (1 infra) | 1 |
| **Total lines changed** (excl. artifacts) | +9 / −2 (11 total) | +2 / −2 (4 total) |
| − Formatting / whitespace | 0 | 0 |
| − Warnings-as-errors & deprecations | 0 | 0 |
| − Other infra relaxations | 3 (1 file: `gradle.properties`) | 0 |
| **= Core migration changes** | **8** | **4** |
| **Migration notes** | 20-line file (false positives only) | 28-line file (false positives only) |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed |

## Notes

- **Both runs are essentially no-op Provider-API migrations.** Neither distro pair required a single Provider-API source change. micronaut-core's build logic runs through external `io.micronaut.build.*` binary convention plugins, so there are no in-repo lazy-property call sites to migrate. The only universally-shared change is the `gradle/wrapper/gradle-wrapper.properties` distribution swap (point `distributionUrl` at the preview distribution, set `validateDistributionUrl=false`; no `distributionSha256Sum` was present to drop). The baseline upgrade (task 03) was a no-op in both runs — the repo wrapper was already at 9.5.1 ≥ both pairs' baselines.
- **The one real difference between the runs is a preview-distribution incompatibility, not Provider-API work.** The `g94-to-PAPI-20260204` preview distribution removed an internal Develocity API (`GradleEnterprisePluginConfig.getDevelocityUrl()`) that the Develocity plugin bundled via `io.micronaut.build.shared.settings` still calls, so `./gradlew help` failed with `NoSuchMethodError` until that run added `develocity.enabled=false` (plus a 6-line explanatory comment) to `gradle.properties`. The `g951-to-PAPI-20260609` preview distribution does not exhibit this, so that run needed no such relaxation. This is the entire reason Run 1 shows more changed lines and an extra changed file.
- **`categorize_diff.py` splits the Develocity block across buckets.** Of the 7 added `gradle.properties` lines in Run 1, 3 match the `develocity` infra-content pattern (counted as `infra`) and the other 4 (a blank line and comment text without the keyword) fall to `core`. So Run 1's `core=8` is the 4-line wrapper swap plus 4 lines of the Develocity comment block — a heuristic artifact, not genuine migration churn. Run 2's `core=4` is purely the wrapper swap.
- **Both runs found zero confirmed scanner hits.** `scan_usages.py` surfaced only 3 candidate sites per run, all `[unconfirmed]` and all false positives in Micronaut's annotation-processor *application* source (none import `org.gradle`) — JDK `Class.getName()` calls and a locally-declared `isIncremental(...)` method. `apply_migrations.py` applied 0 rewrites in both runs. Each run's `MIGRATION_NOTES.md` documents the false positives and passes both task-06 audits (boilerplate count 0, coverage OK).
- **Tasks 07/08 outcomes.** In Run 2, both `./gradlew help` and `./gradlew assemble` passed on the first attempt with no edits (no commits). In Run 1, `assemble` passed first-try but `help` required the Develocity fix above (committed under the task-07 title). `assemble` emits pre-existing javadoc doclint messages in both runs (non-fatal, unrelated to the migration).

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs. Here the core lines are the wrapper distribution swap (both runs) plus, in Run 1, the keyword-free remainder of the Develocity comment block.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn).

## Adjusted: excluding unnecessary supported-operator rewrites

Neither run rewrote any supported append operator (`<<` / `+=`) to a method call (no source changes were made at all), so the figures above need no adjustment on this account.
