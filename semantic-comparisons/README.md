# Semantic comparisons: baseline build vs Provider API branch build

Each comparison runs `clean assemble` twice on the same project:

- **Baseline build**: the baseline commit (the commit before "Swap Gradle Distribution" on the project's `gradle-10-migration/…` branch) on the Gradle 9.9.2 release.
- **Provider API branch build**: the migration branch tip on a distribution built from the Provider API migration branch. The "Branch build" column names it per project:
  - `018f16a`: Gradle `10.0.0-20261126124457+0000`, revision `018f16a2641`;
  - `8779a72`: Gradle `9.9.0-20261124151743+0000`, revision `8779a723` (an earlier build of the branch).

An init script dumps the task graph and every task's inputs and outputs in a form that does not depend on the Gradle version, and the two dumps are compared. Every difference is tagged with a reason mnemonic.

Input values are compared by **eager-API semantics**: where a lazy property replaced an eager one, the dump reads it through the generated eager-getter adapter (`<Type>_Adapter.access_get_<accessor>`), which is what code compiled against an earlier Gradle sees. Reports marked "no" in the "Adapters" column read lazy properties directly, so an unset property shows as `null` where the eager getter returns a value (`VALUE-UNSET`).

The tools and the procedure are in the `provider-api-build-comparison` skill (`.claude/skills/provider-api-build-comparison/`). Dumps, logs and raw comparison output are in `out/task-compare-g992/<project>/` (not committed).

## Reports

Ordered from the smallest migration to the largest (build code the migration changed).

| Project | Report | Migration changed build code? | Task graph | Differing tasks | Adapters | Branch build | Last run | Headline result |
|---|---|---|---|---|---|---|---|---|
| gradle-lint-plugin | [report](REPORT-gradle-lint-plugin.md) | No | 19 tasks, identical | 12 of 19 | yes | `018f16a` | 2026-11-26 15:46 | No input value differs. Compiled classes identical; jars differ only in build date, Gradle version and commit hash |
| micronaut-core | [report](REPORT-micronaut-core.md) | No | 741 tasks, identical; `buildSrc` 9, identical | 84 of 741 | yes | `018f16a` | 2026-11-26 16:02 | No input value differs. No build-product difference attributable to the distribution; one generated class differs in element order (project non-determinism). Java incremental-compilation state written in a different order on 27 modules |
| detekt | [report](REPORT-detekt.md) | Yes, 2 edits in 1 build script | Root 322, `build-logic` 13, `detekt-gradle-plugin` 8: all identical | 34 of 322 (root) | yes | `8779a72` | 2026-11-25 15:30 | One eager getter returns a different value: `JavaExec.defaultCharacterEncoding` `UTF-8` → `null` (`EAGER-DEFAULT`). Root build products identical. In `build-logic`, a precompiled script plugin compiles to different bytecode because an assigned property changed type |
| groovy | [report](REPORT-groovy.md) | Yes, 7 files (+13/−12), 5 of them in `build-logic` | 497 tasks, identical; `build-logic` 9, identical | 74 of 497 | yes | `8779a72` | 2026-11-25 17:57 | The migration's own edit makes javadoc receive three `-tag` options instead of one (the original code overwrote them); Javadoc HTML identical. No build-product difference attributable to the distribution; one class varies in method order between runs. In `build-logic`, the branch's Groovy DSL compiler wraps `+=` in unedited script code |
| kotest | [report](REPORT-kotest.md) | Yes, 2 files (+18/−9), including the project's Gradle plugin | 4,046 tasks, identical; `buildSrc` 14 | 2,108 of 4,046 | **no** | `8779a72` | 2026-11-25 11:07 | **Published BOM broken**: a string template over `MavenPublication` coordinates interpolates `Property` objects (outside `assemble`). Otherwise equivalent when built at the same path |
| kafka | [report](REPORT-kafka.md) | Yes, about 15 edits in the root `build.gradle` (+16/−15) | 456 tasks, identical | 125 of 456 | yes | `8779a72` | 2026-11-25 18:08 | One eager getter returns a different value: `JavaExec.defaultCharacterEncoding` `UTF-8` → `null` (`EAGER-DEFAULT`), no visible effect. Migrated compiler-argument code yields identical arguments; all 7,987 classes identical; jars differ only in entry timestamps |

A task differs when anything recorded for it differs: an input value, an input or output file, its outcome, or the text of a property it could not read. Most differing tasks have no build-product difference; each report classifies every one.

Times are local (UTC−3), when the Provider API branch build's dump was written.

## Reason mnemonics

Every difference in a report is tagged with one of these. Each report's "Basis" table gives the project-specific evidence for the ones it uses.

| Mnemonic | Kind | Meaning |
|---|---|---|
| `API-ADDED` | Task API | The task type declares an input property that it does not declare in the baseline build. |
| `API-REBIND` | Compilation | Same as `API-RECOMPILE`. |
| `API-RECOMPILE` | Compilation | Unchanged build source compiles to different bytecode because a Gradle API it uses changed, e.g. an assigned property changed type. |
| `BUILD-METADATA` | Outputs | A generated manifest or properties file embeds the build date or the Gradle version. |
| `BUILD-TIME` | Outputs | An archive differs only in the timestamps of its entries, which record when each build ran. |
| `CHECKOUT-PATH` | Comparison setup | A generated file embeds the absolute path of the checkout, and the two builds ran in different directories. |
| `COMPILE-ORDER` | Outputs | Incremental-compilation state (`previous-compilation-data.bin`) holds the same values in a different order, consistently between distributions. Not a build product. |
| `COMPILE-STATE` | Outputs | Incremental-compilation state (`previous-compilation-data.bin`) differs. Not a build product. |
| `DERIVED-CP` | Environment | Data computed from a classpath (e.g. Kotlin classpath snapshots) differs because the classpath differs. |
| `DISK-STATE` | Comparison setup | A task outcome or a configuration-time value depends on what was on disk before the build, not on the Gradle version. |
| `DISTRIBUTION` | Environment | Same as `GRADLE-LIBS`. |
| `DSL-TRANSFORM` | Outputs | The branch's Groovy DSL compiler rewrites compound assignments `a += b` into `forCompoundAssignment(a) + b` wrapped in `toAssignmentResult(…)`, to support `+=` on lazy properties; 9.9.2 has no such transform. |
| `EAGER-DEFAULT` | Task API | The old eager getter returned a computed default when nothing was set; read through the adapter, the branch's getter returns `null` because the lazy property is unset. A real change in the eager API. |
| `EXEC-MUTATION` | Task API | A task action modifies its own input, so a value read after execution differs from the value the task started with. |
| `GEN-ORDER` | Project non-determinism | A compiler or annotation processor emits the same elements (methods, constants) in an order that varies between runs; everything else is identical. |
| `GIT-REV` | Comparison setup | The build records the commit hash, and the two builds ran from different commits. |
| `GRADLE-LIBS` | Environment | A classpath contains files of the Gradle distribution itself: generated `gradle-api` / `gradle-test-kit` jars, the installation beacon, embedded Kotlin. |
| `GRADLE-VERSION` | Outputs | A file contains the Gradle version, or a path under the version-specific Gradle cache directory. |
| `IMPLICIT-IMPORTS` | Environment | The `kotlin-dsl` compiler argument that lists the implicit imports has different content, because the two distributions' public APIs differ. |
| `KOTLIN-COMPILER` | Outputs | A class differs only in a Kotlin metadata flag; the bytecode is the same. |
| `KOTLIN-DSL` | Environment | Classpaths of `kotlin-dsl` tasks contain the distribution's embedded Kotlin and Kotlin compiler artifacts, which differ by version. |
| `KT-STATE` | Outputs | Kotlin incremental-compilation state (`last-build.bin`, lookup tables, shrunk classpath snapshot) differs. Not a build product. |
| `MIGRATED` | Build logic | The difference follows from a source change made by the migration. |
| `MIGRATED-SOURCE` | Build logic | Same as `MIGRATED`. |
| `PROJECT-PATH` | Comparison setup | Same as `CHECKOUT-PATH`. |
| `QUERY-ERROR` | Tool noise | The dump script could not read a property; only the error text differs, or the property appears on one side only. The property is not compared. |
| `RUN-VARIANCE` | Outputs | Differs between two runs of the same build at the same path; same as `KT-STATE` or `COMPILE-STATE`. |
| `TOSTRING` | Tool noise | The value is an object without a stable string form; only its `toString()` text differs. |
| `UPSTREAM` | Propagation | The file differs only because it is, or contains, the output of another task that already differs. |
| `VALUE-UNSET` | Task API | A lazy property read directly, not through the adapter, shows `null` where the eager getter returned a default. |
| `VERSION-STRING` | Outputs | A generated file embeds the Gradle version. |
| `WORKAROUND` | Build logic | Consequence of a workaround the migration applied on the branch. |

## Differences tied to the Gradle distribution

| Difference | Task type | Projects |
|---|---|---|
| eager getter `getDefaultCharacterEncoding()` returns `null` instead of the default charset when unset (`EAGER-DEFAULT`) | `JavaExec` | detekt, kafka |
| BOM coordinates built by string template over `MavenPublication.groupId`/`artifactId`/`version` interpolate `Property` objects | `buildSrc` convention plugin | kotest |
| input `selectedConfiguration` only in the Provider API branch build | `DependencyReportTask` | gradle-lint-plugin |
| `jacoco.toolVersion = …` compiles to `getToolVersion(): Property` plus `assign` instead of `setToolVersion(String)` | precompiled Kotlin script plugin | detekt (`build-logic`) |
| eager `options.getJFlags()` read after execution: 9.9.2 leaks the execution-time `-Xmx<maxMemory>` into the task's own options (shared list in the options copy); the branch does not. Both start javadoc with the same `-J-Xmx…` (`EXEC-MUTATION`) | `Javadoc` | groovy |
| compound assignments `a += b` in Groovy DSL scripts compile to `forCompoundAssignment(a) + b` wrapped in `toAssignmentResult(…)` (`DSL-TRANSFORM`) | precompiled Groovy script plugin | groovy (`build-logic`) |
| classpaths contain jars of the Gradle distribution itself (`gradle-api`, installation beacon; on `8779a72` also embedded Kotlin 2.4.20 vs 2.4.21) | compile tasks of plugin builds | gradle-lint-plugin, micronaut-core (`buildSrc`), detekt (`build-logic`), kotest (`buildSrc`), groovy (`build-logic`) |
| generated or compiled files that follow the distribution: adapter sources embedding the Gradle version; a Kotlin metadata flag and the implicit-imports compiler argument of `kotlin-dsl` | `buildSrc` / `build-logic` tasks | micronaut-core (`buildSrc`), detekt (`build-logic`), groovy (`build-logic`) |
| `previous-compilation-data.bin` differs, the same way in two baseline runs (in micronaut-core on all but `micronaut-jackson-databind`, whose classes differ). In micronaut-core: the same 32-bit values in a different order (`COMPILE-ORDER`); in groovy, content not inspected | `JavaCompile`, `GroovyCompile` | micronaut-core (27 tasks), groovy (9 tasks) |

## Differences not tied to the Gradle distribution

| Difference | Basis | Projects |
|---|---|---|
| Kotlin `last-build.bin` | Holds only the time of the build; differs between two runs of the baseline build (control runs in detekt and micronaut-core). | gradle-lint-plugin, micronaut-core, detekt, kotest |
| Java `previous-compilation-data.bin` | Control runs: differs between two baseline runs on 1 task in kafka and 1 in micronaut-core (a module whose classes differ). | kafka, micronaut-core |
| Task outcomes that depend on what was on disk before the build (`DISK-STATE`) | Control run in detekt: the second baseline run has the Provider API branch build's outcomes. | detekt |
| Javadoc `-tag` options: one in the baseline build, three after the migration (`MIGRATED`: the original code's repeated `addStringOption('tag', …)` calls overwrote each other) | Read from `javadoc.options` on both sides; no source uses the tags, Javadoc output identical. | groovy |
| Order of two synthetic methods in a Groovy-compiled class | Groovy compiler non-determinism; differs between two runs of the baseline build. | groovy |
| Jar entry timestamps | The project preserves file timestamps; entries and content are equal. | kafka |
| Build date and commit hash in manifests | The two builds ran at different times from different commits. | gradle-lint-plugin |
| Absolute checkout path in generated files | The two builds ran in different directories. | detekt, kotest (2,750 Kotlin/Android files) |
| Order of two types in generated classes | Annotation-processor non-determinism; differs between two runs of the baseline build. | micronaut-core |
| Tool noise: `toString()` text of `Javadoc` options; property query errors ("resolution without an exclusive lock") | Limitations of the dump script. | all |

## Caveats that apply to all reports

- The Provider API branch build identifies itself as 10.0.0 (`018f16a`) or 9.9.0 (`8779a72`) and the baseline build is 9.9.2, so the two also differ by mainline changes outside the Provider API branch (on `8779a72`, for example, embedded Kotlin 2.4.20 vs 2.4.21). The reports do not separate these from Provider API changes.
- Only tasks reached by `assemble` are covered: no tests and no verification tasks.
- File collections are compared as sets, so a reordered classpath shows as identical.
- Properties the dump script cannot read are not compared.
- Reason mnemonics were assigned per project and checked by hand; the compare script does not produce them.
