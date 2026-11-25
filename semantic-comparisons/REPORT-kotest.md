# Task graph and task input/output differences: kotest, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `d285691bc` ("Upgrade Baseline Gradle") | migration branch tip `257cf363d` (`gradle-10-migration/20260618-0925-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release, via the wrapper) | `9.9.0-20261124151743+0000` (built from the Provider API migration branch, revision `8779a723`) |
| JVM | Temurin 21.0.11 | Temurin 21.0.11 |
| Tasks in graph | 4,046 (root build), 14 (`buildSrc`) | 4,046 (root build), 14 (`buildSrc`) |
| Build result | passed | passed |

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache` with `skip-kotlin-metadata-check.init.gradle` and `task-dump.init.gradle`; the JSON dumps were then compared. kotest has a `buildSrc` and no included builds, so there are two dumps per side.

**Read this first**

- **One real behaviour change was found, outside what `assemble` exercises: the published BOM is broken on the Provider API branch build.** `buildSrc` builds each BOM coordinate with a string template over `MavenPublication.groupId` / `artifactId` / `version`. Those are now `Property<String>`, the template still compiles, and it yields the literal text `property 'groupId':property 'artifactId':property 'version'`. The generated `kotest-bom` POM has 1 bogus dependency instead of 74. The migration did not touch this code. See "BOM coordinates".
- **Everything `assemble` produces is otherwise equivalent.** When the Provider API branch build is run at the same absolute path as the baseline build, all 780 `.klib` files, all 3 `.aar` files, 432 of 435 jars and 4,074 of 4,327 class files are byte-identical. Every file that is not identical is accounted for by one of three causes: source the migration edited, a workaround the migration branch carries, or the Gradle version string.
- The workaround `skip-kotlin-metadata-check.init.gradle` is applied to both builds. Without it both fail alike at `:kotest-framework:kotest-framework-plugin-gradle:compileKotlin` (`no-workaround/*.log`).
- The migration branch carries a second, one-sided workaround: `instrumentCode = false` in `kotest-intellij-plugin`. It makes `:kotest-intellij-plugin:instrumentCode` skip. This is the only task outcome that differs.
- The baseline worktree has one local edit: the wrapper points at 9.9.2 (`distributionUrl` and the official `distributionSha256Sum`).
- Comparing the two worktrees directly shows 3,173 differing output files. 2,750 of them differ only because Kotlin and Android tooling embed the absolute project path; the same files differ when the baseline is built twice at two paths. See "Control runs".

## Summary

| Area | Result |
|---|---|
| Task graph | Same 4,046 tasks, same types, same `dependsOn` edges, same execution order |
| Task outcomes | Same, except `:kotest-intellij-plugin:instrumentCode`: executed → skipped (migration branch workaround) |
| Compiled classes | 4,327 class files; 4,074 byte-identical. The 253 others: 35 in the Gradle plugin module the migration edited, 218 instrumented classes no longer produced |
| Kotlin libraries | 780 `.klib` files, all byte-identical at the same path |
| Jars and AARs | 432 of 435 jars and 3 of 3 AARs byte-identical at the same path |
| `buildSrc` | Not edited by the migration; 8 of 815 class files compile differently because the Gradle API they call changed |
| BOM (not part of `assemble`) | **Broken**: 74 dependency constraints → 1 bogus one |

## BOM coordinates

`buildSrc/src/main/kotlin/kotest-publishing-conventions.gradle.kts`, line 169, unchanged by the migration:

```kotlin
"${this@publication.groupId}:${this@publication.artifactId}:${this@publication.version}"
```

| | Baseline build | Provider API branch build |
|---|---|---|
| Bytecode of the template | concatenates three `String` values | concatenates three `Property` objects |
| Coordinates logged by `:kotest-bom` | `io.kotest:kotest-common-jvm:6.99.99-LOCAL`, … (74) | `property 'groupId':property 'artifactId':property 'version'` (1) |
| `<dependency>` entries in the generated POM | 74 | 1, with `<groupId>property 'groupId'</groupId>` |

Verified by running `:kotest-bom:generatePomFileForKotestBomPublication` on both sides (`bom-check/`). The task succeeds on both; nothing fails or warns. The fix is `.get()` on each of the three properties.

This was found through the `buildSrc` dump (a class file that differs although its source does not), not through the root build's dump, where `assemble` never runs the POM task.

## Migrated build logic

| Edit | Effect seen in the dumps |
|---|---|
| `KotestPlugin.kt` in `kotest-framework-plugin-gradle`: `includePatterns` / `commandLineIncludePatterns` read with `.get()`, `clear()` → `set(emptySet())`, `isFailOnNoMatchingTests` / `isIgnoreExitValue` → property assignment | `compileKotlin` of that module: 35 of its class files differ, as do its jar and sources jar. No other module is affected. |
| `kotest-intellij-plugin/build.gradle.kts`: `instrumentCode = true` → `false` | `instrumentCode` skipped, its 218 instrumented classes absent. The `jar` task's 278 entries are identical apart from `META-INF/MANIFEST.MF`. |

Not exercised: the edited plugin code runs when a consuming build executes tests, which `assemble` does not do. Its behaviour was not compared.

## `buildSrc`: unedited source that compiles differently

| Class | Call that changed | Effect |
|---|---|---|
| `Kotest_publishing_conventions_gradle$9$1$2$1$1` | `MavenPublication.getGroupId/ArtifactId/Version` return `Property` | **Changed behaviour**, see "BOM coordinates" |
| `Kotest_base_gradle$2` | `setPreserveFileTimestamps(false)` / `setReproducibleFileOrder(true)` → set on the property | None seen: jars are byte-identical |
| `Kotlin_conventions_gradle$2$1` | `TestFilter.setFailOnNoMatchingTests(false)` → set on the property | Not exercised |
| `Kotlin_conventions_gradle$2`, `Kotest_jvm_conventions_gradle$5`, `Kotest_junit4_conventions_gradle$5` | `Test.getJvmArgumentProviders()` returns `ListProperty` instead of `List` | Not exercised |
| two `…$inlined$sam$i$org_gradle_api_Action$0` classes | no difference in the disassembled code | Not traced |

## Reason mnemonics

| Mnemonic | Kind | Meaning | Basis |
|---|---|---|---|
| `VALUE-UNSET` | Task API | A property whose eager getter returned a default now reads as unset (`null`). | The dump reads lazy properties with `getOrNull()`. `Delete.followSymlinks` is a `Property<Boolean>` with no convention; the task action applies the default with `getOrElse` (checked in the distribution's bytecode). Not a behaviour change. |
| `MIGRATED-SOURCE` | Build logic | The file is, or is built from, source the migration edited. | The only differing source input is `KotestPlugin.kt`. |
| `WORKAROUND` | Build logic | Consequence of `instrumentCode = false` on the migration branch. | Outcome and outputs of `:kotest-intellij-plugin:instrumentCode`. |
| `API-REBIND` | Compilation | Unedited source compiled against a changed Gradle API. | `javap` on the 8 `buildSrc` classes. |
| `GRADLE-VERSION` | Outputs | The file contains the Gradle version, or a path under the version-specific Gradle cache directory. | `Created-By: Gradle 9.9.2` in `MANIFEST.MF`; `…/caches/9.9.2/transforms/<hash>/…` paths in Android blame logs and compiled resources. |
| `PROJECT-PATH` | Outputs | The file embeds the absolute path of the checkout. | Differs between two baseline builds at different paths; identical when the Provider API branch build runs at the baseline's path. |
| `RUN-VARIANCE` | Outputs | Differs between two runs of the same build at the same path. | Second baseline run. Kotlin `last-build.bin` (84 tasks), three Android manifest-merger reports, three `compile-file-map.properties`. |
| `UPSTREAM` | Propagation | An input differs only because it is the output of a task that already differs. | Every differing input file is such an output, or a distribution jar (see `DISTRIBUTION`). |
| `DISTRIBUTION` | Inputs | A classpath contains the Gradle distribution's own jars. | `kotest-framework-plugin-gradle` and `buildSrc` compile against the Gradle API. |
| `QUERY-ERROR` | Tool noise | The dump script could not read a property after the build ("resolution … without an exclusive lock"). | Same error on both sides; on 504 tasks only the exception class name differs. The unreadable property was **not compared**. |

## Control runs

| Comparison | Differing output files | What it shows |
|---|---|---|
| Baseline vs Provider API branch build, each in its own worktree | 3,173 in 769 tasks | The raw comparison |
| Baseline vs baseline, same path (`control/dump-before-rerun.json`) | 90 in 90 tasks | `RUN-VARIANCE` |
| Baseline vs baseline at a different path (`control/dump-before-other-path.json`) | 2,750 of the 3,173 | `PROJECT-PATH` |
| Baseline vs Provider API branch build at the baseline's path (`control/dump-after-at-before-path.json`) | 487 in 96 tasks | What is left once the path is equal |

The last row is the one the summary is based on. Its 487 files are: 84 `last-build.bin` and 6 Android report and state files, the same 90 as in the second row (`RUN-VARIANCE`); 220 for `instrumentCode` (`WORKAROUND`); 35 classes, 7 incremental-compilation files and 2 jars for the edited module (`MIGRATED-SOURCE`); 131 Android blame and path-map files, one `MANIFEST.MF` and the jar containing it (`GRADLE-VERSION`).

## Differences

Each row is one kind of difference; the count is the number of tasks showing it. Output rows are from the same-path comparison.

### Task inputs and declared properties

| Tasks | Task type | Difference | Reason |
|---|---|---|---|
| 456 of 456 | `Delete` | input `followSymlinks`: `false` → `null` | `VALUE-UNSET` |
| 1 of 1 | `Javadoc` | input `options`: text form of the object changed | Tool noise: the object has no stable `toString()` |
| 1 | `KotlinCompile` (`kotest-framework-plugin-gradle`) | `sources`: `KotestPlugin.kt` | `MIGRATED-SOURCE` |
| 3 | `KotlinCompile`, `JavaCompile`, `Javadoc` (same module) | classpath: Gradle API and Kotlin jars of the distribution | `DISTRIBUTION` |
| 1 | `VerifyLibraryResourcesTask` | 5 transformed AndroidX resource directories | `GRADLE-VERSION` |
| 82 | `DefaultTask` (79), `Jar` (3) | inputs that are outputs of differing tasks | `UPSTREAM` |
| 629 | Kotlin, KSP and Java compile tasks | property query error on both sides | `QUERY-ERROR` |

### Outputs

| Tasks | Task type | Difference | Reason |
|---|---|---|---|
| 84 | `KotlinCompile` (41), `Kotlin2JsCompile` (43) | `last-build.bin` | `RUN-VARIANCE` |
| 6 | `ProcessLibraryManifest` (3), `MergeResources` (3) | merger reports, `compile-file-map.properties` | `RUN-VARIANCE` |
| 1 | `:kotest-intellij-plugin:instrumentCode` | 218 classes and one `kotlin_module` no longer produced | `WORKAROUND` |
| 1 | `KotlinCompile` (`kotest-framework-plugin-gradle`) | 35 class files, incremental-compilation state | `MIGRATED-SOURCE` |
| 2 | `Jar` (same module: jar, sources jar) | archive content | `MIGRATED-SOURCE` |
| 2 | `GenerateManifestTask`, `Jar` (`kotest-intellij-plugin`) | `Created-By: Gradle …` | `GRADLE-VERSION` |
| 2 | `MergeResources`, `MapSourceSetPathsTask` | 129 blame JSON files, `merger.xml`, `file-map.txt` | `GRADLE-VERSION` |

### `buildSrc`

| Tasks | Task type | Difference | Reason |
|---|---|---|---|
| 6 | `KotlinCompile` (2), `GroovyCompile`, `JavaCompile`, `GeneratePrecompiledScriptPluginAccessors`, `Jar` | classpaths contain distribution jars | `DISTRIBUTION` |
| 2 | `KotlinCompile` | `freeCompilerArgs`: the list of Gradle API types passed to the compiler plugin | `DISTRIBUTION` |
| 1 | `KotlinCompile` (`compileKotlin`) | 8 of 815 class files | `API-REBIND` |
| 1 | `Jar` | `buildSrc.jar` | `UPSTREAM` |

## Limitations of this comparison

- `assemble` compiles main code only. Tests, publication tasks and the IntelliJ plugin distribution were not run. The BOM defect was found only because the `buildSrc` bytecode pointed at it; other `API-REBIND` call sites marked "not exercised" were not checked at run time.
- A property read that silently changes meaning is invisible to this method unless a task that uses the value runs. Only `buildSrc` was inspected for such call sites, and only where the bytecode differs.
- File collections are compared as sets. A classpath with the same entries in a different order shows as identical.
- The properties listed under `QUERY-ERROR` could not be read on either side and are not part of the comparison. Most affected tasks are `no-source` (402) or skipped (178); 49 executed.
- 28 Kotlin/JS incremental-cache files in `kotest-property-permutations` and `kotest-property-datetime` differ in the two-worktree comparison and in neither baseline control. They are identical in the same-path comparison, so they were not traced further.
- The Provider API branch build identifies itself as 9.9.0, the baseline build as 9.9.2; they also differ by mainline changes after the branch point.
- The migration branch was produced against an older Provider API distribution (`g951-to-PAPI-20260609`). Whether `instrumentCode = false` is still needed on this distribution was not checked.

## Files

- `dump-before*.json`, `dump-after*.json`: the dumps (root build and `buildSrc`)
- `comparison.txt`, `comparison-verbose.txt`, `comparison-buildSrc.txt`: `compare_dumps.py` output for the two-worktree comparison
- `before.log`, `after.log`: build logs
- `no-workaround/`: logs and dumps of both builds without the Kotlin metadata workaround (both fail)
- `control/`: second baseline run, baseline at a different path (`other-path` worktree), Provider API branch build at the baseline's path, with logs and `comparison-same-path.txt`
- `bom-check/`: logs and generated POMs of `:kotest-bom:generatePomFileForKotestBomPublication` on both sides
- `run.sh`, `control/*.sh`: the invocations; `analyze.py`, `outfiles.py`, `residual.py`: the scripts that produced the counts
