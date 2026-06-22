# Migration Comparison: detekt

**Repository:** [`abstratt/detekt`](https://github.com/abstratt/detekt) — `git@github.com:abstratt/detekt.git`

Two migration runs of the same repository (base branch `main`), each targeting a different distro pair.

| | **Run A — g94-to-PAPI-20260204** | **Run B — g951-to-PAPI-20260609** |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` (Gradle 9.4.0 → provider-api preview 2026-02-04) | `g951-to-PAPI-20260609` (Gradle 9.5.1 → provider-api preview 2026-06-09) |
| **Base branch** | [`main`](https://github.com/abstratt/detekt/tree/main) | [`main`](https://github.com/abstratt/detekt/tree/main) |
| **Migration branch** | [`gradle-10-migration/20260620-0214-g94-to-PAPI-20260204`](https://github.com/abstratt/detekt/tree/gradle-10-migration/20260620-0214-g94-to-PAPI-20260204) | [`gradle-10-migration/20260620-0232-g951-to-PAPI-20260609`](https://github.com/abstratt/detekt/tree/gradle-10-migration/20260620-0232-g951-to-PAPI-20260609) |
| **Report** | [`REPORT-20260620-0214.md`](https://github.com/abstratt/detekt/blob/gradle-10-migration/20260620-0214-g94-to-PAPI-20260204/REPORT-20260620-0214.md) | [`REPORT-20260620-0232.md`](https://github.com/abstratt/detekt/blob/gradle-10-migration/20260620-0232-g951-to-PAPI-20260609/REPORT-20260620-0232.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/detekt/blob/gradle-10-migration/20260620-0214-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/detekt/blob/gradle-10-migration/20260620-0232-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Total lines changed** (excl. artifacts) | 87 | 11 |
| − formatting | 0 | 0 |
| − warnings-as-errors & deprecations | 6 | 0 |
| − other infra relaxations | 25 | 0 |
| **= core migration changes** | **56** | **11** |
| **Files changed** | 10 (warnings: 3, infra: 6) | 2 (warnings: 0, infra: 0) |
| **Succeeded?** | **No** (FAILED) — `./gradlew help` does not pass: the third-party Shadow plugin (`com.gradleup.shadow:9.4.2`) throws `NoSuchMethodError` on apply because the 2026-02-04 preview changed `Configuration.extendsFrom(Provider…)` from a varargs to a single-argument overload. A preview-distribution-vs-precompiled-plugin binary incompatibility triggered by the task-04 distribution swap, not a Provider-API defect in detekt's own build scripts — but per the mechanical rule, `help` not passing means failed | **Yes** (MIGRATED) — `./gradlew help` and `./gradlew assemble` both exit 0 under the preview distribution |

## Observations

- **Core migration size differs sharply** (56 vs 11 lines), but the two runs are not measuring the same thing: Run A failed at configuration before completing, so its larger core count reflects the distribution swap propagated across multiple included builds (root, `build-logic`, `detekt-gradle-plugin`) rather than more Provider-API work. Run B's 11 core lines are the wrapper swap plus two genuine Provider-API fixes in `detekt-generator/build.gradle.kts` (`commandLine` and `standardOutput` now Provider/Property types).
- **The non-core split is concentrated in Run A.** Run A spent 6 lines disabling warnings-as-errors (across three `gradle.properties` files) and 25 lines on other infra relaxations (across the included builds), whereas Run B needed neither — its preview did not require those relaxations to configure.
- **The two runs end in different outcomes** owing to the third-party Shadow-plugin binary incompatibility surfaced only by the 2026-02-04 preview distribution; the 2026-06-09 preview configures and assembles cleanly.

## Methodology

Change counts come from `comparisons/categorize_diff.py` run over `git diff <base>...<branch>` (three-dot) against a throwaway clone fetched fresh from the repository URL — not the local `migrated/` working copies. The helper excludes the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) and splits changed lines into four disjoint buckets that sum to the total, applying precedence **infra-by-path → warnings → infra-by-content → formatting → core**:

- **formatting** — whitespace/indent/blank-line-only churn, computed exactly via a whitespace-ignoring diff (`git diff -w`);
- **warnings** — warnings-as-errors & deprecation-suppression flag changes (pattern-based heuristic; matched patterns include `allWarningsAsErrors`, `warningsAsErrors`, `-Werror`, `werror`, `disable.werror`, `deprecation`);
- **infra** — other throwaway-preview relaxations (pattern-based heuristic; infra-by-path `gradle/verification-metadata.xml`; infra-by-content `develocity`, `gradle-enterprise`, `buildScan`, `build-scan`);
- **core** — the residual: the genuine Provider-API migration work (the primary figure to compare).

`formatting` is exact; `warnings` and `infra` are pattern-based heuristics. The qualitative succeeded/failed status comes from each run's `REPORT-<timestamp>.md`.
