# Task graph and task input/output differences: kafka, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `4746ada405` ("Upgrade Baseline Gradle") | migration branch tip `90f39bd803` (`gradle-10-migration/20260615-2121-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `9.9.0-20261124151743+0000` (built from the Provider API migration branch, revision `8779a723`) |
| JVM | Temurin 21.0.11 | Temurin 21.0.11 |
| Tasks in graph | 456 | 456 |
| Build result | passed | passed |

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache` with `task-dump.init.gradle`; the two JSON dumps were then compared. No workaround was needed on either side. kafka has no `buildSrc` and no included builds, so there is one dump per side.

**Read this first**

- Input property values are compared by **eager-API semantics**. Where a lazy property replaced an eager one, the dump reads the value through the eager accessor generated for that property (`org.gradle.internal.classpath.generated.<Type>_Adapter.access_get_<originalAccessor>`, or the `$$BridgeFor$$` class of a custom adapter). That is what code compiled against an earlier Gradle gets when it calls the old getter. In the Provider API branch build, 1,264 input values across 222 tasks were read that way; the baseline build has no such accessors and is read as before.
- **One input value still differs when read through the adapter**: `JavaExec.defaultCharacterEncoding`, `UTF-8` → `null`, on the 8 `processMessages` code generators (`EAGER-DEFAULT`, the same finding as in detekt). The 9.9.2 getter returned the default charset when nothing was set; the branch's getter returns `null`. The generated sources compile to identical classes, so it had no visible effect here.
- This migration **changed build logic**: about 15 places in the root `build.gradle` where compiler arguments were appended with `<<` or `+=` now call `.add(…)` / `.addAll(…)`. The affected values are identical on both sides. See "Migrated build logic".
- Each side was run with its distribution's `bin/gradle` directly, not through the wrapper. The baseline worktree has one local edit, the wrapper pointing at 9.9.2, which this run does not use.
- **All 7,987 compiled class files are byte-identical, and every jar has the same entries with the same content.**
- 125 of the 456 tasks differ (in an input value, a file, an outcome or a read error); all of them are covered by the rows below.
- Apart from `EAGER-DEFAULT` (8 tasks) and `QUERY-ERROR` (34 tasks, tool noise), every difference is also seen between two runs of the baseline build (see "Control run").

## Summary

| Area | Result |
|---|---|
| Task graph | Same 456 tasks, same types, same `dependsOn` edges, same execution order |
| Task outcomes | Same (337 executed, 87 no-source, 31 up-to-date, 1 skipped) |
| Compiler arguments (migrated code) | Identical on all 74 compile tasks |
| Compiled classes | 7,987 class files, all byte-identical |
| Jars | 71 of the 72 jar files differ as files; they differ only in entry timestamps (`BUILD-TIME`) |

## Migrated build logic

| Edit | Tasks affected | Result |
|---|---|---|
| `options.compilerArgs << …` / `+= […]` → `.add(…)` / `.addAll(…)` | 71 `JavaCompile`, 3 `ScalaCompile` | `options.compilerArgs` has the same values in the same order on every task. Example, `:clients:compileJava`: `-encoding UTF-8 -Xlint:all -Xlint:-serial -Xlint:-try -Werror` on both sides. |
| `scalaCompileOptions.additionalParameters += […]` → `.add(…)` / `.addAll(…)` | 3 `ScalaCompile` | `scalaCompileOptions.additionalParameters` identical on every task. |
| `options.compilerArgs << "-Xlint:-cast"` → `.add(…)` in `:jmh-benchmarks` | 1 `JavaCompile` | Identical. |

Not exercised: branches that depend on build properties left at their defaults (the Scala optimizer modes `method` and `inline-*`, and `keepAliveMode=SESSION`), and the test compile tasks, which `assemble` does not run.

## Reason mnemonics

| Mnemonic | Kind | Meaning | Basis |
|---|---|---|---|
| `EAGER-DEFAULT` | Task API | The old eager getter returned a computed default when nothing was set; through the adapter, the branch's getter returns `null` because the lazy property is unset. | Verified in the source in the detekt report (same distributions): 9.9.2 `JvmOptions.getDefaultCharacterEncoding()` returns the default charset; in the branch, `JavaForkOptions.getDefaultCharacterEncoding()` is a `Property<String>` without a convention. kafka sets it nowhere. Effect: the classes compiled from the generated sources are identical on both sides; the forked JVM's `file.encoding` was **not checked** at runtime. |
| `BUILD-TIME` | Outputs | An archive differs only in the timestamps of its entries, which record when each build ran. | The project sets `preserveFileTimestamps = true`. Verified on disk for all 72 jars (second baseline run vs Provider API branch build): entry names, order, sizes and CRCs are equal; one jar (the empty root `kafka-…jar`) is byte-identical. For the first baseline run, the dumps show every class file identical; its jars' entry lists were not inspected. |
| `COMPILE-STATE` | Outputs | `previous-compilation-data.bin` (incremental-compilation state, not a build product) differs although the compiled classes are identical. | Only `:jmh-benchmarks:compileJava`, and it differs between the two baseline runs too. What varies was **not traced**. |
| `UPSTREAM` | Propagation | The file differs only because it is, or contains, the output of another task that already differs. | Verified by path: every changed input file is one of the `BUILD-TIME` jars, or a file under shadow's `expanded/zip_<hash>/` directories (checked in the previous version of this report). |
| `QUERY-ERROR` | Tool noise | The dump script could not read a property after the build ("resolution … without an exclusive lock"). | Same error on both sides; only the exception class name in the message differs (`GradleException` → `IllegalResolutionException`). Consequence: on these tasks the unreadable property was **not compared**. |

## Control run

The baseline build was run a second time, unchanged, into `control/dump-before-rerun2.json`.

| Comparison | Tasks that differ |
|---|---|
| First baseline run vs Provider API branch build | 125 |
| First baseline run vs second baseline run | 92 |
| Second baseline run vs Provider API branch build | 125, the same tasks |

The 92 tasks that differ between the two baseline runs are all among the 125. The other 33 differ only in `QUERY-ERROR` text. So every output difference in this report also appears between two runs on one Gradle version. The 8 `EAGER-DEFAULT` tasks are among the 92 because their classpath contains the `generator` jar (`UPSTREAM` of `BUILD-TIME`); their `defaultCharacterEncoding` is equal between the two baseline runs. Inputs and outcomes are identical between the two baseline runs.

## Differences

Each row is one kind of difference; the count is the number of tasks showing it.

### Task inputs and declared properties

| Tasks | Task type | Difference | Reason |
|---|---|---|---|
| 8 of 8 | `JavaExec` | input `defaultCharacterEncoding`: `"UTF-8"` → `null` (read through `JavaExec_Adapter`) | `EAGER-DEFAULT` |
| 34 | `JavaCompile` (31 of 71), `ScalaCompile` (3 of 3) | property query error on both sides, different exception class name | `QUERY-ERROR` |

The properties that could not be read are `classpath` and `options.annotationProcessorPath` (on `no-source` tasks) and `scalaClasspath` (on executed `ScalaCompile` tasks). For 33 of the 34 tasks this is the only difference.

### Outputs

| Tasks | Task type | Difference | Reason |
|---|---|---|---|
| 72 (71 jar files differ) | `Jar` (70 of 71), `ShadowJar` (2 of 2) | jar differs only in entry timestamps | `BUILD-TIME` |
| 1 | `JavaCompile` (`:jmh-benchmarks`) | `previous-compilation-data.bin` | `COMPILE-STATE` |
| 8 | `JavaExec` | `classpath` contains the `generator` jar | `UPSTREAM` |
| 6 | `JavaCompile` (5), `ScalaCompile` (1) | `classpath` contains the `kafka-clients` jar | `UPSTREAM` |
| 6 | `Copy` (`copyDependantLibs`) | copies of project jars in `dependant-libs-*` | `UPSTREAM` |
| 1 | `:jmh-benchmarks:shadowJar` | inputs: project jars and their expanded contents | `UPSTREAM` |

## Limitations of this comparison

- `assemble` compiles main code only. Test compilation, tests, checkstyle and spotbugs tasks were not run.
- File collections are compared as sets. A classpath with the same entries in a different order shows as identical.
- Jar files are hashed raw, which is why timestamp-only differences appear. Entry content was compared separately to classify them.
- Properties that could not be read on either side (`QUERY-ERROR`) are not part of the comparison.
- The Provider API branch build identifies itself as 9.9.0, the baseline build as 9.9.2; they also differ by mainline changes after the branch point.

## Changes from the previous version of this report

- Inputs are now read through the eager-API adapters. `Delete.followSymlinks` (67 tasks) and `JavaExec.enableAssertions` (8 tasks), previously `VALUE-UNSET` (`false` → `null`), are gone: through the adapters, the branch returns `false`, as the baseline does.
- `JavaExec.defaultCharacterEncoding` `UTF-8` → `null` remains, now as `EAGER-DEFAULT`: the eager getter itself returns a different value.
- Each side now runs the distribution's `bin/gradle` directly; the baseline previously ran through the wrapper.
- Differing tasks: 125 of 456 instead of 220.
- `previous-compilation-data.bin` differs on 1 task instead of 32 (previously `RUN-VARIANCE`; renamed `COMPILE-STATE` to match the other reports). Why fewer differ in this run was not traced.
- The previous run's files are in `pre-adapter/`.

## Files

In `out/task-compare-g992/kafka/`:

- `dump-before.json`, `dump-after.json`: the dumps
- `comparison.txt`, `comparison-verbose.txt`: `compare_dumps.py` output
- `before.log`, `after.log`: build logs
- `control/dump-before-rerun2.json`, `control/rerun2-before.log`, `control/comparison-*.txt`: the control run
- `pre-adapter/`: the previous version's dumps, logs, control run (`pcd-check/`) and report
