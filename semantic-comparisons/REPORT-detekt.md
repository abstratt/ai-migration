# Task graph and task input/output differences: detekt, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `461748b90` | migration branch tip `79cced83a` (`gradle-10-migration/20260620-0232-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `9.9.0-20261124151743+0000` (built from the Provider API migration branch, revision `8779a723`) |
| JVM | Temurin 21.0.11 | Temurin 21.0.11 |
| Build result | passed | passed |

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache` with `task-dump.init.gradle`; the JSON dumps were then compared. No workaround was needed on either side. detekt is a composite build, so there is one dump per build:

| Build | Tasks, baseline build | Tasks, Provider API branch build | Identical tasks |
|---|---|---|---|
| root (`detekt`) | 322 | 322 | 288 |
| included `build-logic` | 13 | 13 | 8 |
| included `detekt-gradle-plugin` | 8 | 8 | 7 |

**Read this first**

- Input property values are compared by **eager-API semantics**. Where a lazy property replaced an eager one, the dump reads the value through the eager accessor generated for that property (`org.gradle.internal.classpath.generated.<Type>_Adapter.access_get_<originalAccessor>`, or the `$$BridgeFor$$` class of a custom adapter). That is what code compiled against an earlier Gradle gets when it calls the old getter. In the Provider API branch build, 866 input values across 158 tasks were read that way (836 in 154 root tasks, 15 in 2 tasks of each included build); the baseline build has no such accessors and is read as before.
- **One input value still differs when read through the adapter**: `JavaExec.defaultCharacterEncoding`, `UTF-8` → `null` (`EAGER-DEFAULT`). The 9.9.2 getter never returned `null` when the property was unset: it returned the daemon's default charset. Through the adapter, the branch's getter returns `null`. This is a change in the eager API's behaviour, not something the comparison introduced.
- This migration **changed build logic**: two edits in `detekt-generator/build.gradle.kts`. See "Migrated build logic".
- Each side was run with its distribution's `bin/gradle` directly, not through the wrapper. Before each run the `build` directories of both included builds were deleted, so their tasks executed too (`clean` does not reach included builds).
- In the root build and in `detekt-gradle-plugin`, **every compiled class, jar and generated script is identical**. The only build-product difference there is a checkout path inside one generated Markdown file.
- In `build-logic`, a precompiled script plugin compiles to different bytecode from unchanged source, because the API it is compiled against changed (`API-RECOMPILE`).
- The Provider API branch build identifies itself as 9.9.0, the baseline build as 9.9.2; they also differ by mainline changes after the branch point (embedded Kotlin 2.4.20 vs 2.4.21). Every difference is classified; items whose effect was not checked are marked as such.

## Migrated build logic

| Edit | Task | In the `assemble` graph? | Result |
|---|---|---|---|
| `standardOutput as ByteArrayOutputStream` → `standardOutput.get() as …` | `:detekt-generator:generateCliOptions` (`JavaExec`) | yes | Same dependencies and same inputs apart from the `EAGER-DEFAULT` row shared with the other `JavaExec` task. Output `_cli-options.md` is identical apart from the checkout path (`CHECKOUT-PATH`). |
| `commandLine = listOf(…)` → `commandLine(…)` | `:detekt-generator:verifyGeneratorOutput` (`Exec`) | **no** | Not exercised by this comparison. |

## Reason mnemonics

| Mnemonic | Kind | Meaning | Basis |
|---|---|---|---|
| `EAGER-DEFAULT` | Task API | The old eager getter returned a computed default when nothing was set; through the adapter, the branch's getter returns `null` because the lazy property is unset. | Verified in the source. In 9.9.2, `JvmOptions.getDefaultCharacterEncoding()` returns the `file.encoding` entry, which the constructor sets to `Charset.defaultCharset()` (`UTF-8` here; the daemon runs with `-Dfile.encoding=UTF-8` from detekt's `gradle.properties`). In the branch, `JavaForkOptions.getDefaultCharacterEncoding()` is a `Property<String>` without a convention. detekt sets it nowhere. Effect on the forked JVM, read from the code but **not checked at runtime**: the branch's `JvmOptions` still sets `file.encoding` to the default charset, and the outputs of both tasks are identical apart from `CHECKOUT-PATH`. |
| `API-RECOMPILE` | Outputs | A precompiled script plugin compiles to different bytecode from identical source, because a property it assigns changed type. | Verified with `javap` on `Module_gradle`: `jacoco.toolVersion = …` calls `JacocoPluginExtension.setToolVersion(String)` in the baseline build, and `getToolVersion(): Property` followed by `PropertyExtensionsKt.assign` in the Provider API branch build. `Module_gradle$2` and `Module_gradle$2$1` also differ in code; their individual call sites were not listed. |
| `KOTLIN-COMPILER` | Outputs | A class differs only in a Kotlin metadata flag; the bytecode is the same. | Verified with `javap`: no code difference, only the metadata `xi` value (944 vs 176). Attributed to the embedded Kotlin compiler (2.4.21 vs 2.4.20) by inference. |
| `KOTLIN-DSL` | Environment | Classpaths of `kotlin-dsl` tasks contain the embedded Kotlin and Kotlin compiler artifacts, which differ by version (2.4.21 vs 2.4.20). | Observed from the paths. |
| `GRADLE-LIBS` | Environment | A classpath contains jars of the Gradle distribution (`gradle-api`, `gradle-kotlin-dsl-*`, installation beacon). | Observed from the paths. |
| `IMPLICIT-IMPORTS` | Environment | The `kotlin-dsl` compiler argument listing the implicit imports has different content. | Verified in the previous version of this report: the baseline build lists 17 `org.gradle.api.problems.*ProblemGroup*` types that the Provider API branch build lacks; the Provider API branch build lists `org.gradle.api.provider.PresentProvider`, which the baseline build lacks. Same distributions here. |
| `CHECKOUT-PATH` | Comparison setup | A generated file embeds the absolute path of the checkout, and the two builds ran in different directories. | Verified with `diff`: the only differing lines are the two "Default:" paths. |
| `KT-STATE` | Outputs | Kotlin incremental-compilation state differs (`last-build.bin`, lookup tables, shrunk classpath snapshot); not a build product. | `last-build.bin` differs between two runs of the baseline build too (control run). The other 10 files under `build/kotlin/` (in `build-logic` only) are identical between the two baseline runs; they belong to the two tasks whose inputs and classes differ (`API-RECOMPILE`, `KOTLIN-COMPILER`, `KOTLIN-DSL`), and their content was not inspected. |
| `DISK-STATE` | Comparison setup | A task outcome depends on what was on disk before the build, not on the Gradle version. | Verified by the control run: the second baseline run has the same outcomes as the Provider API branch build. |
| `UPSTREAM` | Propagation | The file differs only because it contains the output of another task that already differs. | Verified by path. |
| `QUERY-ERROR` | Tool noise | The dump script could not read a property after the build. | Same error on both sides (`:compileJava` `options.annotationProcessorPath`, "resolution without an exclusive lock"); only the exception class name in the message differs. |

## Control run

The baseline build was run a second time, unchanged, again with the `build` directories of the two included builds removed first. Dumps are in `control/dump-before-rerun2*.json`; comparisons in `control/comparison-*.txt`.

| Build | Output files that differ, first baseline run vs Provider API branch build | First baseline run vs second baseline run | Second baseline run vs Provider API branch build |
|---|---|---|---|
| root | 31 `last-build.bin`, `_cli-options.md` | 31 `last-build.bin` | 31 `last-build.bin`, `_cli-options.md` |
| `build-logic` | 2 `last-build.bin`, 6 classes, 10 other files under `build/kotlin/`, `build-logic.jar` | 2 `last-build.bin` | same as the first column |
| `detekt-gradle-plugin` | 1 `last-build.bin` | 1 `last-build.bin` | 1 `last-build.bin` |

So `last-build.bin` is the only output that varies between runs on one Gradle version. Every other output difference in this report is stable across the two baseline runs.

Input values: the second baseline run and the Provider API branch build differ in exactly the same inputs as the first baseline run does (`EAGER-DEFAULT` in the root build, `IMPLICIT-IMPORTS` in `build-logic`).

Task outcomes: the first and second baseline runs differ on 3 root tasks, `:clean` (up-to-date → executed) and the two `JavaExec` tasks (executed → up-to-date, their outputs are outside `build/`). The second baseline run and the Provider API branch build have the same outcomes on every task. So the outcome differences in the main comparison are `DISK-STATE`.

## Task graph

No differences in any of the three builds: same tasks, same types, same `dependsOn` edges, same execution order. Outcomes differ on 3 root tasks only (`DISK-STATE`, see "Control run").

## Differences, root build

| Task type | Difference | Tasks | Reason |
|---|---|---|---|
| `JavaExec` | input `defaultCharacterEncoding`: `UTF-8` → `null` (read through `JavaExec_Adapter`) | 2 (all): `:detekt-generator:generateCliOptions`, `:detekt-generator:generateDocumentation` | `EAGER-DEFAULT` |
| `JavaExec` | outcome executed → up-to-date | the same 2 | `DISK-STATE` |
| `JavaExec` | output `website/docs/gettingstarted/_cli-options.md` | 1 | `CHECKOUT-PATH` |
| `Delete` | outcome up-to-date → executed | 1 (`:clean`) | `DISK-STATE` |
| `KotlinCompile` | output `last-build.bin` | 31 | `KT-STATE` |

## Differences, `build-logic`

| Task | Difference | Reason |
|---|---|---|
| `:compileKotlin` | output classes `Module_gradle`, `Module_gradle$2`, `Module_gradle$2$1` | `API-RECOMPILE` |
| `:compileKotlin` | output classes `Module_gradle$2$inlined$sam$…`, `Module_gradle$6$1$inlined$sam$…`, `Releasing_gradle$inlined$sam$…` | `KOTLIN-COMPILER` |
| `:compileKotlin`, `:compilePluginsBlocks` | input `compilerOptions.freeCompilerArgs` | `IMPLICIT-IMPORTS` |
| `:compileKotlin`, `:compilePluginsBlocks` | inputs `compileClasspath`, `pluginClasspath`, `defaultCompilerClasspath`, `classpathSnapshot` | `KOTLIN-DSL`, `GRADLE-LIBS` |
| `:compileKotlin`, `:compilePluginsBlocks` | outputs under `build/kotlin/` | `KT-STATE` |
| `:compileJava`, `:generatePrecompiledScriptPluginAccessors` | input classpaths | `KOTLIN-DSL`, `GRADLE-LIBS` |
| `:compileJava` | property query error on both sides | `QUERY-ERROR` |
| `:jar` | the six classes as input; output `build-logic.jar` | `UPSTREAM` |

## Differences, `detekt-gradle-plugin`

| Task | Difference | Reason |
|---|---|---|
| `:compileKotlin` | output `last-build.bin` | `KT-STATE` |

## Changes from the previous version of this report

- `Delete` (all 35 `clean` tasks), input `followSymlinks`: `false` → `null`, is gone. Read through `Delete_Adapter`, the branch returns `false`, as the baseline does.
- `JavaExec` input `enableAssertions`: `false` → `null`, is gone. Read through `JavaExec_Adapter`, the branch returns `false`.
- `JavaExec` input `defaultCharacterEncoding`: `UTF-8` → `null` remains, now as `EAGER-DEFAULT` instead of `VALUE-UNSET`: the eager getter itself returns a different value.
- Root identical tasks: 288 of 322 instead of 254.
- The previous version reported identical outcomes. In this run, the first baseline build ran from a different on-disk state, so 3 outcomes differ; the control run shows them to be `DISK-STATE`.

## Files

- `dump-before*.json`, `dump-after*.json`: the dumps (root, `build-logic`, `detekt-gradle-plugin`)
- `comparison*.txt`, `comparison*-verbose.txt`: `compare_dumps.py` output
- `before.log`, `after.log`: build logs
- `control/dump-before-rerun2*.json`, `control/rerun2-before.log`, `control/comparison-*.txt`: the control run
