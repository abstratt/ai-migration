# Task graph and task input/output differences: gradle-lint-plugin, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `5f78b4d` ("Upgrade Baseline Gradle") | migration branch tip `ba0f413` (`gradle-10-migration/20260619-1749-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `10.0.0-20261126124457+0000` (built from the Provider API migration branch, revision `018f16a2641`) |
| JVM | Temurin 21.0.11 | Temurin 21.0.11 |
| Tasks in graph | 19 | 19 |
| Build result | passed | passed |

Both builds ran `clean assemble --no-build-cache --no-configuration-cache --no-scan -Prelease.version=0.0.0-compare` with `skip-kotlin-metadata-check.init.gradle` and `task-dump.init.gradle`; the two JSON dumps were then compared.

**Read this first**

- Input property values are compared by **eager-API semantics**. Where a lazy property replaced an eager one, the dump reads the value through the eager accessor generated for that property (`org.gradle.internal.classpath.generated.<Type>_Adapter.access_get_<originalAccessor>`, or the `$$BridgeFor$$` class of a custom adapter). That is what code compiled against an earlier Gradle gets when it calls the old getter. Without that, an unset `Property<Boolean>` that replaced `boolean isX()` reads as `null` where the old getter, and the adapter, return `false`. In the Provider API branch build, 88 input values across 7 tasks were read that way; the baseline build has no such accessors and is read as before.
- The migration changed **no build logic** in this project (only the wrapper files, plus the generated notes and report). Every difference below comes from the Gradle distribution or from the comparison setup.
- Each side was run with its distribution's `bin/gradle` directly, not through the wrapper.
- Each task's inputs were read right before it ran, and its outputs right after it finished.
- The Provider API branch build identifies itself as 10.0.0, the baseline build as 9.9.2. The two differ by the Provider API branch and also by whatever mainline changed between 9.9.2 and the branch's base. This report does not separate the two. Both embed Kotlin 2.4.21.
- 12 of the 19 tasks differ; all of them are covered by the rows below. The other 7 have no differences: `:assemble`, `:checkKotlinGradlePluginConfigurationErrors`, `:classes`, `:clean`, `:createPropertiesFileForJar`, `:pluginDescriptors`, `:processResources`.

## Summary

| Area | Result |
|---|---|
| Task graph | Same 19 tasks, same types, same dependency edges, same planned order |
| Task outcomes | Same on every task |
| Compiled classes | Identical (`build/classes` trees are byte-identical) |
| Jars | Same entries in the same order; only `META-INF/MANIFEST.MF` and `META-INF/gradle-lint-plugin.properties` differ (`BUILD-METADATA`, `GIT-REV`) |
| Task inputs | Two task-API differences (`API-ADDED`, `TOSTRING`), plus distribution jars (`GRADLE-LIBS`). No input value differs once read through the eager accessors. |

## Reason mnemonics

| Mnemonic | Kind | Meaning | Basis |
|---|---|---|---|
| `API-ADDED` | Task API | The task type declares an input property that the baseline build does not. | Observed: the property exists only in the Provider API branch build dump. |
| `GRADLE-LIBS` | Environment | Files of the Gradle distribution itself: the installation beacon and the generated `gradle-api` / `gradle-test-kit` jars. | Verified by path. Expected whenever two distributions are compared. |
| `DERIVED-CP` | Environment | Kotlin classpath snapshots computed from the compile classpath; they differ because the classpath differs (`GRADLE-LIBS`). | Verified by path. |
| `KT-STATE` | Outputs | Kotlin compiler bookkeeping files (`last-build.bin`, shrunk classpath snapshot). Not a build product. | Verified by path. |
| `BUILD-METADATA` | Outputs | Generated manifest or properties file embeds the build date and the Gradle version. | Verified with `diff` in this run: only `Build-Date`, `Build-Date-UTC` and `Gradle-Version` differ, apart from `GIT-REV`. |
| `GIT-REV` | Comparison setup | The two builds ran from different commits and the build records the commit hash (`Change`, `Full-Change`). | Verified with `diff`. |
| `UPSTREAM` | Propagation | The file differs only because it contains the output of another task that already differs. | Verified in this run for the three jars, entry by entry: same entry names and order (7,339, 156 and 28 entries); only `META-INF/MANIFEST.MF` and `META-INF/gradle-lint-plugin.properties` differ. |
| `TOSTRING` | Tool noise | The value is an object without a stable string form; only its `toString()` text changed. | Tool limitation. Says nothing about the object's content; the individual `options.*` inputs of the same task are identical. |

## Task graph

No differences: same 19 tasks, same types, same `dependsOn` edges, same execution order, same outcomes (`:compileJava` no-source, `:checkKotlinGradlePluginConfigurationErrors` skipped, the rest executed).

## Per-task differences

| Task | Type | Difference | Reason |
|---|---|---|---|
| `:dependencyReportCompileClasspath`, `:dependencyReportRuntimeClasspath`, `:dependencyReportTestCompileClasspath`, `:dependencyReportTestRuntimeClasspath` | `DependencyReportTask` | input `selectedConfiguration = null` only in the Provider API branch build | `API-ADDED` |
| `:javadoc` | `Javadoc` | input `options`: `StandardJavadocDocletOptions@<id>` → `task ':javadoc' property 'options'` | `TOSTRING` |
| `:compileGroovy` | `GroovyCompile` | inputs `classpath` and `astTransformationClasspath`: beacon, `gradle-api`, `gradle-test-kit` | `GRADLE-LIBS` |
| `:compileJava`, `:javadoc` | `JavaCompile`, `Javadoc` | input `classpath`: the same three files | `GRADLE-LIBS` |
| `:compileKotlin` | `KotlinCompile` | input `classpathSnapshotProperties.classpathSnapshot`: 3 removed, 3 added (the snapshots of those three files, named by Gradle version), 13 content-changed | `DERIVED-CP` |
| `:compileKotlin` | `KotlinCompile` | outputs `shrunk-classpath-snapshot.bin`, `last-build.bin` | `KT-STATE` |
| `:writeManifestProperties` | Nebula info task | input `manifest`: `Change`, `Full-Change`; output `gradle-lint-plugin.properties` | `GIT-REV`, `BUILD-METADATA` |
| `:javadocJar`, `:shadowJar`, `:sourcesJar` | `Jar`, `ShadowJar` | output jar file: its `MANIFEST.MF` (written by the task while it runs) and `gradle-lint-plugin.properties` | `BUILD-METADATA`, `GIT-REV`, `UPSTREAM` |

## Changes from the previous version of this report

- Rerun on a newer build of the Provider API branch: `10.0.0-20261126124457+0000`, revision `018f16a2641`, instead of `9.9.0-20261124151743+0000`, revision `8779a723`. The baseline build is unchanged.
- Same 12 differing tasks, with the same kinds of difference.
- Inputs are now read right before each task runs and outputs right after it finishes, instead of both after the build. As a result, the jar tasks' temporary `MANIFEST.MF` no longer shows as a differing input (it does not exist yet when the task starts); the jars still differ in it.
- The embedded Kotlin jars (`kotlin-stdlib`, `kotlin-reflect`) no longer differ: both distributions now embed 2.4.21. They are gone from `GRADLE-LIBS`, and `:compileKotlin`'s classpath snapshot has 3 removed / 3 added files instead of 5 / 5.
- Corrections to the previous version: input values were read through the adapters on 7 tasks, not 8; `:clean` executed, it was not up-to-date.

## Files

In `out/task-compare-g992/gradle-lint-plugin/`:

- `dump-before.json`, `dump-after.json`: the two dumps
- `comparison.txt`, `comparison-verbose.txt`: `compare_dumps.py` output
- `before.log`, `after.log`: build logs
- `run-8779a723/`: the previous run (dumps, logs, comparison, report), against revision `8779a723`
- `run-018f16a-read-after-build/`: this run's distributions with every property read after the build, for comparison
