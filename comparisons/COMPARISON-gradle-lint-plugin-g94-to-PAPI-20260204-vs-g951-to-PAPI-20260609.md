# Migration Comparison: gradle-lint-plugin

**Repository:** [abstratt/gradle-lint-plugin](https://github.com/abstratt/gradle-lint-plugin) (nebula gradle-lint-plugin; migrated directly on `abstratt/gradle-lint-plugin`, which is also the authenticated GitHub account, so there is no separate fork)

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260619-1737-g94-to-PAPI-20260204`](https://github.com/abstratt/gradle-lint-plugin/tree/gradle-10-migration/20260619-1737-g94-to-PAPI-20260204) | [`gradle-10-migration/20260619-1749-g951-to-PAPI-20260609`](https://github.com/abstratt/gradle-lint-plugin/tree/gradle-10-migration/20260619-1749-g951-to-PAPI-20260609) |
| **Base branch** | `main` | `main` |
| **Report** | [`REPORT-20260619-1737.md`](https://github.com/abstratt/gradle-lint-plugin/blob/gradle-10-migration/20260619-1737-g94-to-PAPI-20260204/REPORT-20260619-1737.md) | [`REPORT-20260619-1749.md`](https://github.com/abstratt/gradle-lint-plugin/blob/gradle-10-migration/20260619-1749-g951-to-PAPI-20260609/REPORT-20260619-1749.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/gradle-lint-plugin/blob/gradle-10-migration/20260619-1737-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/gradle-lint-plugin/blob/gradle-10-migration/20260619-1749-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 1 | 1 |
| **Total lines changed** (excl. artifacts) | +2 / −3 (5 total) | +2 / −3 (5 total) |
| − Formatting / whitespace | 0 | 0 |
| − Warnings-as-errors & deprecations | 0 | 0 |
| − Other infra relaxations | 0 | 0 |
| **= Core migration changes** | **5** | **5** |
| **Migration notes** | 72-line file (false positives only) | 71-line file (false positives only) |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed |

## Notes

- **Both runs are essentially no-op migrations.** Neither distro pair required a single Provider-API source change. The only change on each branch is the 5-line `gradle/wrapper/gradle-wrapper.properties` edit — the baseline upgrade plus the distribution swap (drop `distributionSha256Sum`, point `distributionUrl` at the preview distribution, set `validateDistributionUrl=false`). The two wrapper diffs are identical except for the target `distributionUrl`.
- **The 5 "core" lines are the distribution swap, not Provider-API work.** `categorize_diff.py` classifies the wrapper edit as `core` because it matches none of the formatting/warnings/infra heuristics. There is no genuine lazy-property migration churn in either run — the residual is the wrapper itself.
- **Both runs found zero confirmed scanner hits.** `scan_usages.py` surfaced ~30 candidate sites per run (0 Cat-A confirmed; 29 Cat-B changed-return getters; 0 Cat-C; 0 Cat-D; 1 Cat-E), all `[unconfirmed]`. `apply_migrations.py` applied 0 rewrites in both runs. Manual review resolved every hit to a false positive — method-name collisions on non-Gradle receivers (`org.apache.maven.model.*`, `java.io.File`, `java.lang.System`, plain `org.gradle.api.artifacts.Dependency`, `ConfigurationContainer`, a nebula `GradleLintRule`, a `SingleFileReport`, and the task's own `listeners` field). Each run's `MIGRATION_NOTES.md` documents these with site-specific reasons and passes both task-06 audits (boilerplate count 0, coverage OK).
- **No predictable infra issues fired in either run.** The repo has no `gradle/verification-metadata.xml` and no warnings-as-errors flags, so neither the dependency-verification relaxation nor the `-Werror` disabling was needed. Tasks 07 and 08 made no changes in either run (`help`/`assemble` passed on the first attempt), so they produced no commits.
- **The migrations are equivalent across the two pairs** — identical files-changed, identical line counts, identical (empty) transformation set, both succeeding. The only difference is the baseline version (9.4.0 vs 9.5.1) and target preview distribution recorded in the wrapper.

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs. Here the 5 core lines per run are the wrapper distribution swap, which matches none of these patterns.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn).

## Adjusted: excluding unnecessary supported-operator rewrites

Neither run rewrote any supported append operator (`<<` / `+=`) to a method call (no source changes were made at all), so the figures above need no adjustment on this account.
