# Task graph and task input/output differences: micronaut-core, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `c4fcf5622` ("chore: Bump version to 5.1.3-SNAPSHOT") | migration branch tip `f48ed2d53` (`gradle-10-migration/20260619-1844-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `10.0.0-20261126124457+0000` (built from the Provider API migration branch, revision `018f16a2641`) |
| JVM | Temurin 25.0.3 | Temurin 25.0.3 |
| Tasks in graph | 741 (root), 9 (`buildSrc`) | 741 (root), 9 (`buildSrc`) |
| Build result | passed | passed |

No input value differs, and no build product differs because of the Gradle distribution. The Java incremental-compilation state is written in a different order on 27 modules (`COMPILE-ORDER`).

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache -I task-dump.init.gradle`, each with its distribution's `bin/gradle`. No workaround was needed. `buildSrc/build` was deleted on both sides first, since `clean` does not reach `buildSrc`.

## Summary

| Area | Result |
|---|---|
| Task graph | Same 741 tasks (root) and 9 (`buildSrc`), same types, same dependency edges, same planned order |
| Task outcomes | Same on every task |
| Differing tasks | 84 of 741 (root), 5 of 9 (`buildSrc`); none added or removed |
| Build code changed by the migration | None (only the wrapper files, plus the generated notes and report) |
| Task inputs | No value differs. 4,610 values in 446 root tasks and 33 in 3 `buildSrc` tasks were read through the eager-getter adapters. One tool-noise difference that follows task type uniformly (`TOSTRING` on all 43 `Javadoc`) |
| Compiled classes | 4,790 of 4,791 root-build classes identical; the other one is `GEN-ORDER`. In `buildSrc`, the 8 generated adapter classes differ (`VERSION-STRING`) |
| Jars | Identical except `micronaut-http-server-netty` (only the `GEN-ORDER` class differs) and `buildSrc.jar` (only the 8 adapter classes differ) |
| Other outputs | `previous-compilation-data.bin` of 27 `JavaCompile` tasks (`COMPILE-ORDER`); Kotlin `last-build.bin` of 5 tasks (`KT-STATE`) |

## Basis

Mnemonics are defined in the [index](README.md#reason-mnemonics).

| Mnemonic | Basis |
|---|---|
| `GEN-ORDER` | The Micronaut annotation processor's generated class `$DefaultNettyEmbeddedServerFactory$Definition` lists two types in swapped order. Verified with `javap -c -p`: 2 changed lines, two adjacent `ldc` class constants; everything else identical. Two baseline runs differ in the same way in `micronaut-jackson-databind` (`$JsonMediaTypeCodec$Definition`, `$JsonStreamMediaTypeCodec$Definition`). |
| `COMPILE-ORDER` | `previous-compilation-data.bin` of 27 `JavaCompile` tasks holds count-prefixed sets of 32-bit values. Verified byte by byte on the 27 files. Of 176 differing regions, 150 are permutations of 4-byte words. 23 have equal byte multisets; these are sets at odd offsets in the stream, and the ones inspected by hand are permutations too. The other 3 are in `micronaut-http-server-netty` and `micronaut-jackson-databind`, whose classes differ (`GEN-ORDER`). Two baseline runs differ in this file on 1 task only (`micronaut-jackson-databind`, `GEN-ORDER`), so this is not run-to-run variance. Cause in Gradle **not checked**; fastutil (8.5.2) and Guava (33.7.2) are the same in both distributions. |
| `KT-STATE` | `last-build.bin` of 5 tasks; it records the time of the build. Differs on the same 5 tasks between two baseline runs too. Compiled classes are identical. |
| `UPSTREAM` | Verified: every such entry is the `micronaut-http-server-netty` jar or classes directory, or in `buildSrc` the adapter classes. Jars checked with `zipfile`: same entries in the same order (331 and 104); only the differing classes have a different CRC. |
| `TOSTRING` | `Javadoc` `options`. Says nothing about the object's content; the individual `options.*` inputs of the same tasks are identical. |
| `GRADLE-LIBS` | The installation beacon and the generated `gradle-api` jar, on `buildSrc` classpaths only. Verified by path. |
| `VERSION-STRING` | `buildSrc`'s 8 generated adapter sources. Verified with `diff`: one line per file, "Precompiled Groovy script plugins built by Gradle …". |

## Task graph

No differences: same 741 tasks, same types, same `dependsOn` edges, same execution order, same outcomes (510 executed, 23 up-to-date, 133 no-source, 75 skipped). `buildSrc`: same 9 tasks, all executed.

## Differences, root build

Each row is one kind of difference; the count is the number of tasks showing it. A task can appear in more than one row.

| Task type | Difference | Tasks | Reason |
|---|---|---|---|
| `Javadoc` | input `options`: `StandardJavadocDocletOptions@<id>` → `task '…' property 'options'` | 43 (all) | `TOSTRING` |
| `JavaCompile` | output `previous-compilation-data.bin` | 27 | `COMPILE-ORDER` |
| `JavaCompile` | output class `$DefaultNettyEmbeddedServerFactory$Definition` (`:micronaut-http-server-netty:compileJava`) | 1 | `GEN-ORDER` |
| `Jar` | input classes and output jar of `:micronaut-http-server-netty` | 1 | `UPSTREAM` |
| `JavaCompile`, `GroovyCompile`, `Javadoc` | inputs `classpath` / `astTransformationClasspath` contain that jar or classes directory (`benchmarks`, `micronaut-http-client-tck`, `micronaut-http-server-netty`, `test-suite-kotlin`, `test-suite-kotlin-ksp-all-open`) | 11 | `UPSTREAM` |
| `KotlinCompile`, `KaptGenerateStubsTask` | output `last-build.bin` | 5 | `KT-STATE` |

Union of the rows: 84 tasks. No root-build task has a Gradle distribution file on a compared classpath, so `GRADLE-LIBS` does not appear here.

The dump script could not read `groovyClasspath` on 53 `GroovyCompile` tasks ("Cannot infer Groovy class path because no Groovy Jar was found on class path"). The error is the same on both sides, so on those tasks that property was not compared.

## Differences, `buildSrc`

4 of the 9 tasks are identical (`:classes`, `:extractPluginRequests`, `:pluginDescriptors`, `:processResources`).

| Task | Difference | Reason |
|---|---|---|
| `:compileJava`, `:compileGroovy`, `:compileGroovyPlugins` | input `classpath` / `astTransformationClasspath`: beacon, `gradle-api` | `GRADLE-LIBS` |
| `:generatePluginAdapters` | 8 generated adapter sources, one line each | `VERSION-STRING` |
| `:compileJava` | the 8 adapter sources as input, their 8 classes as output, `previous-compilation-data.bin` | `UPSTREAM` |
| `:jar` | input: those 8 classes; output `buildSrc.jar` | `UPSTREAM` |
