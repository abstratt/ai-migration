# Semantic comparisons: baseline build vs Provider API branch build

Each comparison runs `clean assemble` twice on the same project:

- **Baseline build**: the baseline commit (the commit before "Swap Gradle Distribution" on the project's `gradle-10-migration/…` branch) on the Gradle 9.9.2 release.
- **Provider API branch build**: the migration branch tip on Gradle `9.9.0-20261124151743+0000`, built from the Provider API migration branch (revision `8779a723`).

An init script dumps the task graph and every task's inputs and outputs in a form that does not depend on the Gradle version, and the two dumps are compared. Every difference is tagged with a reason mnemonic.

Input values are compared by **eager-API semantics**: where a lazy property replaced an eager one, the dump reads it through the generated eager-getter adapter (`<Type>_Adapter.access_get_<accessor>`), which is what code compiled against an earlier Gradle sees. Reports marked "no" in the "Adapters" column read lazy properties directly, so an unset property shows as `null` where the eager getter returns a value (`VALUE-UNSET`).

The tools and the procedure are in the `provider-api-build-comparison` skill (`.claude/skills/provider-api-build-comparison/`). Dumps, logs and raw comparison output are in `out/task-compare-g992/<project>/` (not committed).

## Reports

Ordered from the smallest migration to the largest (build code the migration changed).

| Project | Report | Migration changed build code? | Task graph | Identical tasks | Adapters | Last run | Headline result |
|---|---|---|---|---|---|---|---|
| gradle-lint-plugin | [report](REPORT-gradle-lint-plugin.md) | No | 19 tasks, identical | 7 of 19 | yes | 2026-11-25 14:46 | No input value differs. Compiled classes identical; jars differ only in build date, Gradle version and commit hash |
| micronaut-core | [report](REPORT-micronaut-core.md) | No | 741 tasks, identical; `buildSrc` 9, identical | 646 of 741 | yes | 2026-11-25 14:58 | No input value differs. No build-product difference attributable to the distribution; three generated classes differ in element order (project non-determinism) |
| detekt | [report](REPORT-detekt.md) | Yes, 2 edits in 1 build script | Root 322, `build-logic` 13, `detekt-gradle-plugin` 8: all identical | 288 of 322 (root) | yes | 2026-11-25 15:30 | One eager getter returns a different value: `JavaExec.defaultCharacterEncoding` `UTF-8` → `null` (`EAGER-DEFAULT`). Root build products identical. In `build-logic`, a precompiled script plugin compiles to different bytecode because an assigned property changed type |
| groovy | [report](REPORT-groovy.md) | Yes, 7 files (+13/−12), 5 of them in `build-logic` | 497 tasks, identical; `build-logic` 9, identical | 423 of 497 | yes | 2026-11-25 17:57 | The migration's own edit makes javadoc receive three `-tag` options instead of one (the original code overwrote them); Javadoc HTML identical. No build-product difference attributable to the distribution; one class varies in method order between runs. In `build-logic`, the branch's Groovy DSL compiler wraps `+=` in unedited script code |
| kotest | [report](REPORT-kotest.md) | Yes, 2 files (+18/−9), including the project's Gradle plugin | 4,046 tasks, identical; `buildSrc` 14 | 1,938 of 4,046 | **no** | 2026-11-25 11:07 | **Published BOM broken**: a string template over `MavenPublication` coordinates interpolates `Property` objects (outside `assemble`). Otherwise equivalent when built at the same path |
| kafka | [report](REPORT-kafka.md) | Yes, about 15 edits in the root `build.gradle` (+16/−15) | 456 tasks, identical | 331 of 456 | yes | 2026-11-25 18:08 | One eager getter returns a different value: `JavaExec.defaultCharacterEncoding` `UTF-8` → `null` (`EAGER-DEFAULT`), no visible effect. Migrated compiler-argument code yields identical arguments; all 7,987 classes identical; jars differ only in entry timestamps |

Times are local (UTC−3), when the Provider API branch build's dump was written.

## Differences tied to the Gradle distribution

| Difference | Task type | Projects |
|---|---|---|
| eager getter `getDefaultCharacterEncoding()` returns `null` instead of the default charset when unset (`EAGER-DEFAULT`) | `JavaExec` | detekt, kafka |
| BOM coordinates built by string template over `MavenPublication.groupId`/`artifactId`/`version` interpolate `Property` objects | `buildSrc` convention plugin | kotest |
| input `selectedConfiguration` only in the Provider API branch build | `DependencyReportTask` | gradle-lint-plugin |
| `jacoco.toolVersion = …` compiles to `getToolVersion(): Property` plus `assign` instead of `setToolVersion(String)` | precompiled Kotlin script plugin | detekt (`build-logic`) |
| eager `options.getJFlags()` read after execution: 9.9.2 leaks the execution-time `-Xmx<maxMemory>` into the task's own options (shared list in the options copy); the branch does not. Both start javadoc with the same `-J-Xmx…` (`EXEC-MUTATION`) | `Javadoc` | groovy |
| compound assignments `a += b` in Groovy DSL scripts compile to `forCompoundAssignment(a) + b` wrapped in `toAssignmentResult(…)` (`DSL-TRANSFORM`) | precompiled Groovy script plugin | groovy (`build-logic`) |
| classpaths contain jars of the Gradle distribution itself (embedded Kotlin 2.4.21 vs 2.4.20, `gradle-api`) | compile tasks of plugin builds | gradle-lint-plugin, micronaut-core (`buildSrc`), detekt (`build-logic`), kotest (`buildSrc`), groovy (`build-logic`) |
| generated or compiled files that follow the distribution: adapter sources embedding the Gradle version; a Kotlin metadata flag and the implicit-imports compiler argument of `kotlin-dsl` | `buildSrc` / `build-logic` tasks | micronaut-core (`buildSrc`), detekt (`build-logic`), groovy (`build-logic`) |
| `previous-compilation-data.bin` differs, stable across two baseline runs; content not inspected | `GroovyCompile`, `JavaCompile` | groovy (9 tasks) |

## Differences not tied to the Gradle distribution

| Difference | Basis | Projects |
|---|---|---|
| Kotlin `last-build.bin` | Holds only the time of the build; differs between two runs of the baseline build (control runs in detekt). | gradle-lint-plugin, micronaut-core, detekt, kotest |
| Java `previous-compilation-data.bin` | Control run in kafka (1 task, differs between two baseline runs); in micronaut-core only on the two modules whose classes differ. | micronaut-core, kafka |
| Task outcomes that depend on what was on disk before the build (`DISK-STATE`) | Control run in detekt: the second baseline run has the Provider API branch build's outcomes. | detekt |
| Javadoc `-tag` options: one in the baseline build, three after the migration (`MIGRATED`: the original code's repeated `addStringOption('tag', …)` calls overwrote each other) | Read from `javadoc.options` on both sides; no source uses the tags, Javadoc output identical. | groovy |
| Order of two synthetic methods in a Groovy-compiled class | Groovy compiler non-determinism; differs between two runs of the baseline build. | groovy |
| Jar entry timestamps | The project preserves file timestamps; entries and content are equal. | kafka |
| Build date and commit hash in manifests | The two builds ran at different times from different commits. | gradle-lint-plugin |
| Absolute checkout path in generated files | The two builds ran in different directories. | detekt, kotest (2,750 Kotlin/Android files) |
| Order of two types in generated classes | Annotation-processor non-determinism. | micronaut-core |
| Tool noise: `toString()` text of `Javadoc` options; property query errors ("resolution without an exclusive lock") | Limitations of the dump script. | all |

## Caveats that apply to all reports

- The Provider API branch build identifies itself as 9.9.0 and the baseline build is 9.9.2, so the two also differ by mainline changes after the branch point (for example embedded Kotlin 2.4.20 vs 2.4.21). The reports do not separate these from Provider API changes.
- Only tasks reached by `assemble` are covered: no tests and no verification tasks.
- File collections are compared as sets, so a reordered classpath shows as identical.
- Properties the dump script cannot read are not compared.
- Reason mnemonics were assigned per project and checked by hand; the compare script does not produce them.
