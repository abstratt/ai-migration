# Migration Comparison: kotlin

**Repository:** [JetBrains/kotlin](https://github.com/JetBrains/kotlin) (migrated via fork [abstratt/kotlin](https://github.com/abstratt/kotlin))

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260617-1412-g94-to-PAPI-20260204`](https://github.com/abstratt/kotlin/tree/gradle-10-migration/20260617-1412-g94-to-PAPI-20260204) | [`gradle-10-migration/20260617-1202-g951-to-PAPI-20260609`](https://github.com/abstratt/kotlin/tree/gradle-10-migration/20260617-1202-g951-to-PAPI-20260609) |
| **Base branch** | `master` (@ `77e77a815`) | `master` (@ `77e77a815`) |
| **Report** | [`REPORT-20260617-1412.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260617-1412-g94-to-PAPI-20260204/REPORT-20260617-1412.md) | [`REPORT-20260617-1202.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260617-1202-g951-to-PAPI-20260609/REPORT-20260617-1202.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260617-1412-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/kotlin/blob/gradle-10-migration/20260617-1202-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 67 | 65 |
| **Total lines changed** (excl. artifacts) | +135 / −80 (215 total) | +127 / −74 (201 total) |
| − Formatting / whitespace | 0 | 10 |
| − Warnings-as-errors & deprecations | 41 (19 files) | 41 (19 files) |
| − Other infra relaxations | 4 (1 file) | 3 (1 file) |
| **= Core migration changes** | **170** | **147** |
| **Migration notes entries** | 393 bullet entries (477-line file) | 171 bullet entries (282-line file) |
| **Succeeded?** | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed | ✅ Yes — `./gradlew help` and `./gradlew assemble` both succeed |

## Notes

- **Core migration churn is close, with `g94` slightly larger.** Excluding formatting, warnings-as-errors, and infra relaxations, the genuine Provider-API work is **170 lines across 67 files** for `g94` vs **147 lines across 65 files** for `g951` — both runs applied the same families of transformations across the build-conventions plugins, the `kotlin-native/build-tools` included build, and a similar set of subproject build scripts.
- **Only `g951` made any formatting/whitespace-only changes** (10 lines vs 0 for `g94`) — a small amount of incidental reflow; `g94` made none, consistent with the migration policy of not making cosmetic edits.
- **The warnings-as-errors relaxation is identical between runs** (41 lines over the same 19 files): flipping `allWarningsAsErrors true → false` across the convention-plugin `build.gradle.kts` files plus the `gradle.properties` files (root, `gradle-build-conventions`, `gradle-settings-conventions`), and the accompanying `kotlin.build.disable.werror` / relaxation comments.
- **The infra bucket is the `gradle/verification-metadata.xml` blanket jar-trust relaxation** in both runs (4 vs 3 lines). Other per-run plumbing differences noted in the reports (the `g951` run's `InstrumentJava.kt` classloader fix for an ASM `NoSuchMethodError`; the `kgp-npm-tooling-helper` `.set()` rewrites that lack the assignment plugin) are not separately bucketed by the heuristic and fall into core — they are small and do not change the picture.
- Both runs reported the wrapper was already at Gradle `9.5.1`, so the baseline-upgrade task (03) made no change in either case (the `g94` baseline of 9.4.0 is below the existing version, and `g951` matches it exactly).
- Both runs intentionally left the Kotlin Gradle Plugin source unmigrated (it compiles against a pinned Gradle API) and limited verification to `help` + `assemble`. The `MIGRATION_NOTES.md` entries are dominated by residual `scan_usages.py` hits characterized as curated false positives / deferred sites — `g94`'s notes file is substantially longer (477 vs 282 lines) but that is audit-trail volume, not code change.

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn).
