# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [abstratt/spring-boot](https://github.com/abstratt/spring-boot) (fork of spring-projects/spring-boot)
- **Task**: Gradle 9 → 10 lazy-property migration on the custom Provider API preview distribution (`gradle-provider-api-20260204140400.zip`)
- **Base commit**: [`09ece89`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e) (merge-base of the two branches)
- **Date**: 2026-04-22

## Models under test

Both runs used the same model; the branches differ in **workflow**, not in model identity. The key axis of difference is that **v1 ran the full nine-task pipeline** (including the bulk task-06 `Migrate Build Scripts and Gradle API Usages` commit), while **v4-minus-task-6 deliberately skipped task 06** and allowed task 07 (`./gradlew help`) and task 08 (`./gradlew assemble`) to drive every rewrite reactively from compile failures.

| Label | Model identifier | Tool | Branch | Base → Branch |
|---|---|---|---|---|
| **v1** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1035`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1035) | [compare](https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260422-1035) |
| **v4-minus-task-6** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-2013`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-2013) | [compare](https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260422-2013) |

## Executive summary

**v1 wins decisively on all four criteria.** v4-minus-task-6 finishes in about a third of v1's wall-clock (9m 6s vs. 29m 41s) and its build gates (`./gradlew help`, `./gradlew assemble`) pass — but every compile-successful shortcut leaves production code in a semantically broken state. The experiment confirms the value of task 06: when bulk migration is skipped, the `help`/`assemble` gates are **too coarse to detect** five latent runtime regressions (four `Property.toString()` bugs plus one `ConfigurableFileCollection` self-reference) and **by design do not reach** the eleven Groovy DSL files where `ListProperty` append/remove operators need rewriting. v4-minus-task-6 should not be accepted; the short runtime is an illusion of throughput created by silent coverage gaps.

### Headline metrics

| Metric | v1 | v4-minus-task-6 |
|---|---|---|
| Wall-clock elapsed (self-reported) | **29m 41s** | **9m 6s** |
| Wall-clock elapsed (swap → report commit timestamps) | 31m 00s | 10m 06s |
| Task-06 migrate commit present? | **yes** ([`d34f3c0`](https://github.com/abstratt/spring-boot/commit/d34f3c0db3ade90b8155f734987927ca6db71e25), 31 files) | **no** (intentionally skipped) |
| Files changed across branch (vs base) | **37** | **23** |
| Files in verify-help commit | 4 | 12 |
| Files in verify-assemble commit | 1 | 9 |
| `./gradlew help` passed at branch tip | yes | yes |
| `./gradlew assemble` passed at branch tip | yes | yes |
| Latent runtime regressions (`Property.toString()` / self-reference) | **0** | **5** |
| Removed-accessor call sites left unmigrated | **0** | **8** |
| Groovy syntax errors introduced | 0 | 0 |
| Semantic regressions (`from(...)` where `setFrom(...)` was needed) | 0 | 0 |
| `buildSrc/` migrated | yes | yes |
| DSL (`*.gradle`) files with residual `<<` / `+=` / `-=` on `ListProperty` | **0** | **10** |
| `MIGRATION_NOTES.md` curated deferral document | yes (116 lines) | **absent** |
| `Assistant` commit trailer correctly filled on all commits | yes | yes |

## Methodology

Both branches follow the same pipeline base; task 03 (Upgrade Gradle) was unnecessary because the repo is already on 9.x. v4-minus-task-6 omits task 06 entirely.

| Task | v1 | v4-minus-task-6 |
|---|---|---|
| 04 Swap Gradle Distribution | [`6043c1b`](https://github.com/abstratt/spring-boot/commit/6043c1bdab18fc8e1a1c24da5678335cdca78410) | [`88150ce`](https://github.com/abstratt/spring-boot/commit/88150ced90f57e099b8e420fb64c7c298bb810b1) |
| 06 Migrate Build Scripts and Gradle API Usages | [`d34f3c0`](https://github.com/abstratt/spring-boot/commit/d34f3c0db3ade90b8155f734987927ca6db71e25) | — *(skipped per run definition)* |
| 07 Verify with `./gradlew help` | [`513dcde`](https://github.com/abstratt/spring-boot/commit/513dcde3598349267c439ad3ee2cdd1e1dc874a4) | [`15750dc`](https://github.com/abstratt/spring-boot/commit/15750dc4b5d4b9012c0723dad9f3a524959fd0a1) |
| 08 Verify with `./gradlew assemble` | [`b07d378`](https://github.com/abstratt/spring-boot/commit/b07d37853ea67a430638f99fa3a9e369e5bf9d52) | [`c4d6c82`](https://github.com/abstratt/spring-boot/commit/c4d6c82f59261e057f8f7104d970dd2426e73cd3) |
| 09 Generate Report | [`2acb0ee`](https://github.com/abstratt/spring-boot/commit/2acb0eeade20eff712797c222b21e47765ee54ae) | [`c999b71`](https://github.com/abstratt/spring-boot/commit/c999b7141bb223f662300d0cb7624dead84edb9d) |

Every commit on both branches carries the same `Assistant` trailer content (`Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]`). Trailer key is `A:` on both branches. v4-minus-task-6's REPORT explicitly acknowledges the missing migrate commit: *"There is no task-06 commit on the branch; the `Verify with` commits carry the source-level transformations."*

Of the 22 Java/Groovy files touched by both branches, **17 are byte-identical**; **5 differ**. The 14 files v1 touches and v4-minus-task-6 does not are 11 `build.gradle` scripts, `WarPluginAction.java`, `AbstractBootArchiveTests.java`, and one `.gradle` test-fixture.

## Results by criterion

### (1) Behavior preservation

**v1 wins.** v4-minus-task-6 introduces five latent runtime regressions on lines that still compile because `javac` happily applies `Object.toString()` in string concatenation and `String.format`. None of them are exercised by `help` or `assemble`, so the gates pass. Every one would fail at the first real use:

**Regression 1 — `JavaConventions.java:300` (Checkstyle coordinate)**

```diff
-		checkstyleDependencies.add(project.getDependencies()
-			.create("com.puppycrawl.tools:checkstyle:" + checkstyle.getToolVersion().get()));
+		checkstyleDependencies
+			.add(project.getDependencies().create("com.puppycrawl.tools:checkstyle:" + checkstyle.getToolVersion()));
```

v4-minus-task-6 sets `checkstyle.getToolVersion().set(...)` four lines earlier (line 295 of the same file), proving it knows the accessor returns `Property<String>` — yet concatenates the raw property object here. The resulting dependency coordinate is `com.puppycrawl.tools:checkstyle:property(java.lang.String, …)`, which will fail resolution the moment any `Checkstyle` task runs. ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java#L300))

**Regression 2 — `ApplicationPluginAction.java:57` (distribution base name)**

```diff
-				.convention((project.provider(() -> javaApplication.getApplicationName().get() + "-boot")));
+				.convention((project.provider(() -> javaApplication.getApplicationName() + "-boot")));
```

`JavaApplication.getApplicationName()` is now `Property<String>`. v4-minus-task-6 concatenates the property itself, producing a distribution base name like `property(java.lang.String, fixed(…, myApp))-boot`. Not reached by `assemble`, but the first `./gradlew bootDistZip` would produce a garbage archive name. ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java#L57))

**Regression 3 — `BootRun.java:62` (self-referential `ConfigurableFileCollection`)**

```diff
-		// Snapshot the existing classpath before replacing to avoid a circular reference
-		getClasspath().setFrom(
-				getProject().files(srcDirs, getClasspath().getFiles()).filter((file) -> !file.equals(resourcesDir)));
+		getClasspath().setFrom(getProject().files(srcDirs, getClasspath()).filter((file) -> !file.equals(resourcesDir)));
```

v4-minus-task-6 passes the live `ConfigurableFileCollection` into a `setFrom` on the same collection — the textbook cycle that `MIGRATION_RULES.md` tells runs to break with `.getFiles()`. v1 snapshots explicitly and keeps the commentary; v4-minus-task-6 drops both, so `BootRun.sourceResources(...)` will throw `A circular evaluation has been detected` the first time its classpath resolves. `help`/`assemble` do not run a `BootRun`. ([file at commit](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java#L62))

**Regressions 4 & 5 — `RepositoryTransformersExtension.java:91` and `MavenMetadataVersionResolver.java:135` (`Property<URI>` into `String.format`)**

```diff
-		xml.append("%s\t<url>%s</url>%n".formatted(indent, repository.getUrl().get()));
+		xml.append("%s\t<url>%s</url>%n".formatted(indent, repository.getUrl()));
```

```diff
-			.formatted(repository.getName(), repository.getUrl().get(), credentials));
+			.formatted(repository.getName(), repository.getUrl(), credentials));
```

`MavenArtifactRepository.getUrl()` returns `Property<URI>`. Both files contain **internal inconsistency**: v4-minus-task-6 itself calls `repository.getUrl().get()` at other sites in the same file (lines 61 and 69 of `RepositoryTransformersExtension.java`; line 83 of `MavenMetadataVersionResolver.java`) — it fixed the lines that the compiler complained about and stopped there. A generated Maven `<url>…</url>` element containing `property(java.net.URI, …)` would corrupt the published Maven settings the first time the bom tooling runs. ([RepositoryTransformersExtension.java:91](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/RepositoryTransformersExtension.java#L91) · [MavenMetadataVersionResolver.java:135](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/bom/bomr/MavenMetadataVersionResolver.java#L135))

**Deprecated-but-still-compiling setters.** v4-minus-task-6 also leaves **eight call sites** on old Gradle setters that haven't been removed yet, so they compile under the preview distribution but will break at the first preview that drops the eager setter:

- [`WarPluginAction.java:99`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/WarPluginAction.java#L99) — `bootWar.setClasspath(classpath)` (still eager setter)
- [`AbstractBootArchiveTests.java:221, 233, 336, 381, 382`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/test/java/org/springframework/boot/gradle/tasks/bundling/AbstractBootArchiveTests.java#L221) — two `task.setClasspath(…)`, two `task.setPreserveFileTimestamps(…)`, one `task.setReproducibleFileOrder(…)`
- Plus a `.gradle` test-fixture `…-javaCompileTasksUseParametersAndAdditionalCompilerFlags.gradle` that v1 migrates

v1 rewrites all of these in its migrate commit (see `d34f3c0` diff).

### (2) Lazy vs eager

**v1 wins.** Both branches handle the obvious lazy-wiring constructs (`BootRun.exec()`'s `getJvmArgs().set(getJvmArgs().get())` snapshot idiom) identically. The divergence shows up where v4-minus-task-6's reactive path skipped a step:

- Regression 3 above is itself a lazy-vs-eager failure: the correct rewrite threads a live `Provider`-snapshot via `.getFiles()`; v4-minus-task-6 passes a live self-reference.
- Regressions 1, 2, 4, 5 are all examples of *eager consumption inside a lazy producer* (string concatenation / `String.format` against a `Property`). v1 resolves via `.get()` at the right point; v4-minus-task-6 omits it and the chain never actually resolves the property.

No new eager `.get()` calls inside configuration blocks were introduced by either branch, and neither branch exhibits the `Property.set(otherProvider.get())` anti-pattern — v4-minus-task-6's omissions are of a different shape (missing `.get()` on consumption, not overly-eager `.get()` on plumbing).

### (3) Coverage

**v1 wins by a wide margin.** v4-minus-task-6 skipped task 06 entirely, and `help`/`assemble` do not parse Groovy DSL bodies inside `compileJava {…}` / `test {…}` configuration closures unless those tasks actually execute during the gate — so the ten `build.gradle` files using `<<` / `+=` on `ListProperty<String>` all slip through. Concrete residuals at the v4-minus-task-6 tip:

```diff
# core/spring-boot/build.gradle — unmigrated on v4-minus-task-6, migrated on v1
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

Full list of `.gradle` files v1 migrated and v4-minus-task-6 left untouched:

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

The one `.gradle` file v4-minus-task-6 *does* migrate (`loader/spring-boot-loader-tools/build.gradle`) is the sole site with a `-=` operator, which raises a compile error in Groovy against `ListProperty` and therefore **forced** a fix in task 07. `<<` and `+=` don't force a fix — Groovy's metaclass dispatch accepts them — so they survive reactive verification and rot silently.

`buildSrc/` Java coverage is comparable between branches: both migrate the same 11 `buildSrc` files. The difference is quality, not count — v4-minus-task-6's reactive approach left the five regressions documented in §1 on those same files.

### (4) Self-reporting

**v1 wins.** Both REPORTs correctly list the model identity in the Assistant block, and every commit on both branches has the correct trailer (no `<<Tool Name>>` placeholders). Beyond that surface check:

- **v4-minus-task-6 has no `MIGRATION_NOTES.md`** — no curated deferral document at all. Skipping task 06 removes the step where false-positive scanner hits get catalogued. v1's [`MIGRATION_NOTES.md`](https://github.com/abstratt/spring-boot/blob/2acb0eeade20eff712797c222b21e47765ee54ae/MIGRATION_NOTES.md) lists 34 confirmed scanner hits organized by receiver-type category (user-defined tasks, third-party collisions, non-migrated Gradle types) with file + line citations. A reviewer picking up v4-minus-task-6 has no record of what was considered and intentionally left alone versus what was simply never looked at.
- **v4-minus-task-6's REPORT is accurate about what it did do, but does not flag the five regressions documented in §1.** The "Known limitations" section mentions `setRuntimeClasspath`/`setCompileClasspath` on `SourceSet` (a genuine deferral — those methods remain plain setters in this snapshot) but is silent about the latent `Property.toString()` bugs in `JavaConventions`, `ApplicationPluginAction`, `RepositoryTransformersExtension`, and `MavenMetadataVersionResolver`, and about the `BootRun` self-reference. The report also describes `getJvmArgs().set(getJvmArgs().get())` in `BootRun.exec()` as a "self-assignment no-op rewritten as"; it is in fact a legitimate convention-detach, not a no-op — consistent with v1's handling but the rationale is misdescribed.
- **v1's REPORT and `MIGRATION_NOTES.md` match reality.** Every rule kind claimed was applied; every lambda-parameter fix discovered in verify is listed; the Javadoc pin-to-9.0.0 workaround is explained with cause and intended follow-up.

## Verification cost — the rescue effect

| Branch | Commit | Files | Breakdown |
|---|---|---|---|
| v1 | [`513dcde`](https://github.com/abstratt/spring-boot/commit/513dcde3598349267c439ad3ee2cdd1e1dc874a4) (help) | 4 | **All legitimate** — lambda-parameter receivers the scanner's import heuristic missed (`JavaConventions` × 2 sites, `ConsumableContentContribution`, `ConfigurationPropertiesPlugin`, `MavenPluginPlugin`). |
| v1 | [`b07d378`](https://github.com/abstratt/spring-boot/commit/b07d37853ea67a430638f99fa3a9e369e5bf9d52) (assemble) | 1 | **Legitimate** — Javadoc external link pinned to stable Gradle 9.0.0 to dodge the missing docs URL under the preview snapshot version. |
| v4-minus-task-6 | [`15750dc`](https://github.com/abstratt/spring-boot/commit/15750dc4b5d4b9012c0723dad9f3a524959fd0a1) (help) | 12 | **All "legitimate" in the sense that they fix genuine compile errors** — but this commit is doing the job task 06 should have done. Includes `buildSrc/` mass rewrite plus one Cat-C DSL fix in `loader-tools/build.gradle`. This is migration under a different name. |
| v4-minus-task-6 | [`c4d6c82`](https://github.com/abstratt/spring-boot/commit/c4d6c82f59261e057f8f7104d970dd2426e73cd3) (assemble) | 9 | **All "legitimate" in the same sense** — spring-boot-gradle-plugin compile errors forced by the preview distribution. Same comment: this is the plugin's share of task 06 happening inside task 08. |

v1's verify activity is **5 files of true edge-case fixes** — things an up-front migrate commit genuinely could not have caught. v4-minus-task-6's **21 verify-commit files are task 06 by another name**: the rewrites that should have landed in a dedicated, reviewable `Migrate Build Scripts and Gradle API Usages` commit are instead split across two commits whose subjects (`Verify with …`) imply they are green-light gates, not migration work. The cost is invisible to the commit-message reviewer and erases the coverage signal the pipeline depends on — there is no file the reviewer can open to see "what task 06 decided to leave alone", because nothing made those decisions.

## Verdict

1. **Behavior preservation — v1 wins.** v4-minus-task-6 introduces five latent runtime regressions (string-concatenation of `Property<T>` and a `ConfigurableFileCollection` self-reference) at [`JavaConventions.java:300`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java#L300), [`ApplicationPluginAction.java:57`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java#L57), [`BootRun.java:62`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java#L62), [`RepositoryTransformersExtension.java:91`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/RepositoryTransformersExtension.java#L91), and [`MavenMetadataVersionResolver.java:135`](https://github.com/abstratt/spring-boot/blob/c999b7141bb223f662300d0cb7624dead84edb9d/buildSrc/src/main/java/org/springframework/boot/build/bom/bomr/MavenMetadataVersionResolver.java#L135). It also leaves eight removed-accessor call sites in `WarPluginAction.java` and `AbstractBootArchiveTests.java` on the old eager setters.
2. **Lazy vs eager — v1 wins** (same set of regressions viewed through the lazy-resolution lens).
3. **Coverage — v1 wins.** v1 migrates 13 DSL / test-fixture `.gradle` files and v4-minus-task-6 migrates 1. v4-minus-task-6 retains `<<` / `+=` on `ListProperty<String>` in 10 `build.gradle` files and the one test fixture.
4. **Self-reporting — v1 wins.** v4-minus-task-6 produces no `MIGRATION_NOTES.md` and its REPORT does not acknowledge the five latent regressions. v1's curated 116-line notes file and accurate REPORT make the migration auditable.

### Recommendation

**Accept v1** ([`gradle-10-migration/20260422-1035`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1035)). Nothing from v4-minus-task-6 is worth salvaging: its unique value add over v1 is zero files. The short wall-clock is a product of silent gaps, not efficiency.

The experiment's real value is as evidence that **`help` and `assemble` are not sufficient gates** to catch a lazy-property migration. Five runtime bugs passed both — because `javac` accepts `Object + String` and `String.format(Object)` without complaint, and the two Gradle tasks never exercise the broken configuration paths. The task-06 bulk pass (and the receiver-type ladder inside it) is load-bearing. Any future attempt to streamline the pipeline by letting verify commits do the migration work will produce the same class of latent regressions as v4-minus-task-6, with the same compile-clean disguise.

### Aside — what task 06 actually buys

Looking only at what differs between the two branches (same model, same base, same gates):

- **Property-consumption read sites** — string concatenation, `String.format`, any Java-level API expecting `Object.toString()` — silently produce garbage on `Property<T>` unless explicitly `.get()`-ed. `javac` does not flag them. A reactive path driven only by compile errors will miss every single one. Task 06's bulk pass over all call sites of migrated accessors is the only step that forces the read-side analysis.
- **Groovy DSL operators on `ListProperty`** — `<<`, `+=`, `-=` — are absorbed by Groovy's runtime metaclass dispatch and do not fail configuration time. Only `-=` on a `ListProperty` raised a compile error that v4-minus-task-6's reactive path noticed. The other nine sites with `<<` / `+=` are invisible to `help`/`assemble`.
- **Scanner false-positive triage** — the `MIGRATION_NOTES.md` produced by task 06 is the only artifact that documents *decided non-actions*. Without it, a subsequent reviewer cannot distinguish "considered and left" from "never looked at".

In short, task 06 is not optional, and its absence is not compensated by stronger verification — because the verification we have isn't strong enough to notice.
