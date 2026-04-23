# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [abstratt/spring-boot](https://github.com/abstratt/spring-boot) (fork of spring-projects/spring-boot)
- **Task**: Gradle 9 → 10 lazy-property migration on the custom Provider API preview distribution (`gradle-provider-api-20260204140400.zip`)
- **Base commit**: [`09ece89`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e) (merge-base of the two branches)
- **Date**: 2026-04-22

## Models under test

Both runs used the same model and the same tool. The **only deliberate axis of variation is the pipeline**: v4 ran the full nine-task workflow (including the bulk task-06 `Migrate Build Scripts and Gradle API Usages` commit), v4-minus-task-6 skipped task 06 and deferred every rewrite to the reactive verify commits.

| Label | Model identifier | Tool | Branch | Base → Branch |
|---|---|---|---|---|
| **v4** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1946`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1946) | [compare](https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260422-1946) |
| **v4-minus-task-6** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-2013`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-2013) | [compare](https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260422-2013) |

## Executive summary

**v4 wins on all four criteria.** v4-minus-task-6 is half the wall-clock of v4 (9m 6s vs. 17m 3s) but that saving comes from work it silently skipped: seven latent runtime regressions on shared files (all shapes of eager consumption of migrated `Property<T>`), ten Groovy `build.gradle` scripts left with legacy `ListProperty` operators, eight deprecated-setter call sites still on removed-API paths, and no `MIGRATION_NOTES.md` to record what was considered and set aside. The `./gradlew help` and `./gradlew assemble` gates pass on v4-minus-task-6 because none of these paths execute during configuration or assembly — `javac` accepts `Object + String`, and Groovy's metaclass machinery accepts `<<` / `+=` on `ListProperty` at parse time. The experiment is a clean controlled comparison of the same model and tool with a single pipeline step flipped on/off; the result confirms that task 06 is load-bearing and the verify gates alone are not a substitute for it.

### Headline metrics

| Metric | v4 | v4-minus-task-6 |
|---|---|---|
| Wall-clock elapsed (self-reported) | **17m 03s** | **9m 06s** |
| Wall-clock elapsed (swap → report commit timestamps) | 18m 14s | 10m 06s |
| Task-06 migrate commit present? | **yes** ([`ab4b6c7`](https://github.com/abstratt/spring-boot/commit/ab4b6c727dfc8d2378e237fecf794250b871ba8e), 34 files) | **no** (intentionally skipped) |
| Files changed across branch (vs base) | **37** | **23** |
| Files in verify-help commit | 2 | 12 |
| Files in verify-assemble commit | 2 | 9 |
| `./gradlew help` passed at branch tip | yes | yes |
| `./gradlew assemble` passed at branch tip | yes | yes |
| Latent runtime regressions on shared files | **0** | **7** |
| Removed-accessor call sites left unmigrated | **0** (on unique-to-v4 files) | **8** |
| Groovy syntax errors introduced | 0 | 0 |
| Semantic regressions (`from(...)` where `setFrom(...)` was needed) | 0 | 0 |
| `buildSrc/` migrated | yes | yes |
| DSL (`*.gradle`) files with residual `<<` / `+=` on `ListProperty` | **0** | **10** |
| `MIGRATION_NOTES.md` deferral document | yes (1432 lines, machine-generated) | **absent** |
| `Assistant` commit trailer correctly filled on all commits | yes | yes |

Of the 22 Java/Groovy files touched on both branches, **14 are byte-identical**, 2 are cosmetically different, and **7 exhibit a v4-minus-task-6 regression that v4 got right**. Zero cases where v4 is worse than v4-minus-task-6. The 14 files v4 touches that v4-minus-task-6 does not are 10 Groovy `build.gradle`s, `WarPluginAction.java`, `AbstractBootArchiveTests.java`, one `.gradle` test fixture, and `MIGRATION_NOTES.md`.

## Methodology

Same pipeline base on both branches; task 03 unnecessary (repo already on 9.x). v4-minus-task-6 omits task 06.

| Task | v4 | v4-minus-task-6 |
|---|---|---|
| 04 Swap Gradle Distribution | [`2fd0996`](https://github.com/abstratt/spring-boot/commit/2fd09961cab392c5ff66e03324a73b9b4c4fb6ce) | [`88150ce`](https://github.com/abstratt/spring-boot/commit/88150ced90f57e099b8e420fb64c7c298bb810b1) |
| 06 Migrate Build Scripts and Gradle API Usages | [`ab4b6c7`](https://github.com/abstratt/spring-boot/commit/ab4b6c727dfc8d2378e237fecf794250b871ba8e) | — *(skipped per run definition)* |
| 07 Verify with `./gradlew help` | [`d300d56`](https://github.com/abstratt/spring-boot/commit/d300d56d2da5f5d1a747ca289376012f100841f1) | [`15750dc`](https://github.com/abstratt/spring-boot/commit/15750dc4b5d4b9012c0723dad9f3a524959fd0a1) |
| 08 Verify with `./gradlew assemble` | [`8b19722`](https://github.com/abstratt/spring-boot/commit/8b19722bdcb84c18ecb050c252dced81c74eac28) | [`c4d6c82`](https://github.com/abstratt/spring-boot/commit/c4d6c82f59261e057f8f7104d970dd2426e73cd3) |
| 09 Generate Report | [`b2e74a2`](https://github.com/abstratt/spring-boot/commit/b2e74a2ab82696e00bc126ba85c5fd7d8d9883c9) | [`c999b71`](https://github.com/abstratt/spring-boot/commit/c999b7141bb223f662300d0cb7624dead84edb9d) |

Every commit on both branches carries the `A:` trailer with content `Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]` (the key is `A:` on both, not `Assistant:`). v4-minus-task-6's REPORT explicitly acknowledges the missing task-06 commit: *"There is no task-06 commit on the branch; the `Verify with` commits carry the source-level transformations."*

## Results by criterion

### (1) Behavior preservation

**v4 wins.** v4-minus-task-6 introduces seven latent runtime regressions on lines that still compile — `javac` happily applies `Object.toString()` in string concatenation and `String.format`, and legacy eager setters still exist on the preview distribution. The five sites below match the ones found in the v1-vs-v4-minus-task-6 benchmark; walking the shared files again against v4 surfaced two more.

**Regression 1 — `JavaConventions.java:300` (Checkstyle coordinate)**

```diff
-		checkstyleDependencies.add(project.getDependencies()
-			.create("com.puppycrawl.tools:checkstyle:" + checkstyle.getToolVersion().get()));
+		checkstyleDependencies
+			.add(project.getDependencies().create("com.puppycrawl.tools:checkstyle:" + checkstyle.getToolVersion()));
```

v4-minus-task-6 sets `checkstyle.getToolVersion().set(...)` four lines earlier (line 295 of the same file), proving it knows the accessor returns `Property<String>` — yet concatenates the raw property object here. The resulting dependency coordinate is `com.puppycrawl.tools:checkstyle:property(java.lang.String, …)`, which fails resolution the moment any `Checkstyle` task runs. ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java#L300))

**Regression 2 — `ApplicationPluginAction.java:57` (distribution base name)**

```diff
-				.convention((project.provider(() -> javaApplication.getApplicationName().get() + "-boot")));
+				.convention((project.provider(() -> javaApplication.getApplicationName() + "-boot")));
```

Same shape: `Property<String>` concatenated directly. First `./gradlew bootDistZip` produces a garbage archive name. ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java#L57))

**Regression 3 — `BootRun.java:62` (self-referential `ConfigurableFileCollection`)**

```diff
-		// Snapshot the current classpath files before reassigning to avoid a circular reference.
-		getClasspath().setFrom(getProject().files(srcDirs, getClasspath().getFiles())
-				.filter((file) -> !file.equals(resourcesDir)));
+		getClasspath().setFrom(getProject().files(srcDirs, getClasspath()).filter((file) -> !file.equals(resourcesDir)));
```

Live `ConfigurableFileCollection` passed into its own `setFrom` — exactly the cycle `MIGRATION_RULES.md` says must be broken with `.getFiles()`. v4-minus-task-6 drops both the snapshot and the rationale comment. `BootRun.sourceResources(...)` throws `A circular evaluation has been detected` the first time its classpath resolves. ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java#L62))

**Regression 4 — `BootRun.java:70` (immutable-list `.set(get())` snapshot)**

```diff
-			// Snapshot current jvmArgs before reassigning to avoid a circular reference.
-			getJvmArgs().set(new java.util.ArrayList<>(getJvmArgs().get()));
+			getJvmArgs().set(getJvmArgs().get());
```

Subtler than it looks. Gradle's `DefaultListProperty.get()` returns an **immutable** view. v4-minus-task-6's `getJvmArgs().set(getJvmArgs().get())` stores that immutable list as the property's new value, and the next line (`jvmArgs("-XX:TieredStopAtLevel=1")`, which routes into the backing list's `add(...)`) raises `UnsupportedOperationException`. v4 wraps the snapshot in a fresh `ArrayList` before setting, preserving mutability. This fires in the real run path for any `BootRun` with `optimizedLaunch=true` (the default). ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java#L70))

**Regression 5 — `BootArchiveSupport.java:132` (`.get()` on an unset `Property<String>`)**

```diff
-		String metadataCharset = jar.getMetadataCharset().getOrNull();
+		String metadataCharset = jar.getMetadataCharset().get();
```

`Property<String>.get()` throws `MissingValueException` when no value is configured; `getOrNull()` returns null and the calling site falls back to UTF-8. v4-minus-task-6's use of `.get()` narrows the set of valid archive configurations — any `BootJar` / `BootWar` that does not explicitly configure `metadataCharset` will now fail. ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java#L132))

**Regressions 6 & 7 — `RepositoryTransformersExtension.java:91` and `MavenMetadataVersionResolver.java:135` (`Property<URI>` into `String.format`)**

```diff
-		xml.append("%s\t<url>%s</url>%n".formatted(indent, repository.getUrl().get()));
+		xml.append("%s\t<url>%s</url>%n".formatted(indent, repository.getUrl()));
```

```diff
-			.formatted(repository.getName(), repository.getUrl().get(), credentials));
+			.formatted(repository.getName(), repository.getUrl(), credentials));
```

Both files contain **internal inconsistency**: v4-minus-task-6 itself calls `repository.getUrl().get()` at other sites (lines 61/69 of `RepositoryTransformersExtension.java`; line 83 of `MavenMetadataVersionResolver.java`) — it fixed the lines the compiler complained about and stopped. A generated Maven `<url>…</url>` element containing `property(java.net.URI, …)` corrupts the published Maven settings the first time the bom tooling runs. ([RepositoryTransformersExtension.java:91](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/RepositoryTransformersExtension.java#L91) · [MavenMetadataVersionResolver.java:135](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/bom/bomr/MavenMetadataVersionResolver.java#L135))

**Deprecated-but-still-compiling setters.** v4-minus-task-6 also leaves **eight call sites** on old Gradle setters that haven't been removed yet under the preview — but which task 06 on v4 migrated in anticipation of future removal:

- [`WarPluginAction.java:99`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/WarPluginAction.java#L99) — `bootWar.setClasspath(classpath)` stays on the eager setter
- [`AbstractBootArchiveTests.java:336, 381, 382, 412`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/test/java/org/springframework/boot/gradle/tasks/bundling/AbstractBootArchiveTests.java#L336) — `setPreserveFileTimestamps` (×2), `setReproducibleFileOrder`, `setMetadataCharset`
- Plus a `.gradle` test fixture `…-javaCompileTasksUseParametersAndAdditionalCompilerFlags.gradle`

v4 rewrites all of these in its migrate commit ([`ab4b6c7`](https://github.com/abstratt/spring-boot/commit/ab4b6c727dfc8d2378e237fecf794250b871ba8e)). (Both branches leave the `setClasspath(...)` calls at `AbstractBootArchiveTests.java:221,233` untouched — those sites target `Jar.setClasspath`, which remains a first-class method in the preview, so leaving them is defensible.)

### (2) Lazy vs eager

**v4 wins.** The five `Property<T>` / `Property<URI>` / `ListProperty` and one `ConfigurableFileCollection` regressions above are all lazy-resolution failures under a different framing: each is a point where the rewrite was *half-done* — the write side was migrated (`.set(...)` / `.setFrom(...)`) but the read side was left on the pre-migration assumption that the accessor still returns a concrete value. v4 completes the read-side analysis everywhere; v4-minus-task-6 does so only where `javac` complained, which misses every case where Java's `toString()` promiscuity or a surviving legacy setter silences the error.

No new eager `.get()` calls inside configuration blocks were introduced by either branch, and neither branch exhibits the `Property.set(otherProvider.get())` anti-pattern.

### (3) Coverage

**v4 wins decisively.** v4-minus-task-6 skipped task 06 entirely, so the ten `build.gradle` files using `<<` / `+=` on `ListProperty<String>` all slip through the `help`/`assemble` gates. Groovy's metaclass dispatch accepts these operators at parse time and defers the failure indefinitely. Concrete residuals at the v4-minus-task-6 tip:

```diff
# core/spring-boot/build.gradle — unmigrated on v4-minus-task-6, migrated on v4
-		options.compilerArgs << '-Alog4j.graalvm.groupId=org.springframework.boot'
-		options.compilerArgs << '-Alog4j.graalvm.artifactId=spring-boot-log4j'
+		options.compilerArgs.add('-Alog4j.graalvm.groupId=org.springframework.boot')
+		options.compilerArgs.add('-Alog4j.graalvm.artifactId=spring-boot-log4j')
```

```diff
# module/spring-boot-jetty/build.gradle (and 8 more files with the same jvmArgs += pattern)
-		jvmArgs += "--add-opens=java.base/java.net=ALL-UNNAMED"
+		jvmArgs.add("--add-opens=java.base/java.net=ALL-UNNAMED")
```

Full list of `.gradle` files v4 migrated and v4-minus-task-6 left untouched:

- [`core/spring-boot/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/core/spring-boot/build.gradle)
- [`core/spring-boot-autoconfigure/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/core/spring-boot-autoconfigure/build.gradle)
- [`core/spring-boot-testcontainers/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/core/spring-boot-testcontainers/build.gradle)
- [`integration-test/spring-boot-integration-tests/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/integration-test/spring-boot-integration-tests/build.gradle)
- [`module/spring-boot-jetty/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/module/spring-boot-jetty/build.gradle)
- [`module/spring-boot-security/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/module/spring-boot-security/build.gradle)
- [`module/spring-boot-servlet/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/module/spring-boot-servlet/build.gradle)
- [`module/spring-boot-tomcat/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/module/spring-boot-tomcat/build.gradle)
- [`module/spring-boot-webflux/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/module/spring-boot-webflux/build.gradle)
- [`module/spring-boot-websocket/build.gradle`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/module/spring-boot-websocket/build.gradle)

The one `.gradle` file v4-minus-task-6 migrated (`loader/spring-boot-loader-tools/build.gradle`) is the sole site with a `-=` operator, which raises a compile error against `ListProperty` and therefore **forced** a fix in task 07. `<<` and `+=` do not force a fix; they survive reactive verification.

`buildSrc/` Java coverage is numerically the same on both branches (11 files migrated on each), but the quality differs — v4-minus-task-6 has the regressions documented in §1 on the very same files.

### (4) Self-reporting

**v4 wins.** Both REPORTs are internally consistent about their own scope, and every commit on both branches has the correct `A:` trailer (no `<<Tool Name>>` placeholder was left as template).

- **v4-minus-task-6 has no `MIGRATION_NOTES.md`.** Skipping task 06 removes the step that produces this artifact. A reviewer picking up v4-minus-task-6 has no record of what was considered and intentionally left alone versus what was never examined.
- **v4's `MIGRATION_NOTES.md` is a machine-generated backlog, not curated analysis.** The file is 1432 lines, 596 deferral entries. Across all 596 entries, only **7 distinct reason strings** are used; 511 of the 596 entries (86%) carry the identical Cat-B boilerplate text `"getter rewrite depends on downstream usage — apply .get() or lazy wiring based on compile errors"`. This matches the `apply_migrations.py` output pattern. The per-entry context (file:line + symbol) is useful as a todo pointer, but there is no receiver-type reasoning per entry — the file should be read as a mechanical deferral list, not as the curated false-positive taxonomy v1 produced on 2026-04-22 morning. v4's REPORT describes it as *"558 scanner-flagged sites documented with specific per-entry reasons (no raw boilerplate left)"*; the per-entry count is off (actual: 596) and the "specific per-entry reasons" framing overclaims what 7 reason strings across 596 entries can support.
- **v4-minus-task-6's REPORT is accurate about what it did do but silent on the seven regressions.** The "Known limitations" section mentions `SourceSet` setters as a genuine deferral but does not flag the `Property.toString()` bugs in `JavaConventions`, `ApplicationPluginAction`, `RepositoryTransformersExtension`, and `MavenMetadataVersionResolver`; the `BootRun.java:62` self-reference; the `BootRun.java:70` immutable-list hazard; or the `BootArchiveSupport.java:132` `.get()` regression. The report also describes `getJvmArgs().set(getJvmArgs().get())` in `BootRun.exec()` as *"a self-assignment no-op rewritten as…"* — it is in fact a detach-from-convention idiom, and (as §1 Regression 4 shows) the specific form v4-minus-task-6 committed is defective.
- **v4's REPORT matches reality.** Every rule kind claimed was applied; the Javadoc-link removal is explained with cause and intended follow-up; the two `MavenPluginPlugin.java` / `JavaConventions.java` revert decisions (sites where `apply_migrations.py` over-rewrote and task 07 walked them back) are named. Compared to v4-minus-task-6's REPORT, v4's REPORT does have one overclaim (the `MIGRATION_NOTES.md` characterization above) but is otherwise complete.

## Verification cost — the rescue effect

| Branch | Commit | Files | Breakdown |
|---|---|---|---|
| v4 | [`d300d56`](https://github.com/abstratt/spring-boot/commit/d300d56d2da5f5d1a747ca289376012f100841f1) (help) | 2 | **Mixed**: `JavaConventions` reverts `Format.setEncoding` / `CheckAotFactories.setSource` / `CheckSpringFactories.setSource` over-rewrites from the migrate commit (not Gradle receivers); `MavenPluginPlugin` reverts two `Sync.setDestinationDir` over-rewrites. These are `apply_migrations.py`-introduced mis-rewrites that task 07 walked back. |
| v4 | [`8b19722`](https://github.com/abstratt/spring-boot/commit/8b19722bdcb84c18ecb050c252dced81c74eac28) (assemble) | 2 | **Mixed**: `build-plugin/build.gradle` drops the Javadoc `links` line (Provider-API snapshot has no docs URL); `JavaPluginAction` reverts the `resolveMainClassName.setClasspath` over-rewrite (user-defined task with its own `setClasspath(Object)` overload). |
| v4-minus-task-6 | [`15750dc`](https://github.com/abstratt/spring-boot/commit/15750dc4b5d4b9012c0723dad9f3a524959fd0a1) (help) | 12 | **All "legitimate" in the narrow sense that they fix compile errors** — but this commit is doing the work task 06 should have done. It is migration under a different name. |
| v4-minus-task-6 | [`c4d6c82`](https://github.com/abstratt/spring-boot/commit/c4d6c82f59261e057f8f7104d970dd2426e73cd3) (assemble) | 9 | **Same as above** — spring-boot-gradle-plugin's share of task 06 happening inside task 08. |

v4's verify activity (4 files, all reverts of `apply_migrations.py` over-rewrites) is the expected signature of a pipeline where task 06 took an aggressive first pass and tasks 07/08 walked back the misses. v4-minus-task-6's 21-file verify activity is **task 06 relocated under a misleading subject line**. The verify commit messages (`Verify with ./gradlew help`) imply green-light gates, but they actually carry the migration work — erasing the reviewable signal that a dedicated `Migrate Build Scripts and Gradle API Usages` commit is designed to preserve.

## Verdict

1. **Behavior preservation — v4 wins.** v4-minus-task-6 introduces seven latent runtime regressions at [`JavaConventions.java:300`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java#L300), [`ApplicationPluginAction.java:57`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java#L57), [`BootRun.java:62`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java#L62) and [:70](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java#L70), [`BootArchiveSupport.java:132`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java#L132), [`RepositoryTransformersExtension.java:91`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/RepositoryTransformersExtension.java#L91), and [`MavenMetadataVersionResolver.java:135`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/bom/bomr/MavenMetadataVersionResolver.java#L135). It also leaves eight removed-accessor call sites on the old eager setters in `WarPluginAction.java`, `AbstractBootArchiveTests.java`, and the `.gradle` test fixture.
2. **Lazy vs eager — v4 wins** (same findings through the lazy-resolution lens).
3. **Coverage — v4 wins.** v4 migrates 13 DSL / test-fixture `.gradle` files; v4-minus-task-6 migrates 1. v4-minus-task-6 retains `<<` / `+=` on `ListProperty<String>` in 10 `build.gradle` files and the one test fixture.
4. **Self-reporting — v4 wins.** v4-minus-task-6 produces no `MIGRATION_NOTES.md` and its REPORT does not acknowledge the seven regressions. v4's `MIGRATION_NOTES.md` is machine-generated (not the curated analysis its REPORT claims) and the REPORT mis-counts its own entries, but the artifact exists and at least provides a traceable backlog.

### Recommendation

**Accept v4** ([`gradle-10-migration/20260422-1946`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1946)). Nothing from v4-minus-task-6 is worth salvaging: its unique value add is zero files, and the wall-clock saving is pure coverage loss. The short runtime is an illusion of throughput, not a signal of efficiency.

### Aside — the controlled experiment

Because both branches used the same model and the same tool and differ only in whether task 06 ran, the 14-file / 7-regression / 1432-line-notes-file delta between them is **directly attributable to task 06 and nothing else**. Specifically:

- **Property-consumption read sites** — string concatenation, `String.format`, `getOrNull()` vs `.get()` default handling, immutable-list snapshots — produce silent runtime garbage on `Property<T>` unless explicitly handled. `javac` does not flag them. A reactive path driven only by compile errors misses every one: five of the seven regressions in v4-minus-task-6 are exactly this class.
- **Groovy DSL operators on `ListProperty`** — `<<`, `+=` — are absorbed by Groovy's metaclass dispatch without failing configuration. Only `-=` raised a compile error and got fixed reactively on v4-minus-task-6.
- **Scanner false-positive triage** — v4's `MIGRATION_NOTES.md`, even as raw backlog, is the only artifact that records *which sites were scanned and set aside*. Without it (v4-minus-task-6) a reviewer cannot distinguish "considered and left" from "never looked at".

Task 06 is what turns each of those classes of issue from "hidden" to "visible": the bulk-rewrite step forces a read-side analysis, an operator-rewrite sweep, and a scanner-hit triage that the reactive path simply doesn't do. The verify gates (`./gradlew help`, `./gradlew assemble`) are real signal for certain classes of failure (missing imports, removed methods in reachable code) but they are **not sufficient** to catch a lazy-property migration. The experiment confirms that tightening the verify gates would not close the gap — the test budget for this repo would need to grow into the configuration-path execution tree to catch what task 06 catches statically.
