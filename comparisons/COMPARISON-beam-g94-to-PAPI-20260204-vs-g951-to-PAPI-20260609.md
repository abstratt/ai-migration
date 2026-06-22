# Migration Comparison: beam

**Repository:** [abstratt/beam](https://github.com/abstratt/beam) (Apache Beam; migrated directly on `abstratt/beam`, which is also the authenticated GitHub account, so there is no separate fork — both migration branches are pushed to `abstratt/beam`)

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Branch** | [`gradle-10-migration/20260619-1957-g94-to-PAPI-20260204`](https://github.com/abstratt/beam/tree/gradle-10-migration/20260619-1957-g94-to-PAPI-20260204) | [`gradle-10-migration/20260619-2123-g951-to-PAPI-20260609`](https://github.com/abstratt/beam/tree/gradle-10-migration/20260619-2123-g951-to-PAPI-20260609) |
| **Base branch** | `master` | `master` |
| **Baseline → target** | Gradle 9.4.0 → preview `20260204` | Gradle 9.5.1 → preview `20260609` |
| **Report** | [`REPORT-20260619-1957.md`](https://github.com/abstratt/beam/blob/gradle-10-migration/20260619-1957-g94-to-PAPI-20260204/REPORT-20260619-1957.md) | [`REPORT-20260619-2123.md`](https://github.com/abstratt/beam/blob/gradle-10-migration/20260619-2123-g951-to-PAPI-20260609/REPORT-20260619-2123.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/beam/blob/gradle-10-migration/20260619-1957-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/beam/blob/gradle-10-migration/20260619-2123-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 53 | 65 |
| **Total lines changed** (excl. artifacts) | +352 / −254 (606 total) | +340 / −274 (614 total) |
| − Formatting / whitespace | 60 (0 files exclusively) | 0 |
| − Warnings-as-errors & deprecations | 0 (0 files) | 0 (0 files) |
| − Other infra relaxations | 0 (0 files) | 0 (0 files) |
| **= Core migration changes** | **546** | **614** |
| **Migration notes** | 116-line file (curated false-positive / root-cause groups) | 113-line file (curated false-positive / root-cause groups) |
| **Succeeded?** | ✅ Yes — `MIGRATED`; `./gradlew help` passes, `./gradlew assemble` compiles the whole tree (only 5 environmental failures) | ✅ Yes — `MIGRATED`; `./gradlew help` passes, `./gradlew assemble` compiles the whole tree (only 5 environmental failures) |

## Notes

- **Both runs are substantial, genuine migrations** — Apache Beam is a large multi-module Gradle build whose logic lives in an in-repo Groovy convention plugin (`buildSrc/.../BeamModulePlugin.groovy`) plus dozens of per-module `*.gradle`/`*.gradle.kts` files, so both pairs required real source changes. Neither run needed any warnings-as-errors or `verification-metadata.xml` relaxation, so `warnings` and `infra` are 0 in both columns; the `core` figure is essentially the whole diff.
- **The bulk of the work is Gradle-9 removed-API fixes, not Provider-API lazy-property work.** Both runs independently converged on the same dominant edits (derived from build errors, not from `migration-data.json`): `Project.exec{}` → injected `ExecOperations`; `archivesBaseName` → `base.archivesName`; `sourceCompatibility`/`targetCompatibility` → `java.*`; `reportsDir` → `reporting.baseDirectory`; `mainClassName`/`JavaExec.main` → `application.mainClass`/`mainClass`; `archivePath` → `archiveFile.get().asFile`; `IdeaModule.testSourceDirs` → `testSources.from`; `fileMode` → `filePermissions`; and three third-party plugin bumps for Gradle-9 compatibility (SpotBugs 5→6, protobuf 0.8.13→0.9.x, Kotlin 1.6.10→2.1.0).
- **The two runs diverge mainly in the cross-project `sourceSets` fix.** Run 2 (`g951`) additionally rewrites `project(":x").sourceSets` → `rootProject.project(":x").sourceSets` across many modules (and the paired `testClassesDirs += files(project(...))` sites keep their `+=` operator, changing only `project` → `rootProject`). This is the main reason Run 2 touches more files (65 vs 53) and shows more `core` lines (614 vs 546). Run 1 also carries 60 lines of pure formatting/whitespace churn that Run 2 does not.
- **The genuine Provider-API lazy-property work is small in both runs** and nearly identical: a handful of `ListProperty`/`MapProperty` resolve-and-set fixes and the `options.compilerArgs`/`forkOptions.jvmArgs` collection-append rewrites discussed in the Adjusted section below. A genuinely-necessary `options.compilerArgs -=` → `.set(get() - [...])` rewrite appears in both runs (Groovy has no `-=` operator on a lazy property).
- **Both runs succeeded with the same 5 residual `assemble` failures, all environmental** (out of scope, not Provider-API symptoms): 2 `setupVirtualenv` tasks failing with `sh` exit 127 because the host lacks a Python venv toolchain, and 3 modules (`sql:generateFmppSources`, `sbe`/`org.agrona`, an `it`/`splunk` artifact) failing on network timeouts resolving remote artifacts. Both runs classify these under the task-08 environmental carve-out and report status `MIGRATED`.

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs. Here `core` is the genuine Gradle-9-removal + Provider-API migration work; neither warnings nor infra patterns matched in either run.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn).

## Adjusted: excluding unnecessary supported-operator rewrites

Gradle supports the Groovy `<<` and `+=` append operators on lazy `ListProperty`/`SetProperty`. Rewriting `prop += [x]` to `prop.addAll([x])` is therefore unnecessary — the operator form keeps compiling and behaving identically. Both runs nonetheless rewrote every `options.compilerArgs += [...]` and `options.forkOptions.jvmArgs += ...` site (11 sites each: 8 single-line + 3 multiline arrays = **28 changed lines per run**, all in `buildSrc/.../BeamModulePlugin.groovy`). Excluding those rewrites:

| | Run 1 | Run 2 |
|---|---|---|
| Unnecessary `+=`→`.addAll` rewrite lines (excluded) | 28 | 28 |
| Build files that vanish entirely | 0 | 0 |
| **Files changed** (excl. artifacts): reported → adjusted | 53 → **53** | 65 → **65** |
| **Core migration changes**: reported → adjusted | 546 → **518** | 614 → **586** |

Rewrite kind: Groovy `+=` → `.addAll(…)` on `options.compilerArgs` / `options.forkOptions.jvmArgs`.

- **No file vanishes** — all 28 rewrite lines per run are inside `BeamModulePlugin.groovy`, which carries dozens of other genuinely-necessary edits, so the files-changed count is unaffected.
- **Only the `+=` rewrites are excluded.** The paired `options.compilerArgs -=` → `.set(get() - [...])` rewrite is kept (Groovy has no `-=` operator on a lazy property, so it is necessary), as are the `setCompileAndRuntimeJavaVersion` snapshot blocks (the helper mutates a plain `List`, so a `.get()`/`.set()` round-trip is required) and the `testClassesDirs += files(project(...))` sites (those keep `+=` and only change `project` → `rootProject`). The operator-related comments both runs added concern these necessary `-=`/snapshot changes, not the `+=` rewrites, so none are excluded as "incorrect operator comments".
- These rewrites are independent of which distribution each run targeted (the `+=` operator is supported on both preview distros), so excluding them leaves Run 2 still larger than Run 1 — the genuine target-specific difference is the cross-project `project` → `rootProject.project` sourceSets fix, not the operator churn.
