# Task graph and task input/output differences: spring-framework, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `2e5286d43` ("Upgrade Baseline Gradle") | migration branch tip `49f7a8a1d` (`gradle-10-migration/20260612-1501-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `10.0.0-20261126124457+0000` (built from the Provider API migration branch, revision `018f16a2641`) |
| JVM | Temurin 25.0.3 | Temurin 25.0.3 |
| Tasks in graph | 197 (root), 16 (`buildSrc`) | 190 (root), 16 (`buildSrc`) |
| Build result | passed | passed |

The migration removed the `spring-aspects` module from the build (7 tasks, its jar, 33 classes, and two documentation snippets that need it), because the AspectJ plugin it uses did not work with the Provider API distribution the migration targeted. Apart from that, no root-build input value or build product differs because of the distribution. In `buildSrc`, one eager getter returns a different value: `Test.defaultCharacterEncoding` `UTF-8` → `null` (`EAGER-DEFAULT`).

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache -I task-dump.init.gradle`, each with its distribution's `bin/gradle`. No workaround was needed. `buildSrc/build` was deleted on both sides first, since `clean` does not reach `buildSrc`. The project sets `org.gradle.parallel=true`. `buildSrc` is built with `build`, so its tests and Checkstyle run too.

## Summary

| Area | Result |
|---|---|
| Task graph | Root: the 7 `:spring-aspects` tasks are removed (`WORKAROUND`); the other 190 tasks are the same, with the same types. `:framework-docs:compileJava` and `:compileKotlin` lose their dependencies on `:spring-aspects`, and 5 compile tasks move earlier in the planned order (`WORKAROUND`). `buildSrc`: same 16 tasks, same edges, same order |
| Task outcomes | Same on every common task (root: 128 executed, 32 up-to-date, 14 no-source, 16 skipped; `buildSrc`: 13 executed, 3 no-source) |
| Differing tasks | 21 of 190 (root), 10 of 16 (`buildSrc`); root: 7 removed, none added |
| Build code changed by the migration | 6 files (+16/−62), two of them deleted sources; see "Migrated build logic" |
| Task inputs | Root: no value differs. `buildSrc`: `Test.defaultCharacterEncoding` (`EAGER-DEFAULT`); `Test.testFrameworkProperty` is named `testFramework` (`API-RENAME`); `PluginUnderTestMetadata` no longer has the `paths` input (`API-DECLARATION`). 417 values in 79 root tasks and 88 in 8 `buildSrc` tasks were read through the eager-getter adapters |
| Compiled classes | Root: 8,218 class files in both builds; all identical except `ReactorNettyTcpClient.class` (`GEN-NAME`). The baseline build also has the 33 `spring-aspects` classes and 2 `ApplicationConfiguration` classes in `framework-docs` (`WORKAROUND`). `buildSrc`: 3 classes compile to different bytecode from unchanged source (`API-RECOMPILE`) |
| Jars | Root: 26 jars in both builds; all identical except `spring-messaging`, which differs only in `ReactorNettyTcpClient.class` (`UPSTREAM`); the baseline build also has the `spring-aspects` jar. `buildSrc.jar` differs (`UPSTREAM`) |
| Other outputs | Kotlin `last-build.bin` of 12 tasks (`KT-STATE`) and the incremental-compilation caches of `:framework-docs:compileKotlin` (`WORKAROUND`); `previous-compilation-data.bin` of 5 root tasks (`COMPILE-STATE`); in `buildSrc`, test results (`RUN-VARIANCE`), Checkstyle reports and the plugin-under-test metadata file (`GRADLE-VERSION`, `CHECKOUT-PATH`) |

## Migrated build logic

| Edit | Task | In the `assemble` graph? | Result |
|---|---|---|---|
| `include "spring-aspects"` commented out (`settings.gradle`), because the `io.freefair.aspectj` plugin's `AspectjCompile` was incompatible with the targeted Provider API distribution's `AbstractCompile.getClasspath()` | the 7 `:spring-aspects` tasks | yes | The tasks, the jar and its 33 classes are absent from the Provider API branch build. Whether the plugin works with this branch build was **not checked**. |
| `implementation(project(":spring-aspects"))` commented out (`framework-docs.gradle`); the snippet `ApplicationConfiguration` (`@EnableSpringConfigured`) deleted in Java and Kotlin | `:framework-docs:compileJava`, `:compileKotlin`, `:jar` | yes | Classpaths lose the 2 `spring-aspects` class directories; the 2 `ApplicationConfiguration` classes are absent from the output and the jar input. The `ApplicationConfiguration.xml` resource of the same snippet stays. |
| `springAspectsOutput` and `classpath += files(springAspectsOutput)` in a `doFirst` commented out (`framework-api.gradle`) | `:framework-api:javadoc` | **no** | Not exercised. |
| `jvmArgs += [...]` → `.addAll(...)` (`spring-core.gradle`) | `:spring-core:test` | **no** | Not exercised. |

## Basis

Mnemonics are defined in the [index](README.md#reason-mnemonics).

| Mnemonic | Basis |
|---|---|
| `WORKAROUND` | The `spring-aspects` exclusion above. Verified from the dumps: the 7 removed tasks are exactly the `:spring-aspects` ones; the only changed `dependsOn` edges are the two from `:framework-docs` to `:spring-aspects`; the removed classpath entries are `spring-aspects/build/classes/{aspectj,java}/main`; the removed outputs are the 2 `ApplicationConfiguration.class` files. The planned order changes because `:spring-aspects:compileJava` depends on `:spring-orm:compileJava`, which the baseline build schedules before `:spring-core-test`, `:spring-messaging` and `:spring-jms` compile tasks; without it, those 5 tasks come first. `framework-docs/build/classes/kotlin/main` on `:framework-docs:compileJava`'s classpath and 65 Kotlin incremental-compilation cache files and the shrunk classpath snapshot of `:framework-docs:compileKotlin` differ because the Kotlin snippet was deleted and `spring-aspects` left the classpath. |
| `EAGER-DEFAULT` | `buildSrc` `:test`, `defaultCharacterEncoding` read through the adapter: `UTF-8` → `null`. Verified in the source: in 9.9.2, `JvmOptions.getDefaultCharacterEncoding()` returns the stored `file.encoding`, which defaults to the JVM's default charset; on the branch, `DefaultJavaForkOptions.getDefaultCharacterEncoding()` is an unset `Property<String>`. Effect on the test JVM's encoding **not checked**; the tests passed on both sides. |
| `API-RENAME` | `buildSrc` `:test`: the nested input `testFrameworkProperty` (9.9.2, `Test.getTestFrameworkProperty()`) is `testFramework` on the branch (`Test.getTestFramework()`, `@ReplacesEagerProperty`, with a `@BytecodeUpgrade` bridge for the old name). Verified in the source of both versions. Same implementation types and the same 4 option values on both sides. |
| `API-DECLARATION` | `buildSrc` `:pluginUnderTestMetadata`: in 9.9.2 the task has an `@Input` `getPaths()` (the absolute classpath paths) and a `@Classpath` `pluginClasspath`; on the branch (commit "Migrate PluginUnderTestMetadata task to provider API"), `getPaths()` is gone and `pluginClasspath` is `@PathSensitive(ABSOLUTE)`. Verified in the source of both versions and from the dumps (input `paths` only in the baseline build; `pluginClasspath` normalizer "runtime classpath" → "absolute path"). The output file has the same content apart from the checkout path. |
| `API-RECOMPILE` | `buildSrc`: `SpringFrameworkExtension`, `RuntimeHintsAgentPlugin`, `MultiReleaseJarValidateTask`, from unchanged source. Verified with `javap -c -p -v`: calls to `Test.getJvmArgumentProviders()`, `CompileOptions.getCompilerArgumentProviders()` and `JavaExec.getArgumentProviders()` return `ListProperty` instead of `List`, and `add` is `ListProperty.add(Object): void` instead of `List.add(Object): boolean`. |
| `GEN-NAME` | `ReactorNettyTcpClient.class` in `spring-messaging`. Verified with `javap -c -p -v`: the only difference is the name of a synthetic local variable of type `Integer`, `$1703371824` vs `$1336234810`. Differs between two baseline runs too. `spring-messaging` jar checked with `zipfile`: same 367 entries in the same order; only that class has a different CRC. |
| `KT-STATE` | `last-build.bin` of 12 `KotlinCompile` tasks. Differs on the same 12 tasks between two baseline runs. |
| `COMPILE-STATE` | Root: `previous-compilation-data.bin` of `:framework-docs`, `:spring-messaging`, `:spring-test`, `:spring-web` and `:spring-webmvc` `compileJava`. Differs between two baseline runs too, on these 5 tasks and 15 more, so it is run-to-run variance. `buildSrc` `:compileJava` and `:compileTestJava`: identical between two baseline runs; their classpaths differ (`GRADLE-LIBS`), and so do the classes of `:compileJava` (`API-RECOMPILE`). Content not inspected. |
| `RUN-VARIANCE` | `buildSrc` `:test`: the JUnit XML report, the HTML reports and `results-generic.bin` record the timestamp and duration of each test. Verified with `diff` on the XML report. Differ between two baseline runs too. |
| `GRADLE-VERSION` | `buildSrc` Checkstyle HTML reports `main.html`, `test.html`: "Generated by Gradle 9.9.2" vs "Generated by Gradle 10.0.0-…". Verified with `diff`; nothing else differs once the checkout path is normalized. |
| `CHECKOUT-PATH` | `buildSrc`: the Checkstyle XML reports (`<file name="…">`) and `plugin-under-test-metadata.properties` (`implementation-classpath`) name the `before` or `after` checkout. Verified with `diff`: identical once the checkout directory name is normalized. |
| `GRADLE-LIBS` | `buildSrc`: the installation beacon and the generated `gradle-api` and `gradle-test-kit` jars on the classpaths of the compile, Checkstyle, `validatePlugins` and `test` tasks, and the `gradleHome` input of `:test`. Verified by path. |
| `UPSTREAM` | Root: `:spring-messaging:jar` (input `ReactorNettyTcpClient.class`, output jar); `spring-messaging/build/classes/java/main` on the classpaths of `:spring-jms`, `:spring-websocket` and `:framework-docs` `compileJava`. `buildSrc`: `build/classes/java/main` and `build/pluginUnderTestMetadata` on the classpaths and plugin classpaths of later tasks, `:jar` and `buildSrc.jar`. Verified by path. |

## Task graph

Root: the 7 `:spring-aspects` tasks (`assemble`, `classes`, `clean`, `compileAspectj`, `compileJava`, `jar`, `processResources`) are only in the baseline build. The other 190 tasks are the same, with the same types and outcomes. Their `dependsOn` edges are the same except the two from `:framework-docs` to `:spring-aspects`. In the planned order, 5 tasks (`:spring-core-test:compileJava`, `:spring-messaging:checkKotlinGradlePluginConfigurationErrors`, `:compileKotlin`, `:compileJava`, `:spring-jms:compileJava`) come before `:spring-orm:compileJava` instead of after it (`WORKAROUND`).

`buildSrc`: no differences.

## Differences, root build

Each row is one kind of difference; the count is the number of tasks showing it.

| Task type | Difference | Tasks | Reason |
|---|---|---|---|
| (7 tasks) | `:spring-aspects` tasks only in the baseline build | removed | `WORKAROUND` |
| `JavaCompile`, `KotlinCompile` | `:framework-docs`: `dependsOn` and classpath lose `:spring-aspects`; source and class `ApplicationConfiguration` removed; Kotlin incremental caches | 2 | `WORKAROUND` |
| `Jar` | `:framework-docs:jar`: input loses the 2 `ApplicationConfiguration` classes | 1 | `WORKAROUND` |
| `JavaCompile` | `:spring-messaging`: output `ReactorNettyTcpClient.class` | 1 | `GEN-NAME` |
| `Jar` | `:spring-messaging:jar`: input class, output jar | 1 | `UPSTREAM` |
| `JavaCompile` | input classpath `spring-messaging/build/classes/java/main` | 3 | `UPSTREAM` |
| `KotlinCompile` | output `last-build.bin` | 12 | `KT-STATE` |
| `JavaCompile` | output `previous-compilation-data.bin` | 5 | `COMPILE-STATE` |

Union of the rows: 21 tasks, plus 7 removed.

## Differences, `buildSrc`

6 of the 16 tasks are identical (`:check`, `:classes`, `:pluginDescriptors`, `:processResources`, `:processTestResources`, `:testClasses`).

| Task | Difference | Reason |
|---|---|---|
| `:test` | input `defaultCharacterEncoding`: `UTF-8` → `null` (read through the adapter) | `EAGER-DEFAULT` |
| `:test` | nested input `testFrameworkProperty` → `testFramework` (same values) | `API-RENAME` |
| `:test` | outputs: JUnit XML, HTML reports, binary results | `RUN-VARIANCE` |
| `:pluginUnderTestMetadata` | input `paths` only in the baseline build; `pluginClasspath` normalizer | `API-DECLARATION` |
| `:pluginUnderTestMetadata` | output `plugin-under-test-metadata.properties` | `CHECKOUT-PATH` |
| `:compileJava` | output: `SpringFrameworkExtension`, `RuntimeHintsAgentPlugin`, `MultiReleaseJarValidateTask` | `API-RECOMPILE` |
| `:compileJava`, `:compileTestJava` | output `previous-compilation-data.bin` | `COMPILE-STATE` |
| `:checkstyleMain`, `:checkstyleTest` | output HTML reports | `GRADLE-VERSION` |
| `:checkstyleMain`, `:checkstyleTest` | output XML reports | `CHECKOUT-PATH` |
| `:compileJava`, `:compileGroovy`, `:compileTestJava`, `:compileTestGroovy`, `:checkstyleMain`, `:checkstyleTest`, `:validatePlugins`, `:test` | input classpaths: beacon, `gradle-api`, `gradle-test-kit`; `:test` input `gradleHome` | `GRADLE-LIBS` |
| `:compileGroovy`, `:compileTestJava`, `:compileTestGroovy`, `:checkstyleMain`, `:checkstyleTest`, `:validatePlugins`, `:pluginUnderTestMetadata`, `:test`, `:jar` | `build/classes/java/main`, `build/pluginUnderTestMetadata` as input; output `buildSrc.jar` | `UPSTREAM` |
