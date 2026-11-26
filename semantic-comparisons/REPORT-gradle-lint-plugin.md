# Task graph and task input/output differences: gradle-lint-plugin, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `5f78b4d` ("Upgrade Baseline Gradle") | migration branch tip `ba0f413` (`gradle-10-migration/20260619-1749-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `9.9.0-20261124151743+0000` (built from the Provider API migration branch, revision `8779a723`) |
| JVM | Temurin 21.0.11 | Temurin 21.0.11 |
| Tasks in graph | 19 | 19 |
| Build result | passed | passed |

Both builds ran `clean assemble --no-build-cache --no-configuration-cache --no-scan -Prelease.version=0.0.0-compare` with `skip-kotlin-metadata-check.init.gradle` and `task-dump.init.gradle`; the two JSON dumps were then compared.

**Read this first**

- Input property values are compared by **eager-API semantics**. Where a lazy property replaced an eager one, the dump reads the value through the eager accessor generated for that property (`org.gradle.internal.classpath.generated.<Type>_Adapter.access_get_<originalAccessor>`, or the `$$BridgeFor$$` class of a custom adapter). That is what code compiled against an earlier Gradle gets when it calls the old getter. Without that, an unset `Property<Boolean>` that replaced `boolean isX()` reads as `null` where the old getter, and the adapter, return `false`. In the Provider API branch build, 88 input values across 8 tasks were read that way; the baseline build has no such accessors and is read as before.
- The migration changed **no build logic** in this project (only the wrapper files, plus the generated notes and report). Every difference below comes from the Gradle distribution or from the comparison setup.
- Each side was run with its distribution's `bin/gradle` directly, not through the wrapper.
- The Provider API branch build identifies itself as 9.9.0, the baseline build as 9.9.2. The two differ by the Provider API branch and also by whatever mainline changed between the branch point and 9.9.2 (for example embedded Kotlin 2.4.20 vs 2.4.21). This report does not separate the two.
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
| `GRADLE-LIBS` | Environment | Files of the Gradle distribution itself: embedded Kotlin (2.4.21 vs 2.4.20), the installation beacon, and the generated `gradle-api` / `gradle-test-kit` jars. | Verified by path. Expected whenever two distributions are compared. |
| `DERIVED-CP` | Environment | Kotlin classpath snapshots computed from the compile classpath; they differ because the classpath differs (`GRADLE-LIBS`). | Verified by path. |
| `KT-STATE` | Outputs | Kotlin compiler bookkeeping files (`last-build.bin`, shrunk classpath snapshot). Not a build product. | Verified by path. |
| `BUILD-METADATA` | Outputs | Generated manifest or properties file embeds the build date and the Gradle version. | Verified with `diff`: only `Build-Date`, `Build-Date-UTC` and `Gradle-Version` differ, apart from `GIT-REV`. |
| `GIT-REV` | Comparison setup | The two builds ran from different commits and the build records the commit hash (`Change`, `Full-Change`). | Verified with `diff`. |
| `UPSTREAM` | Propagation | The file differs only because it contains the output of another task that already differs. | Verified for the three jars: same entry names and order (7339, 28 and 156 entries); only the manifest and the generated properties file differ. |
| `TOSTRING` | Tool noise | The value is an object without a stable string form; only its `toString()` text changed. | Tool limitation. Says nothing about the object's content; the individual `options.*` inputs of the same task are identical. |

## Task graph

No differences: same 19 tasks, same types, same `dependsOn` edges, same execution order, same outcomes (`:clean` up-to-date, `:compileJava` no-source, `:checkKotlinGradlePluginConfigurationErrors` skipped, the rest executed).

## Per-task differences

| Task | Type | Difference | Reason |
|---|---|---|---|
| `:dependencyReportCompileClasspath`, `:dependencyReportRuntimeClasspath`, `:dependencyReportTestCompileClasspath`, `:dependencyReportTestRuntimeClasspath` | `DependencyReportTask` | input `selectedConfiguration = null` only in the Provider API branch build | `API-ADDED` |
| `:javadoc` | `Javadoc` | input `options`: `StandardJavadocDocletOptions@<id>` → `task ':javadoc' property 'options'` | `TOSTRING` |
| `:compileGroovy` | `GroovyCompile` | inputs `classpath` and `astTransformationClasspath`: Kotlin 2.4.21 → 2.4.20 jars, beacon, `gradle-api`, `gradle-test-kit` | `GRADLE-LIBS` |
| `:compileJava`, `:javadoc` | `JavaCompile`, `Javadoc` | input `classpath`: same seven entries as above | `GRADLE-LIBS` |
| `:compileKotlin` | `KotlinCompile` | input `classpathSnapshotProperties.classpathSnapshot`: 5 removed, 5 added, 11 content-changed | `DERIVED-CP` |
| `:compileKotlin` | `KotlinCompile` | outputs `shrunk-classpath-snapshot.bin`, `last-build.bin` | `KT-STATE` |
| `:writeManifestProperties` | Nebula info task | input `manifest`: `Change`, `Full-Change`; output `gradle-lint-plugin.properties` | `GIT-REV`, `BUILD-METADATA` |
| `:javadocJar`, `:shadowJar`, `:sourcesJar` | `Jar`, `ShadowJar` | input `MANIFEST.MF`; output jar file | `BUILD-METADATA`, `GIT-REV`, `UPSTREAM` |

## Changes from the previous version of this report

- `:clean` (`Delete`), input `followSymlinks`: `false` → `null`, previously tagged `VALUE-UNSET`, is gone. Read through `Delete_Adapter.access_get_isFollowSymlinks`, the Provider API branch build returns `false`, the same as the baseline build. `:clean` is now identical, and the `VALUE-UNSET` mnemonic no longer applies to this project.

## Files

- `dump-before.json`, `dump-after.json`: the two dumps
- `comparison.txt`, `comparison-verbose.txt`: `compare_dumps.py` output
- `before.log`, `after.log`: build logs
