# Task graph and task input/output differences: hibernate-orm, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `711326e5f` ("more updates to the Guide to Hibern8"; the project was already on the baseline Gradle version, so the branch has no "Upgrade Baseline Gradle" commit) | migration branch tip `9d977cf2f` (`gradle-10-migration/20260615-2349-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `10.0.0-20261126124457+0000` (built from the Provider API migration branch, revision `018f16a2641`) |
| JVM | Temurin 25.0.3 | Temurin 25.0.3 |
| Tasks in graph | 307 (root), 11 (`local-build-plugins`) | 307 (root), 11 (`local-build-plugins`) |
| Build result | passed | passed |

No input value differs because of the distribution, and no build product differs because of it. The one build-product difference, an empty `<type>` for `hibernate-reveng` in the Maven plugin descriptor, comes from a race between parallel tasks in the project, and a second baseline run reproduces it (`TASK-RACE`).

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache -I task-dump.init.gradle`, each with its distribution's `bin/gradle`. No workaround was needed. The project sets `org.gradle.parallel=true` and puts build outputs under `target/` instead of `build/`. Both worktrees were fresh checkouts, so the included build `local-build-plugins` (whose outputs `clean` does not reach) executed on both sides.

## Summary

| Area | Result |
|---|---|
| Task graph | Same 307 tasks (root) and 11 (`local-build-plugins`), same types, same dependency edges, same planned order |
| Task outcomes | Same on every task (282 executed, 13 up-to-date, 11 no-source, 1 skipped in the root build; all 11 executed in `local-build-plugins`) |
| Differing tasks | 13 of 307 (root), 7 of 11 (`local-build-plugins`); none added or removed |
| Build code changed by the migration | 4 files (+12/−11), 2 of them in `local-build-plugins`; see "Migrated build logic" |
| Task inputs | No value differs because of the distribution. One value differs because of `TASK-RACE`. 1,685 values in 149 root tasks and 33 in 3 `local-build-plugins` tasks were read through the eager-getter adapters |
| Compiled classes | All 10,758 root-build class files identical. In `local-build-plugins`: `JavaModulePlugin.class` (`MIGRATED`), 7 generated adapter classes (`UPSTREAM`), 4 precompiled script closures (2 `MIGRATED`, 2 `DSL-TRANSFORM`) |
| Jars | 71 of the 72 root-build jars identical. `hibernate-maven-plugin-8.1.0-SNAPSHOT.jar` contains the differing `plugin.xml` (`UPSTREAM`). `local-build-plugins-1.0.0-SNAPSHOT.jar` differs (`UPSTREAM`) |
| Other outputs | Maven plugin descriptor `plugin.xml` (`TASK-RACE`); 29 ANTLR-generated parser sources (`CHECKOUT-PATH`); `previous-compilation-data.bin` of 4 `JavaCompile` tasks (`COMPILE-STATE`) |

## Migrated build logic

| Edit | Task | In the `assemble` graph? | Result |
|---|---|---|---|
| `options.compilerArgs += [...]` → `.addAll(...)` (`local.java-module`) | all `JavaCompile` (24) | yes | `options.compilerArgs` identical on every task, e.g. `:hibernate-core:compileJava` `[--limit-modules, java.base,…, -Aorg.jboss.logging.tools.addGeneratedAnnotation=false]` on both sides. |
| `new ArrayList<>(forOptions.getJvmArgs())` → `forOptions.getJvmArgs().get()` (`JavaModulePlugin`) | all `JavaCompile` (24) | yes | `options.forkOptions.jvmArgs` identical, e.g. `:hibernate-core:compileJava` `[-Dlog4j2.disableJmx=true, -Xmx2g, …, -Dfile.encoding=UTF-8]`. |
| `options.forkOptions.jvmArgs += [...]` → `.addAll(...)` under `APT_DEBUG=true` (`local.java-module`) | `JavaCompile` | **no** | Only applies with `-DAPT_DEBUG=true`; not exercised. |
| `test.jvmArgs += [...]` → `.addAll(...)` (2 sites); `test.systemProperties += providers.systemPropertiesPrefixedBy("hibernate.").get()` → `.putAll(provider)` (`local.java-module`) | `Test` | **no** | Not exercised. |
| `options.compilerArgs += [...]` → `.addAll(...)` on `compileTestJava` (`hibernate-core.gradle`, `hibernate-processor.gradle`) | `compileTestJava` | **no** | Not exercised. |

## Basis

Mnemonics are defined in the [index](README.md#reason-mnemonics).

| Mnemonic | Basis |
|---|---|
| `TASK-RACE` | `:hibernate-maven-plugin:generateMavenPluginDescriptor` (plugin `org.gradlex.maven-plugin-development` 1.0.3) writes one `<dependency>` per `runtimeClasspath` artifact, with `<type>` set to the file's extension, but only if the file exists (`FileUtils.getExtension` returns empty when `!file.isFile()`, verified with `javap -c`). For the project dependency `hibernate-reveng` that file is its jar, and the descriptor task does not depend on `:hibernate-reveng:jar` (`dependsOn` in the dumps: only `compileJava`, `classes`, `generateMavenPluginHelpMojoSources`). With parallel execution, in the first baseline run the jar task finished first (`<type>jar</type>`); in the Provider API branch build and in a second baseline run, the descriptor task ran first (`<type></type>`), per the task order in the build logs. `plugin.xml` verified with `diff`: that one line. The second baseline run's `plugin.xml` and `hibernate-maven-plugin` jar have the same hashes as the Provider API branch build's. |
| `CHECKOUT-PATH` | 29 ANTLR-generated sources of the 5 `SplitGrammarGenerationTask` tasks of `:hibernate-core`. Verified with `diff`: each file differs only in line 1, `// Generated from <absolute path of the .g4 file> by ANTLR 4.13.2`, which names the `before` or `after` checkout. The classes compiled from them are identical. |
| `COMPILE-STATE` | `previous-compilation-data.bin` of `:hibernate-ant`, `:hibernate-core`, `:hibernate-gradle-plugin` and `:hibernate-processor` `compileJava`. Differs between two baseline runs too, on these 4 tasks and 14 more, so it is run-to-run variance. Compiled classes identical. |
| `GRADLE-LIBS` | The installation beacon and the generated `gradle-api` jar on the classpaths of `:hibernate-gradle-plugin` `compileJava`, `javadoc` and `jar`, and of the `local-build-plugins` compile tasks. Verified by path. The classes compiled against them in `:hibernate-gradle-plugin` are identical. |
| `MIGRATED` | `local-build-plugins`: input sources `local.java-module.gradle` and `JavaModulePlugin.java` (also the input of `:spotlessJava`). Verified with `javap -c -p -v`: `JavaModulePlugin.class` calls `ForkOptions.getJvmArgs()` returning `ListProperty`, then `get()` (was `List`); `precompiled_LocalJavaModule$_run_closure4` calls `addAll` (was `plus`), `_run_closure6` calls `addAll` and `putAll` (was `plus`). |
| `DSL-TRANSFORM` | `local-build-plugins`: `precompiled_LocalCodeQuality$_run_closure11$_closure24` (`options.annotationProcessorPath += files(...)` in a `doFirst` for the NullAway source set) and `_run_closure13` (`bundledSignatures +=`, `signaturesFiles +=`, `suppressAnnotations +=` on `forbiddenApisMain`), both in unedited source. Verified with `javap -v`: each has 3 `forCompoundAssignment` and 3 `toAssignmentResult` call sites on the branch, and none in the baseline. Neither `compileNullawayJava` nor `forbiddenApisMain` is in the `assemble` graph, so their runtime effect was **not checked**. |
| `VERSION-STRING` | `local-build-plugins`: the 7 generated adapter sources. Verified with `diff` and `javap`: the only difference is the message "Precompiled Groovy script plugins built by Gradle …". |
| `UPSTREAM` | `local-build-plugins`: the 7 adapter classes, the classes directories on the Groovy compile classpaths, `previous-compilation-data.bin` of `:compileJava`, `:jar` and its jar. Root: `:hibernate-maven-plugin:jar` (input `plugin.xml`, output jar). Verified by path. |

## Task graph

No differences: same 307 root tasks and 11 `local-build-plugins` tasks, same types, same `dependsOn` edges, same planned order, same outcomes.

## Differences, root build

Each row is one kind of difference; the count is the number of tasks showing it.

| Task type | Difference | Tasks | Reason |
|---|---|---|---|
| `GenerateMavenPluginDescriptorTask` | input `runtimeDependencies.$0.type` (`hibernate-reveng`): `jar` → `null`; output `plugin.xml` | 1 | `TASK-RACE` |
| `Jar` | input `plugin.xml`, output `hibernate-maven-plugin-8.1.0-SNAPSHOT.jar` | 1 | `UPSTREAM` |
| `SplitGrammarGenerationTask` | output: generated parser sources | 5 | `CHECKOUT-PATH` |
| `JavaCompile` | output `previous-compilation-data.bin` | 4 | `COMPILE-STATE` |
| `JavaCompile`, `Javadoc`, `Jar` | input `classpath`: beacon, `gradle-api` (`:hibernate-gradle-plugin`) | 3 | `GRADLE-LIBS` |

Union of the rows: 13 tasks.

## Differences, `local-build-plugins`

4 of the 11 tasks are identical (`:classes`, `:pluginDescriptors`, `:processResources`, `:spotlessJavaApply`).

| Task | Difference | Reason |
|---|---|---|
| `:extractPluginRequests`, `:compileGroovyPlugins` | input script `local.java-module.gradle` | `MIGRATED` |
| `:compileGroovyPlugins` | output: `precompiled_LocalJavaModule$_run_closure4`, `_run_closure6` | `MIGRATED` |
| `:compileGroovyPlugins` | output: `precompiled_LocalCodeQuality$_run_closure11$_closure24`, `_run_closure13` | `DSL-TRANSFORM` |
| `:compileJava` | input `JavaModulePlugin.java`; output `JavaModulePlugin.class` | `MIGRATED` |
| `:generatePluginAdapters` | 7 generated adapter sources | `VERSION-STRING` |
| `:compileJava` | the 7 adapter sources as input, their 7 classes as output, `previous-compilation-data.bin` | `UPSTREAM` |
| `:spotlessJava` | input `JavaModulePlugin.java` | `MIGRATED` |
| `:compileJava`, `:compileGroovy`, `:compileGroovyPlugins` | input `classpath` / `astTransformationClasspath`: beacon, `gradle-api` | `GRADLE-LIBS` (and `UPSTREAM` for `classes/java/main`) |
| `:jar` | input: the differing classes; output `local-build-plugins-1.0.0-SNAPSHOT.jar` | `UPSTREAM` |
