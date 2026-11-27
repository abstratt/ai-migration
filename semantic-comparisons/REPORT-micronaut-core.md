# Task graph and task input/output differences: micronaut-core, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `c4fcf5622` ("chore: Bump version to 5.1.3-SNAPSHOT") | migration branch tip `f48ed2d53` (`gradle-10-migration/20260619-1844-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `10.0.0-20261126124457+0000` (built from the Provider API migration branch, revision `018f16a2641`) |
| JVM | Temurin 25.0.3 | Temurin 25.0.3 |
| Tasks in graph | 741 (root), 9 (`buildSrc`) | 741 (root), 9 (`buildSrc`) |
| Build result | passed | passed |

No input value differs and no build product differs because of the distribution; the only distribution-dependent output is the Java incremental-compilation state, which holds the same values in a different order on 27 modules (`COMPILE-ORDER`).

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache -I task-dump.init.gradle`, each with its distribution's `bin/gradle`. No workaround was needed. `buildSrc/build` was deleted on both sides first, since `clean` does not reach `buildSrc`.

## Summary

| Area | Result |
|---|---|
| Task graph | Same 741 tasks (root) and 9 (`buildSrc`), same types, same dependency edges, same planned order |
| Task outcomes | Same on every task |
| Differing tasks | 32 of 741 (root), 5 of 9 (`buildSrc`); none added or removed |
| Build code changed by the migration | None (only the wrapper files, plus the generated notes and report) |
| Task inputs | No value differs. 4,610 values in 446 root tasks and 33 in 3 `buildSrc` tasks were read through the eager-getter adapters |
| Compiled classes | All 4,792 root-build classes identical. In `buildSrc`, the 8 generated adapter classes differ (`VERSION-STRING`) |
| Jars | All 155 root-build jars identical. `buildSrc.jar` differs only in the 8 adapter classes (`UPSTREAM`) |
| Other outputs | `previous-compilation-data.bin` of 27 `JavaCompile` tasks (`COMPILE-ORDER`); Kotlin `last-build.bin` of 5 tasks (`KT-STATE`) |

## Basis

Mnemonics are defined in the [index](README.md#reason-mnemonics).

| Mnemonic | Basis |
|---|---|
| `COMPILE-ORDER` | `previous-compilation-data.bin` of 27 `JavaCompile` tasks. Verified byte by byte: each pair of files has the same size and the same bytes; the 61 differing regions each split into runs that are either identical or permutations of 4-byte words (count-prefixed sets of 32-bit values, separated by 5-byte headers). Identical between two baseline runs on all 27, so this follows the distribution, not run-to-run variance. Cause in Gradle **not checked**; fastutil (8.5.2) and Guava (33.7.2) are the same in both distributions. |
| `KT-STATE` | `last-build.bin` of 5 tasks: an 18-byte serialized timestamp, the time each build ran. Differs on the same 5 tasks between two baseline runs too. Compiled classes are identical. |
| `GRADLE-LIBS` | The installation beacon and the generated `gradle-api` jar, on `buildSrc` classpaths only. Verified by path. |
| `VERSION-STRING` | `buildSrc`'s 8 generated adapter sources. Verified with `diff`: one line per file, "Precompiled Groovy script plugins built by Gradle …". |
| `UPSTREAM` | `buildSrc` only: the 8 adapter classes, `build/classes/java/main` on the Groovy compile classpaths, `previous-compilation-data.bin` of `:compileJava`, and `buildSrc.jar`. Verified with `javap -c -p -v`: each class differs only in the version string constant. `buildSrc.jar` checked with `zipfile`: same 104 entries in the same order; only the 8 adapter classes have a different CRC. |

## Task graph

No differences: same 741 tasks, same types, same `dependsOn` edges, same execution order, same outcomes (510 executed, 23 up-to-date, 133 no-source, 75 skipped). `buildSrc`: same 9 tasks, all executed.

## Differences, root build

Each row is one kind of difference; the count is the number of tasks showing it.

| Task type | Difference | Tasks | Reason |
|---|---|---|---|
| `JavaCompile` | output `previous-compilation-data.bin` | 27 | `COMPILE-ORDER` |
| `KotlinCompile`, `KaptGenerateStubsTask` | output `last-build.bin` | 5 | `KT-STATE` |

Union of the rows: 32 tasks. No root-build task has a Gradle distribution file on a compared classpath, so `GRADLE-LIBS` does not appear here.

The dump script could not read `groovyClasspath` on 53 `GroovyCompile` tasks ("Cannot infer Groovy class path because no Groovy Jar was found on class path"). The error is the same on both sides, so on those tasks that property was not compared.

## Differences, `buildSrc`

4 of the 9 tasks are identical (`:classes`, `:extractPluginRequests`, `:pluginDescriptors`, `:processResources`).

| Task | Difference | Reason |
|---|---|---|
| `:compileJava`, `:compileGroovy`, `:compileGroovyPlugins` | input `classpath` / `astTransformationClasspath`: beacon, `gradle-api` | `GRADLE-LIBS` |
| `:generatePluginAdapters` | 8 generated adapter sources, one line each | `VERSION-STRING` |
| `:compileJava` | the 8 adapter sources as input, their 8 classes as output, `previous-compilation-data.bin` | `UPSTREAM` |
| `:compileGroovy`, `:compileGroovyPlugins` | input `build/classes/java/main` (the 8 adapter classes) | `UPSTREAM` |
| `:jar` | input: those 8 classes; output `buildSrc.jar` | `UPSTREAM` |
