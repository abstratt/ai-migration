# Migration Comparison: grpc-java

**Repository:** [abstratt/grpc-java](https://github.com/abstratt/grpc-java) (fork of `grpc/grpc-java`; migration branches pushed to the `abstratt` fork)

Comparison of the latest completed Gradle 9 → 10 migration run for each distro pair of the same repository. Columns are ordered by distro pair name. Change counts are computed with `comparisons/categorize_diff.py` over `git diff <base>...<branch>` (artifacts excluded); status is taken from each run's `REPORT-*.md`.

| | Run 1 | Run 2 |
|---|---|---|
| **Distro pair** | `g94-to-PAPI-20260204` | `g951-to-PAPI-20260609` |
| **Distro pair label** | Gradle 9.4.0 → provider-api preview (2026-02-04) | Gradle 9.5.1 → provider-api preview (2026-06-09) |
| **Branch** | [`gradle-10-migration/20260619-2041-g94-to-PAPI-20260204`](https://github.com/abstratt/grpc-java/tree/gradle-10-migration/20260619-2041-g94-to-PAPI-20260204) | [`gradle-10-migration/20260619-2113-g951-to-PAPI-20260609`](https://github.com/abstratt/grpc-java/tree/gradle-10-migration/20260619-2113-g951-to-PAPI-20260609) |
| **Base branch** | `master` | `master` |
| **Report** | [`REPORT-20260619-2041.md`](https://github.com/abstratt/grpc-java/blob/gradle-10-migration/20260619-2041-g94-to-PAPI-20260204/REPORT-20260619-2041.md) | [`REPORT-20260619-2113.md`](https://github.com/abstratt/grpc-java/blob/gradle-10-migration/20260619-2113-g951-to-PAPI-20260609/REPORT-20260619-2113.md) |
| **Migration notes** | [`MIGRATION_NOTES.md`](https://github.com/abstratt/grpc-java/blob/gradle-10-migration/20260619-2041-g94-to-PAPI-20260204/MIGRATION_NOTES.md) | [`MIGRATION_NOTES.md`](https://github.com/abstratt/grpc-java/blob/gradle-10-migration/20260619-2113-g951-to-PAPI-20260609/MIGRATION_NOTES.md) |
| **Files changed** (excl. artifacts) | 7 | 8 |
| **Total lines changed** (excl. artifacts) | +51 / −35 (86 total) | +61 / −36 (97 total) |
| − Formatting / whitespace | 2 | 0 |
| − Warnings-as-errors & deprecations | 0 (0 files) | 0 (0 files) |
| − Other infra relaxations | 0 (0 files) | 0 (0 files) |
| **= Core migration changes** | **84** | **97** |
| **Migration notes** | 81-line file (false positives / documentation only) | 77-line file (false positives / documentation only) |
| **Succeeded?** | ✅ migrated — `./gradlew help` passes; `assemble` blocked only by environmental failures | ✅ migrated — `./gradlew help` passes; `assemble` blocked only by environmental failures |

## Notes

- **The genuine Provider-API change is tiny and identical across both runs.** The only Provider-API source change in either run is the animalsniffer `CodeQualityExtension.sourceSets` migration (a `list` kind: `Collection<SourceSet>` → `ListProperty<SourceSet>`) in `core/build.gradle` and `util/build.gradle`. Both runs rewrote the Groovy assignment `sourceSets = [...]` to `sourceSets.set([...])` (Groovy has no assignment overload for a lazy property) and qualified the elements as `project.sourceSets.main` / `project.sourceSets.test` so they resolve against the project's `SourceSetContainer` rather than the extension's own now-lazy `sourceSets` via closure delegation. This was a scanner blind spot (a `prop = value` on a third-party extension) that surfaced as a `help` configuration error in task 07. Everything else in the diff is wrapper regeneration and baseline Gradle-9 fixes (see below).
- **`core` is dominated by wrapper-script regeneration, not Provider-API work.** The baseline upgrade (task 03) and distribution swap (task 04) regenerate `gradlew` (24 changed lines) and `gradlew.bat` (26 changed lines) in both runs; those ~50 line-changes carry no infra/warnings/whitespace signal, so the heuristic files them under `core`. The actual hand-written migration edits are far smaller: the two `animalsniffer` blocks plus the `settings.gradle` module-gating, totaling roughly a dozen meaningful lines per run.
- **The runs diverge only in their baseline Gradle-9 fixes, not in Provider-API work.** Both runs had to neutralize the `gae-jdk8` interop-testing module, whose AppEngine plugin (`com.google.cloud.tools.appengine` 2.8.7) references the removed `WarPluginConvention` and cannot configure under Gradle 9 — but they chose different gates:
  - **Run 1** gates it behind the project's existing `skipAndroid` flag (3 changed lines beyond the removed `include`).
  - **Run 2** introduces a dedicated `skipApp​Engine` flag (default-skip, with an explanatory `println` in the `else` branch) — a larger settings change — **and** additionally fixed `netty/shaded/build.gradle`, where `project(':grpc-netty').configurations…` no longer resolves because Gradle 9 removed the `Project`-delegating accessors on `ProjectDependency`; it was rewritten to `rootProject.project(':grpc-netty').configurations…`. That extra file and the more elaborate gate are why Run 2 shows one more changed file (8 vs 7) and ~11 more changed lines. Both fixes are Gradle 8→9 baseline removals, not Provider-API migration.
- **Both runs end with the same status and the same environmental blockers.** `./gradlew help` passes against the preview distribution in both runs (run with `-PskipAndroid=true`). `./gradlew assemble` does not exit 0 in either run, but only because of two failures both reports confirm reproduce identically on the unmigrated `master` tree under the baseline distribution: (1) `shadowJar` tasks fail under the Shadow 8.3.0 plugin's ASM 9.9 incompatibility (`Remapper.mapValue(Integer)`), and (2) `:grpc-compiler` native C++ codegen fails for lack of host protobuf C++ headers/toolchain. Neither is attributable to the Provider API migration, so task 09 records **migrated** (not failed) for both.
- **Both runs found zero confirmed scanner hits requiring auto-rewrite.** `apply_migrations.py` applied no Cat-A rewrites in either run; the single Provider-API edit (animalsniffer) was a detect-only / blind-spot site fixed by hand after the task-07 `help` failure. Each `MIGRATION_NOTES.md` documents the scan results and passes both task-06 audits (canonical-boilerplate count 0, coverage OK).

## Methodology

- Counts come from `comparisons/categorize_diff.py` run against a fresh clone of the GIT URL, over `git diff <base>...<branch>` with the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`) excluded. The changed lines (additions + deletions) are split into four **disjoint** buckets that reconcile exactly to the total: `formatting + warnings + infra + core = total`.
- **`formatting` is exact** — it is the difference between the normal diff and a whitespace-/blank-line-ignoring diff (`git diff -w --ignore-blank-lines`).
- **`warnings` and `infra` are pattern-based heuristics.** Line classification precedence is: infra-by-path (`gradle/verification-metadata.xml`) → warnings (`allWarningsAsErrors`, `warningsAsErrors`, `-Werror`/`werror`, `disable.werror`, `deprecation`) → infra-by-content (`develocity`, `gradle-enterprise`, `buildScan`, `build-scan`) → formatting → core. **`core`** is the residual and is the primary figure to compare across runs. Neither run touched `verification-metadata.xml`, warnings-as-errors flags, or Develocity/build-scan config, so `warnings` and `infra` are 0 for both; here `core` is wrapper-script regeneration plus the build-script edits described above.
- These figures intentionally differ from the raw `git diff --shortstat` totals quoted inside each `REPORT-*.md` (which include the `MIGRATION_NOTES.md`/`REPORT` artifacts and do not separate out non-migration churn).

## Adjusted: excluding unnecessary supported-operator rewrites

Neither run rewrote any supported append operator (`<<` / `+=`) to a method call. The one operator-style change in each run — `sourceSets = [...]` → `sourceSets.set([...])` — is a Groovy assignment to a lazy `ListProperty`, for which Groovy provides no assignment overload, so `.set(...)` is required rather than an avoidable rewrite. The core figures above therefore need no adjustment on this account.
