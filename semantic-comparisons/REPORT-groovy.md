# Task graph and task input/output differences: groovy, baseline build (Gradle 9.9.2) vs Provider API branch build

| | Baseline build | Provider API branch build |
|---|---|---|
| Code | baseline commit `939b2f8db` ("Merge pull request #2 from apache/master"; the project was already on the baseline Gradle version, so the branch has no "Upgrade Baseline Gradle" commit) | migration branch tip `2b19530db` (`gradle-10-migration/20260615-1919-g951-to-PAPI-20260609`) |
| Gradle | `9.9.2` (release) | `9.9.0-20261124151743+0000` (built from the Provider API migration branch, revision `8779a723`) |
| JVM | Temurin 21.0.11 | Temurin 21.0.11 |
| Build result | passed | passed |

Both builds ran `clean assemble --no-scan --no-build-cache --no-configuration-cache` with `task-dump.init.gradle`; the JSON dumps were then compared. No workaround was needed on either side. groovy has one included build, `build-logic`, so there is one dump per build:

| Build | Tasks, baseline build | Tasks, Provider API branch build | Identical tasks |
|---|---|---|---|
| root (`groovy`) | 497 | 497 | 423 |
| included `build-logic` | 9 | 9 | 3 |

**Read this first**

- Input property values are compared by **eager-API semantics**. Where a lazy property replaced an eager one, the dump reads the value through the eager accessor generated for that property (`org.gradle.internal.classpath.generated.<Type>_Adapter.access_get_<originalAccessor>`, or the `$$BridgeFor$$` class of a custom adapter). That is what code compiled against an earlier Gradle gets when it calls the old getter. In the Provider API branch build, 3,681 input values across 307 tasks were read that way (3,648 in 304 root tasks, 33 in 3 `build-logic` tasks); the baseline build has no such accessors and is read as before.
- This migration **changed build logic**: 7 files, +13/−12, five of them precompiled script plugins and one class in `build-logic`. See "Migrated build logic".
- **One effective change, made by the migration itself, not by the distribution**: every `Javadoc` task now passes three `-tag` options to javadoc instead of one. The original code called `addStringOption('tag', …)` three times, and each call replaced the previous one, so the baseline build passes only `-tag implNote:…`. The migration replaced the calls with `tags = [...]`, which passes all three. No Java source in the project uses `@apiNote`, `@implSpec` or `@implNote`, and **all generated Javadoc HTML is identical**.
- Two input values still differ when read through the adapter: the `tags` above and `options.JFlags` (`[-Xmx1g]` → `[]`). The `JFlags` difference is how the task is read, not what it does: both builds start javadoc with `-J-Xmx1g` (`EXEC-MUTATION`).
- **No build product differs because of the Gradle distribution.** In the root build, every compiled class, jar and Javadoc file is identical except one class whose method order varies from run to run (`GEN-ORDER`, confirmed by the control run).
- In `build-logic`, the precompiled script plugins compile to different bytecode: from the migrated source, and in 4 closures of **unedited** source because the branch's Groovy DSL compiler wraps every `+=` (`DSL-TRANSFORM`). Those 4 closures configure test source sets and JMH, outside `assemble`, so their effect is not covered here.
- Each side was run with its distribution's `bin/gradle` directly, not through the wrapper. Before each run, `build-logic/build` was deleted, so its tasks executed too (`clean` does not reach included builds).
- The Provider API branch build identifies itself as 9.9.0, the baseline build as 9.9.2; they also differ by mainline changes after the branch point (embedded Kotlin 2.4.20 vs 2.4.21). Every difference is classified; items whose effect was not checked are marked as such.

## Summary

| Area | Result |
|---|---|
| Task graph | Same 497 + 9 tasks, same types, same `dependsOn` edges, same execution order |
| Task outcomes | Same on every task (409 executed, 18 up-to-date, 70 no-source in the root build) |
| Migrated values | Identical wherever the task is in the `assemble` graph (`compilerArgs`, `forkOptions.jvmArgs`, antlr `arguments`) |
| Compiled classes, root | All identical except `OptionAccessor.class` (`GEN-ORDER`) |
| Javadoc output | Identical on all 32 executed `Javadoc` tasks |
| Jars, root | Identical except `groovy-cli-picocli-raw`, which contains `OptionAccessor.class` (`UPSTREAM`) |
| `build-logic` | 14 precompiled script classes and 1 class differ (`MIGRATED`, `DSL-TRANSFORM`); 21 generated adapters differ in a version string |

## Migrated build logic

| Edit | Task | In the `assemble` graph? | Result |
|---|---|---|---|
| `options.compilerArgs << '-Xlint:deprecation'` → `.add(…)` (`org.apache.groovy-internal`) | all `JavaCompile`/`GroovyCompile` (90) | yes | `options.compilerArgs` identical on every task, e.g. `:compileJava` `[-Xlint:deprecation]` on both sides. |
| `groovyOptions.forkOptions.jvmArgs += […]` → `.addAll(…)` (`org.apache.groovy-internal`) | all `GroovyCompile` (44) | yes | Identical, e.g. `:compileGroovy` `[-Dgroovy.antlr4.cache.threshold=0, -Dgroovy.target.bytecode=17]`. |
| `arguments += ["-visitor", "-no-listener"]` → `.addAll(…)` (`org.apache.groovy-core`) | `:generateGrammarSource` | yes | `arguments` identical; generated parser sources identical. |
| `outputDirectory.canonicalPath` → `outputDirectory.get().asFile.canonicalPath` in a `doLast` (`org.apache.groovy-core`) | `:generateGrammarSource` | yes | The action ran on both sides; its output (parser files copied into the package directory) is identical. |
| three `addStringOption('tag', …)` → `tags = [...]`; `classpath += file(…)` → `classpath.from(…)` (`org.apache.groovy-documented`) | all `Javadoc` (39) | yes | **Behaviour change**: `-tag` 1 → 3 (see "Read this first"); verified in `build/tmp/javadoc/javadoc.options`. Javadoc output identical. `classpath` identical. |
| `options.forkOptions.jvmArgs += […]` → `.addAll(…)` on `compileTestGroovy` (`org.apache.groovy-base`) | `:compileTestGroovy` | **no** | Not exercised by this comparison. |
| `jvmArgs += […]` → `.addAll(…)` (`subprojects/groovy-console`, task `console`) | `:groovy-console:console` | **no** | Not exercised. |
| `jvmArgs += "--enable-preview"` → `.add(…)` (`subprojects/tests-preview`, `Test`) | `:tests-preview:test` | **no** | Not exercised. |
| `je.args.asList()` → `je.args.get()` in a `println` (`PerformanceTestsExtension`) | `performanceTests` tasks | **no** | Not exercised; class compiled differently as expected (`MIGRATED` in `build-logic`). |

## Reason mnemonics

| Mnemonic | Kind | Meaning | Basis |
|---|---|---|---|
| `MIGRATED` | Build logic | The difference follows from a source change made by the migration. | Verified: `-tag` options in `javadoc.options` on both sides; class differences checked with `javap` against the edited lines (call-site name `leftShift` → `add`, `getArgs(): List` + `asList` → `getArgs(): ListProperty`, and in 3 `Documented` classes line numbers only, shifted by the 4 lines the edit added). |
| `EXEC-MUTATION` | Task API | The dump reads task inputs after execution. In 9.9.2, `Javadoc.generate()` copies the options and adds `-Xmx<maxMemory>` to the copy's `JFlags`, but the copy shares the task's `JFlags` list, so the task's own options end up containing `-Xmx1g`. The branch's copy does not share it. | Verified in the source: 9.9.2 `CoreJavadocOptions(CoreJavadocOptions, …)` has `jFlags = original.jFlags`; the branch has `getJFlags().set(original.getJFlags())`. Verified at runtime: rerunning `:groovy-json:javadoc` with `--debug` on both sides shows the same command, `javadoc @…/javadoc.options -J-Xmx1g`. Shows on exactly the 32 executed `Javadoc` tasks, not on the 7 no-source ones. |
| `DSL-TRANSFORM` | Outputs | The branch's Groovy DSL compiler rewrites every compound assignment `a += b` into `forCompoundAssignment(a) + b`, then `toAssignmentResult(…)`, to support `+=` on lazy properties. 9.9.2 has no such transform. | Verified with `javap -v`: the call-site names `forCompoundAssignment`, `plus`, `toAssignmentResult` appear in the 4 classes and in no baseline class. `CompoundAssignmentExtensions` (branch source): both helpers return their argument unchanged unless it is a `CompoundAssignmentResult`, so on an eager `srcDirs` (`Set`) the effect should be the same. All 4 sites configure things outside the `assemble` graph (test source directories `src/test-resources`, `src/spec/test`, `src/spec/test-resources`; the JMH classpath), so their runtime effect was **not checked**. |
| `GEN-ORDER` | Project non-determinism | The Groovy compiler emits the two synthetic bridge methods `super$1$getProperty` and `super$1$invokeMethod` in either order. | Verified with `javap`: same methods, same code, swapped order. The control run's class differs from the first baseline run's and equals the Provider API branch build's. |
| `UPSTREAM` | Propagation | The file differs only because it is, or contains, the output of another task that already differs. | Verified by path. |
| `COMPILE-STATE` | Outputs | `previous-compilation-data.bin`, the incremental-compilation state, differs; not a build product. | Observed on 9 tasks (7 `GroovyCompile`, 2 `JavaCompile`), whose compiled classes are identical (except `GEN-ORDER`). 8 of them differ between the second baseline run and the Provider API branch build but not between the two baseline runs, so this is stable, not run-to-run variance. **Cause not checked**: the file's content was not inspected. |
| `TOSTRING` | Tool noise | The value is an object without a stable string form; only its `toString()` text changed. | Tool limitation. The individual `options.*` inputs of the same tasks are compared separately. |
| `QUERY-ERROR` | Tool noise | The dump script could not read a file input after the build ("resolution without an exclusive lock"). | Same error on both sides; only the exception class changed (`GradleException` → `IllegalResolutionException`). |
| `GRADLE-LIBS` | Environment | A classpath contains files of the Gradle distribution (embedded Kotlin 2.4.21 vs 2.4.20, installation beacon, generated `gradle-api` jar). | Observed from the paths. |
| `VERSION-STRING` | Outputs | A generated source file embeds the Gradle version in a message. | Verified with `diff`: one line per file, "Precompiled Groovy script plugins built by Gradle …", in all 21 files. |
| `DISK-STATE` | Comparison setup | A task outcome or a configuration-time value depends on what was on disk before the build. | Control run only, see below. |

## Control run

The baseline build was run a second time, unchanged, again with `build-logic/build` removed first. Dumps are in `control/dump-before-rerun2*.json`; comparisons in `control/comparison-*.txt`.

| Build | Outputs that differ, first baseline run vs Provider API branch build | First vs second baseline run | Second baseline run vs Provider API branch build |
|---|---|---|---|
| root | `OptionAccessor.class`, `groovy-cli-picocli-raw` jar, 9 `previous-compilation-data.bin` | `OptionAccessor.class`, the jar, 1 `previous-compilation-data.bin` (`groovy-cli-picocli`) | 8 `previous-compilation-data.bin` |
| `build-logic` | 15 classes, 21 adapter sources, the jar, 1 `previous-compilation-data.bin` | none | same as the first column |

So `OptionAccessor.class` (and the jar that contains it) varies between runs on one Gradle version. Every other output difference is stable across the two baseline runs.

The second baseline run also differs from the first in two ways that come from the first run's leftovers, not from Gradle (`DISK-STATE`): 5 `clean` tasks executed instead of being up-to-date, and `:javadoc` `options.extraOptions` includes `build/generated/sources/antlr4` in `-source-path`, because that directory existed when the second run was configured. The first baseline run and the Provider API branch build both started without it and agree on both.

## Task graph

No differences in either build: same tasks, same types, same `dependsOn` edges, same execution order, same outcomes.

## Differences, root build

Each row is one kind of difference; the count is the number of tasks showing it. A task can appear in more than one row. The 74 differing tasks are all covered.

| Task type | Difference | Tasks | Reason |
|---|---|---|---|
| `Javadoc` | input `options.tags`: `[]` → `[apiNote:a:"API Note:", implSpec:a:"Implementation Requirements:", implNote:a:"Implementation Note:"]` (read through the adapter) | 39 (all) | `MIGRATED` |
| `Javadoc` | input `options.JFlags`: `[-Xmx1g]` → `[]` (read through the adapter) | 32 (all executed) | `EXEC-MUTATION` |
| `Javadoc` | input `options`: `StandardJavadocDocletOptions@<id>` → `task '…' property 'options'` | 39 (all) | `TOSTRING` |
| `GroovyCompile` | output class `groovy/cli/picocli/OptionAccessor.class` (`:groovy-cli-picocli`) | 1 | `GEN-ORDER` |
| `Jar`, `Javadoc` | input classes, output jar of `:groovy-cli-picocli` | 2 | `UPSTREAM` |
| `GroovyCompile`, `JavaCompile` | output `previous-compilation-data.bin` | 9 | `COMPILE-STATE` |
| `GroovyCompile`, `JavaCompile`, `Javadoc` | only the exception class in the query error text differs | 26 | `QUERY-ERROR` |

The `tags` value in the baseline build is `[]` because the `-tag` option was added as a string option, which the dump does not show (`options.extraOptions` is identical on both sides). What javadoc received was read from `build/tmp/javadoc/javadoc.options`: `-tag implNote:…` only in the baseline build, all three in the Provider API branch build.

## Differences, `build-logic`

| Task | Difference | Reason |
|---|---|---|
| `:compileGroovyPlugins`, `:extractPluginRequests` | input script files `org.apache.groovy-{base,core,documented,internal}.gradle` | `MIGRATED` (the edited sources) |
| `:compileGroovyPlugins` | output: 10 classes of the edited scripts (`Base` closure 11, `Core` closures 15 and 15/31, `Documented` and 4 of its closures, `Internal` closures 4 and 5) | `MIGRATED` |
| `:compileGroovyPlugins` | output: 4 classes of closures with a `+=` in unedited code: `srcDirs += …` (`Core` closure 2/18/22, `Tested` closures 1/8/9 and 1/8/10) and `classpath += compileJmhJava.classpath` (`Performance` closure 7) | `DSL-TRANSFORM` |
| `:compileGroovy` | input `PerformanceTestsExtension.groovy`; output `PerformanceTestsExtension$_version_closure3$_closure8.class` | `MIGRATED` |
| `:generatePluginAdapters` | 21 adapter sources | `VERSION-STRING` |
| `:compileJava` | input: the 21 adapter sources; output: their 21 classes | `UPSTREAM` |
| `:compileJava`, `:compileGroovy`, `:compileGroovyPlugins` | input `classpath` | `GRADLE-LIBS` (and `UPSTREAM` for `build/classes/…` directories) |
| `:compileJava` | output `previous-compilation-data.bin` | `COMPILE-STATE` |
| `:jar` | 36 classes as input; output `build-logic.jar` | `UPSTREAM` |

## Changes from the previous version of this report

First version.

## Files

In `out/task-compare-g992/groovy/`:

- `dump-before*.json`, `dump-after*.json`: the dumps (root, `build-logic`)
- `comparison*.txt`, `comparison*-verbose.txt`: `compare_dumps.py` output
- `before.log`, `after.log`: build logs
- `control/dump-before-rerun2*.json`, `control/rerun2-before.log`, `control/comparison-*.txt`: the control run
- `control/javadoc-debug-{before,after}.log`: `:groovy-json:javadoc --rerun --debug`, for the javadoc command line
