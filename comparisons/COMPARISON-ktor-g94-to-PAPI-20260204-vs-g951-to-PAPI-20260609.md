# Migration Comparison: ktor

**Repository:** [`abstratt/ktor`](https://github.com/abstratt/ktor) — `git@github.com:abstratt/ktor.git`

Two migration runs of the same repository (base branch `main`), each targeting a different distro pair.

| | **Run A — g94-to-PAPI-20260204** | **Run B — g951-to-PAPI-20260609** |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` (Gradle 9.4.0 → provider-api preview 2026-02-04) | `g951-to-PAPI-20260609` (Gradle 9.5.1 → provider-api preview 2026-06-09) |
| **Base branch** | [`main`](https://github.com/abstratt/ktor/tree/main) | [`main`](https://github.com/abstratt/ktor/tree/main) |
| **Migration branch** | [`gradle-10-migration/20260619-1903-g94-to-PAPI-20260204`](https://github.com/abstratt/ktor/tree/gradle-10-migration/20260619-1903-g94-to-PAPI-20260204) | [`gradle-10-migration/20260619-2004-g951-to-PAPI-20260609`](https://github.com/abstratt/ktor/tree/gradle-10-migration/20260619-2004-g951-to-PAPI-20260609) |
| **Report** | [`REPORT-20260619-1903.md`](https://github.com/abstratt/ktor/blob/gradle-10-migration/20260619-1903-g94-to-PAPI-20260204/REPORT-20260619-1903.md) | [`REPORT-20260619-2004.md`](https://github.com/abstratt/ktor/blob/gradle-10-migration/20260619-2004-g951-to-PAPI-20260609/REPORT-20260619-2004.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/ktor/blob/gradle-10-migration/20260619-1903-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/ktor/blob/gradle-10-migration/20260619-2004-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Total lines changed** (excl. artifacts) | 53 | 46 |
| − formatting | 0 | 0 |
| − warnings-as-errors & deprecations | 0 | 7 |
| − other infra relaxations | 7 | 0 |
| **= core migration changes** | **46** | **39** |
| **Files changed** | 7 (infra: 1, warnings: 0) | 7 (warnings: 2, infra: 0) |
| **Succeeded?** | **No** (FAILED) — Provider API migration is complete and compiles cleanly; `./gradlew help` passes, but `./gradlew assemble` is blocked by an environmental Kotlin/Native Apple-toolchain gap (no full Xcode on the host), not by a migration defect | **Yes** (MIGRATED) — build configures and compiles under the preview distribution; the only `assemble` failures are the same Kotlin/Native Apple-target tasks, an environmental toolchain gap unrelated to the migration |

## Observations

- **Core migration size is comparable** across pairs: 46 vs 39 lines. Both runs converged on the same real Provider-API sites — `UrlArtifactRepository.url`, `Wrapper.distributionUrl`, the `MavenPublication`/`MavenArtifact` string properties, and the `BaseExecSpec` assign-operator import in `VcpkgInstall.kt`.
- **The non-core split differs by pair, not by migration work.** Run A spent its non-core lines on an infra relaxation (the `develocity` precompiled-plugin extension accessor missing from the 2026-02-04 preview). Run B spent its non-core lines on disabling `allWarningsAsErrors` (Gradle 9.6 DSL deprecations promoted to errors), which the 2026-06-09 preview surfaced. These are predictable per-distribution infrastructure issues, not differences in the Provider-API code change.
- **Both runs hit the identical sole blocker**: the host has only Command Line Tools (no full Xcode), so Kotlin/Native Apple-target `cinterop`/compile tasks fail. This is independent of the distro pair and of the migration.

## Methodology

Change counts come from `comparisons/categorize_diff.py` run over `git diff <base>...<branch>` (three-dot) against a throwaway clone fetched fresh from the repository URL — not the local `migrated/` working copies. The helper excludes the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) and splits changed lines into four disjoint buckets that sum to the total, applying precedence **infra-by-path → warnings → infra-by-content → formatting → core**:

- **formatting** — whitespace/indent/blank-line-only churn, computed exactly via a whitespace-ignoring diff (`git diff -w`);
- **warnings** — warnings-as-errors & deprecation-suppression flag changes (pattern-based heuristic; matched patterns include `allWarningsAsErrors`, `warningsAsErrors`, `-Werror`, `werror`, `disable.werror`, `deprecation`);
- **infra** — other throwaway-preview relaxations (pattern-based heuristic; infra-by-path `gradle/verification-metadata.xml`; infra-by-content `develocity`, `gradle-enterprise`, `buildScan`, `build-scan`);
- **core** — the residual: the genuine Provider-API migration work (the primary figure to compare).

`formatting` is exact; `warnings` and `infra` are pattern-based heuristics. The qualitative succeeded/failed status comes from each run's `REPORT-<timestamp>.md`.
