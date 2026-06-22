# Migration comparison: kotlinx.coroutines

**Repository:** [abstratt/kotlinx.coroutines](https://github.com/abstratt/kotlinx.coroutines) (`git@github.com:abstratt/kotlinx.coroutines.git`)

Two independent Gradle 9→10 Provider API migration runs of the same repository, each against a different distro pair, both branched from `master`. Columns are ordered by distro pair name.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Base branch** | `master` | `master` |
| **Migration branch** | [`gradle-10-migration/20260620-0208-g94-to-PAPI-20260204`](https://github.com/abstratt/kotlinx.coroutines/tree/gradle-10-migration/20260620-0208-g94-to-PAPI-20260204) | [`gradle-10-migration/20260620-0238-g951-to-PAPI-20260609`](https://github.com/abstratt/kotlinx.coroutines/tree/gradle-10-migration/20260620-0238-g951-to-PAPI-20260609) |
| **Report** | [`REPORT-20260620-0208.md`](https://github.com/abstratt/kotlinx.coroutines/blob/gradle-10-migration/20260620-0208-g94-to-PAPI-20260204/REPORT-20260620-0208.md) | [`REPORT-20260620-0238.md`](https://github.com/abstratt/kotlinx.coroutines/blob/gradle-10-migration/20260620-0238-g951-to-PAPI-20260609/REPORT-20260620-0238.md) |
| **Migration notes** | _none_ (task 06 scanned 0 sites) | _none_ (task 06 scanned 0 sites) |
| **Total lines changed** (excl. artifacts) | 75 | 65 |
| − formatting | 0 | 0 |
| − warnings-as-errors & deprecations | 0 | 6 (2 files) |
| − other infra relaxations | 0 | 0 |
| **= core migration changes** | **75** | **59** |
| **Files changed** | 11 (warnings: 0, infra: 0) | 11 (warnings: 2 — `buildSrc/build.gradle.kts`, `gradle.properties`; infra: 0) |
| **Succeeded?** | ✅ Yes (status: **migrated**) | ✅ Yes (status: **migrated**) |

Both runs are classified **migrated**: `./gradlew help` and `./gradlew assemble` pass for every JVM/JS/WASM/Kotlin-Native compilation target. The only `assemble` failure in each run is the macOS-native benchmark *link* step, which fails solely because the host has Command Line Tools rather than full Xcode (`xcrun` cannot find `xcodebuild`) — an environmental blocker unrelated to the migration that would fail identically on the unmigrated baseline.

The two runs make near-identical core changes (baseline-upgrade compatibility fixes plus Provider-API lazy `.get()` reads surfaced as compile errors — the Kotlin-DSL/`.kt` scanner blind spot). The main difference is that Run 2 (`g951-to-PAPI-20260609`) additionally relaxed warnings-as-errors flags (6 lines across `buildSrc/build.gradle.kts` and `gradle.properties`) that its newer preview distribution promoted deprecation warnings into, whereas Run 1's preview did not require that relaxation. Both touched 11 files.

## Methodology

Change counts come from `comparisons/categorize_diff.py` run over `git diff <base>...<branch>` (three-dot) against a throwaway clone fetched fresh from the repository's GIT URL — not the local `migrated/` working copies. The helper excludes the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) and splits changed lines into four disjoint buckets that sum to the total, using the precedence: infra-by-path → warnings → infra-by-content → formatting → core. `formatting` is exact (whitespace-ignoring diff, `git diff -w`); `warnings` and `infra` are pattern-based heuristics. Patterns matched by the helper for these runs — warnings: `allWarningsAsErrors`, `warningsAsErrors`, `-?Werror\b`, `\bwerror\b`, `disable\.werror`, `deprecation`; infra-by-path: `gradle/verification-metadata.xml`; infra-by-content: `develocity`, `gradle-?[eE]nterprise`, `buildScan`, `build-scan`. The qualitative succeeded/failed status comes from each run's `REPORT-<timestamp>.md`.
