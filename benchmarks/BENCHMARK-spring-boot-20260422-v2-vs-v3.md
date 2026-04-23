# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [abstratt/spring-boot](https://github.com/abstratt/spring-boot) (fork of `spring-projects/spring-boot`)
- **Task**: migrate the spring-boot build to the Gradle 10 lazy property API, using the custom Provider API dev distribution
- **Base commit**: [`09ece896`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e) — `Merge branch '4.0.x'` (common ancestor of both runs)
- **Date**: 2026-04-22

## Models under test

Both runs were produced by the same model/tool stack; the `v2` / `v3` labels distinguish two sequential migration attempts on the same base commit a few hours apart.

| Label | Model | Tool | Branch |
|---|---|---|---|
| A (v2) | Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1647`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1647) |
| B (v3) | Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1904`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1904) |

Branch vs. base compare links:

- A: [`09ece896...gradle-10-migration/20260422-1647`](https://github.com/abstratt/spring-boot/compare/09ece896...gradle-10-migration/20260422-1647)
- B: [`09ece896...gradle-10-migration/20260422-1904`](https://github.com/abstratt/spring-boot/compare/09ece896...gradle-10-migration/20260422-1904)

## Executive summary

**Run B (v3) wins on all four primary criteria.** Both runs produce a branch that self-reports green on `./gradlew help` and `./gradlew assemble`, and both end with the same two migration bugs against the `ResolveMainClassName` custom task reverted during `assemble`. The gap is in what happens *before* the verify steps: Run A's migrate commit carries five additional incorrect rewrites (three in `JavaConventions.java`, two in `MavenPluginPlugin.java`) that the verify-help commit had to revert; skips every Cat-C Groovy DSL operator mutation (`jvmArgs +=`, `options.compilerArgs <<`) except the one that crashed help; deletes — rather than repairs — the broken `docs.gradle.org/$gradle.gradleVersion/javadoc` link in the plugin's javadoc config; and commits a 1432-line raw scanner dump as `MIGRATION_NOTES.md`. Run B caught those same apply_migrations.py false positives inline, rewrote the DSL operators proactively, preserved the javadoc link (updated to `docs.gradle.org/current/javadoc`), and shipped a curated 95-line punch list.

### Headline metrics

| Metric | A (v2) | B (v3) |
|---|---|---|
| Wall-clock elapsed (per report) | 15m 15s (16:51:35 → 17:06:50) | 14m 41s (19:06:37 → 19:21:18) |
| Files in migrate commit (excl. `MIGRATION_NOTES.md`) | 17 | 28 |
| Files in verify-help commit | 4 | 4 |
| Files in verify-assemble commit | 3 | 3 |
| `./gradlew help` passed at migrate commit | ❌ (broke on `options.compilerArgs -=`; 4 Cat-A catch-ups + 5 migration-bug reverts) | ❌ (4 Cat-A catch-ups; 0 migration-bug reverts) |
| `./gradlew assemble` passed at migrate commit | ❌ (2 migration-bug reverts + 1 behavior-change workaround) | ❌ (2 migration-bug reverts; 1 URL update) |
| Groovy syntax errors introduced | 0 | 0 |
| Semantic regressions (`from` ≠ `setFrom`, etc.) | 7 (see Behavior Preservation) | 2 (see Behavior Preservation) |
| Compile errors from `.get()` on non-Gradle types | 0 | 0 |
| `buildSrc/` migrated | ✅ | ✅ |
| Cat-C DSL operator mutations migrated in task 06 | 1 of ~12 sites | 12 of ~12 sites |
| Assistant trailer key correct (`Assistant:` vs `A:`) | ❌ (4 of 5 commits use `A:`) | ❌ (4 of 5 commits use `A:`) |
| Trailer contents (model/tool identity filled) | ✅ | ✅ |
| Javadoc link behavior preserved | ❌ (link deleted) | ✅ (URL repointed) |
| `MIGRATION_NOTES.md` is a curated punch list | ❌ (1432-line raw scanner dump) | ✅ (95-line summary) |

## Methodology

Per-task commit mapping (same pipeline on both branches — the April 2026 "verify help" split was already in place for both):

| Task | Subject | Run A (v2) | Run B (v3) |
|---|---|---|---|
| 04 Swap Distribution | `Swap Gradle Distribution` | [`9549f2e4`](https://github.com/abstratt/spring-boot/commit/9549f2e47c1f17948e98f7a7c633d80280e8abf1) | [`4908f07e`](https://github.com/abstratt/spring-boot/commit/4908f07e1b6f52bb65577ddd0f434a4e948c86ce) |
| 06 Migrate | `Migrate Build Scripts and Gradle API Usages` | [`c1216c30`](https://github.com/abstratt/spring-boot/commit/c1216c30f876e596dac788a50fa1f01f7513c882) | [`d264526c`](https://github.com/abstratt/spring-boot/commit/d264526ca7f55f671f28c854dbdfdcab569f9e63) |
| 07 Verify help | `Verify with ./gradlew help` | [`bc4cd2c5`](https://github.com/abstratt/spring-boot/commit/bc4cd2c5d1d60eb0a923d998526e0019835cd7c5) | [`e5d2f7c5`](https://github.com/abstratt/spring-boot/commit/e5d2f7c5b67223ff9a22857b0126b41a009b2ac5) |
| 08 Verify assemble | `Verify with ./gradlew assemble` | [`6bdbe565`](https://github.com/abstratt/spring-boot/commit/6bdbe5656b1b699f5875845721f7785841ea9821) | [`ea31a6c0`](https://github.com/abstratt/spring-boot/commit/ea31a6c004367d81f0fc38eb6e6ca3222b72d38c) |
| 09 Report | `Generate Report` | [`25024949`](https://github.com/abstratt/spring-boot/commit/2502494934fe7deb9d6091dfb0e8c983116def79) | [`58cd7c3a`](https://github.com/abstratt/spring-boot/commit/58cd7c3a8a138725ec2ead203396feb6f6d58a75) |

The wrapper swap diff is byte-identical across both runs (same custom distribution URL, `validateDistributionUrl=false`, same `gradle-9.4.1-bin.zip` → Provider API dev-distribution swap). Every divergence below therefore starts at task 06.

## Results by criterion

### 1. Behavior preservation

Three concrete ways Run A changes observable behavior that Run B does not.

**(1a) Five spurious `apply_migrations.py` rewrites leaked into Run A's migrate commit.** Each of these targets a receiver whose class is *not* in `migration-data.json` — only the property name collides with a migrated one. The scanner confirms by import, not receiver type, so it confirms both. Run B's migrate commit doesn't carry any of them; Run A's verify-help commit reverts them all.

[`JavaConventions.java` in A](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java) (lines 291, 372, 379):

```diff
-		project.getTasks().withType(Format.class, (Format) -> Format.setEncoding("UTF-8"));
+		project.getTasks().withType(Format.class, (Format) -> Format.getEncoding().set("UTF-8"));
```

```diff
 				TaskProvider<CheckAotFactories> checkAotFactories = project.getTasks()
 					.register("checkAotFactories", CheckAotFactories.class, (task) -> {
-						task.setSource(main.getResources());
+						task.getSource().set(main.getResources());
```

`io.spring.javaformat.gradle.tasks.Format` is a third-party task; `CheckAotFactories` / `CheckSpringFactories` extend the in-tree `CheckFactoriesFile` base class with their own `setSource(Object)`. Neither is lazy-migrated.

[`MavenPluginPlugin.java` in A](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/buildSrc/src/main/java/org/springframework/boot/build/mavenplugin/MavenPluginPlugin.java) (lines 238, 290):

```diff
 		return project.getTasks().register("syncHelpMojoInputs", Sync.class, (task) -> {
-			task.setDestinationDir(helpMojoDir.get().getAsFile());
+			task.getDestinationDir().set(helpMojoDir.get().getAsFile());
```

`Sync.setDestinationDir(File)` is inherited from `AbstractCopyTask` and is not in `migration-data.json`. Run A's [verify-help commit reverts all five](https://github.com/abstratt/spring-boot/commit/bc4cd2c5d1d60eb0a923d998526e0019835cd7c5); Run B never introduced them — its [`MIGRATION_NOTES.md`](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/MIGRATION_NOTES.md) enumerates each one in a "Broken rewrites by `apply_migrations.py` that had to be reverted" section, meaning Run B ran the receiver-type ladder on apply_migrations.py's output before committing.

**(1b) Run A *deletes* a Gradle Javadoc link; Run B *repairs* it.** In [`build-plugin/spring-boot-gradle-plugin/build.gradle`](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/build-plugin/spring-boot-gradle-plugin/build.gradle), the original links `https://docs.gradle.org/$gradle.gradleVersion/javadoc`, which 404s for the dev distribution's `9.5.0-20260204101228+0000` version.

[Run A verify-assemble](https://github.com/abstratt/spring-boot/commit/6bdbe5656b1b699f5875845721f7785841ea9821):

```diff
 		windowTitle = "Spring Boot Gradle Plugin ${project.version} API"
-		links "https://docs.gradle.org/$gradle.gradleVersion/javadoc"
 		links "https://docs.oracle.com/en/java/javase/17/docs/api"
```

[Run B verify-assemble](https://github.com/abstratt/spring-boot/commit/ea31a6c004367d81f0fc38eb6e6ca3222b72d38c):

```diff
 		windowTitle = "Spring Boot Gradle Plugin ${project.version} API"
-		links "https://docs.gradle.org/$gradle.gradleVersion/javadoc"
+		links "https://docs.gradle.org/current/javadoc"
 		links "https://docs.oracle.com/en/java/javase/17/docs/api"
```

Run A's version silently drops the Gradle javadoc cross-reference from the published plugin docs. Run B preserves observable behavior (link still present, pointing at a URL that resolves). Per `CONTEXT.md` §"Code Change Guidelines" — "Do not change observable functionality" — Run A is a regression.

**(1c) Both runs share one migration bug, equally caught.** Both [rewrote `resolveMainClassName.setClasspath(classpath)` to `.getClasspath().setFrom(...)` in the migrate commit](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/JavaPluginAction.java) at lines 120/147, and both reverted in verify-assemble:

```diff
-						resolveMainClassName.getClasspath().setFrom(classpath);
+						resolveMainClassName.setClasspath(classpath);
```

`ResolveMainClassName` is a custom `DefaultTask` that owns its own `setClasspath(Object)`. This is a wash.

**(1d) One formatter-driven cosmetic reformat on each side.** Both verify-help commits reflow `checkstyleDependencies.add(...)` in `JavaConventions.java` — Run A and Run B alike. Run B's report discloses that `./gradlew -p buildSrc format` was auto-applied; Run A is silent on the cause. Minor protocol violation for both ("Do not make cosmetic changes"), equal in weight.

### 2. Lazy vs. eager

Both runs land on the same solutions for the interesting sites. The only distinguishable difference is comment discipline.

**`BootRun.java` self-referential classpath and jvmArgs.** Both correctly snapshot the FileCollection with `.getFiles()` (required by the rule in `tasks/06-migrate-build-scripts.md` — "`.getFiles()` is correct only to break an explicit self-reference — if so, require a comment explaining it"), and both use `.set(.get())` for `jvmArgs`:

[Run A](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java):

```diff
+		// Snapshot the current classpath via getFiles() to avoid a self-referential provider.
+		getClasspath()
+			.setFrom(getProject().files(srcDirs, getClasspath().getFiles()).filter((file) -> !file.equals(resourcesDir)));
 ...
-			setJvmArgs(getJvmArgs());
+			// Resolve and re-set jvmArgs to detach it from its convention before appending.
+			getJvmArgs().set(getJvmArgs().get());
```

[Run B](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java):

```diff
+		// Snapshot the existing classpath entries before replacing, to avoid a circular reference
+		// now that getClasspath() returns a ConfigurableFileCollection.
+		getClasspath().setFrom(
+				getProject().files(srcDirs, getClasspath().getFiles()).filter((file) -> !file.equals(resourcesDir)));
 ...
-			setJvmArgs(getJvmArgs());
+			getJvmArgs().set(getJvmArgs().get());
```

Run A comments *both* self-reference sites. Run B comments the classpath site but leaves the `jvmArgs().set(.get())` self-reference uncommented. Minor edge to A.

**`ApplicationPluginAction.java` inside `project.provider(...)`:** Both realize `javaApplication.getApplicationName().get() + "-boot"` inside a `Provider` lambda — the `.get()` call is safe there because the surrounding provider is itself lazy. Equivalent.

**`configureUtf8Encoding` and `configureParametersCompilerArg`:** Both migrate `getEncoding() == null` to `!isPresent()` and both rewrite the `compilerArgs` site so a new arg reaches the `ListProperty`. The specific shapes differ slightly — Run A types the local as `ListProperty<String>`, Run B keeps `List<String>` and calls `.add(...)` on the underlying `ListProperty` — both lazy-correct. Equivalent.

No `.get()` calls inside configuration blocks where `map`/`flatMap` would have worked were found in either branch.

### 3. Coverage

Both runs migrate `buildSrc/` equally (`JavaConventions.java`, `RepositoryTransformersExtension.java`, `ConfigureJavadocLinks.java`, `mavenplugin/MavenExec.java`, and `test/{Docker,Integration,System}TestPlugin.java`). Neither run misses the `org.springframework.boot.build` package tree inside `buildSrc/` — both correctly worked around the `scan_usages.py` default that excludes directories named `build`.

The discriminator is **Cat-C Groovy DSL operator mutations on now-lazy `ListProperty<String>` / jvmArgs:**

Run B's migrate commit rewrote these proactively across 12 sites:

- `jvmArgs += "..."` → `jvmArgs.add("...")` in [`core/spring-boot-autoconfigure/build.gradle`](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/core/spring-boot-autoconfigure/build.gradle), `core/spring-boot-testcontainers/build.gradle`, `integration-test/spring-boot-integration-tests/build.gradle`, `loader/spring-boot-loader-tools/build.gradle`, and the six `module/spring-boot-*/build.gradle` scripts (`jetty`, `security`, `servlet`, `tomcat`, `webflux`, `websocket`).
- `options.compilerArgs << '...'` → `options.compilerArgs.add('...')` in [`core/spring-boot/build.gradle`](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/core/spring-boot/build.gradle) and the `JavaPluginActionIntegrationTests-...AdditionalCompilerFlags.gradle` test fixture.
- `options.compilerArgs -= ['-Werror']` → `options.compilerArgs.set(options.compilerArgs.get() - ['-Werror'])` in `loader/spring-boot-loader-tools/build.gradle`.

Run A migrated **only** the `-=` case, and only because verify-help broke on it. Every other site still carries the pre-Gradle-10 operator syntax at the branch tip:

[`core/spring-boot/build.gradle` on branch A](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260422-1647/core/spring-boot/build.gradle) (lines 91–92):

```groovy
tasks.named("compileJava") {
	options.compilerArgs << '-Alog4j.graalvm.groupId=org.springframework.boot'
	options.compilerArgs << '-Alog4j.graalvm.artifactId=spring-boot-log4j'
}
```

[`module/spring-boot-tomcat/build.gradle` on branch A](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260422-1647/module/spring-boot-tomcat/build.gradle) (line 85):

```groovy
	jvmArgs += "--add-opens=java.base/java.net=ALL-UNNAMED"
```

Empirically these don't block `help`/`assemble` — Gradle's Groovy DSL still honors `leftShift` on `ListProperty` via an extension module (that's also why `-=` broke but `<<` didn't). But they are explicitly called out as rewrites the migration should perform, and leaving them behind creates a reviewable-code gap: downstream readers can't tell which operator mutations were audited and intentional vs. which were simply missed.

### 4. Self-reporting

**Assistant trailer.** Both runs fill in a real model identifier (`claude-opus-4-7[1m]`) and friendly name — neither left the `<<Tool Name>> / <<Friendly Model Name>> / <<model-id>>` placeholder. However, both use the wrong **key** on 4 of 5 commits:

```
A: Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]
```

instead of the required

```
Assistant: Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]
```

Only the `Generate Report` commit on each branch has the correct `Assistant:` key. Both runs are equally non-compliant here (a protocol breach that affects grep-ability of commit metadata).

**`MIGRATION_NOTES.md` at repo root.** Run A committed a [1432-line raw scan dump](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/MIGRATION_NOTES.md), composed almost entirely of Cat-B false positives (`Project.getConfigurations()`, `Task.getName()`, `Project.getVersion()` collisions on non-migrated receivers). Run A's report acknowledges this with "most entries are `[Cat-B]` false positives ... A human pass can prune it" — i.e. it commits the noise and asks the user to clean up. Run B committed a [95-line curated punch list](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/MIGRATION_NOTES.md) structured as four sections: handled in this commit, incorrect rewrites reverted, CONFIRMED scan hits judged non-applicable with per-site reasoning, and expected follow-up. Run B's file is actionable; Run A's is a log.

**Per-run `REPORT-*.md`.** Both are accurate about scope ("only `help` and `assemble` verified; deprecations ignored"). Run B's report is substantially more thorough (163 vs. 68 lines) and — crucially — distinguishes between migrations applied in task 06, migration-bug reverts, and build-driven fixes in tasks 07/08. Run A's report narrates "Reverted spurious `setDestinationDir`/`setSource` rewrites on Sync and the custom `CheckFactoriesFile`/`ResolveMainClassName` tasks" without disclosing that those reverts happened *in task 07*, not during task 06 — conflating what was committed cleanly with what had to be rescued.

## Verification cost — the rescue effect

Both runs ran the same verify steps; the breakdown of what each step had to fix:

| Run | Commit | Files | Legitimate Cat-A catch-ups | Legitimate Cat-C catch-ups | Behavior changes / URL edits | Migration-bug reverts | Cosmetic (formatter) |
|---|---|---:|---:|---:|---:|---:|---:|
| A | [verify-help `bc4cd2c5`](https://github.com/abstratt/spring-boot/commit/bc4cd2c5d1d60eb0a923d998526e0019835cd7c5) | 4 | 3 (`pom.setPackaging`, `options.setIncremental`, `repository.getUrl().get()`) | 1 (`options.compilerArgs -=`) | 0 | **5** (`Format.setEncoding`, 2× `Check*.setSource`, 2× `Sync.setDestinationDir`) | 1 (checkstyle dep reflow) |
| A | [verify-assemble `6bdbe565`](https://github.com/abstratt/spring-boot/commit/6bdbe5656b1b699f5875845721f7785841ea9821) | 3 | 2 (`isPresent`/`ListProperty<String>` fix in `JavaPluginAction.java`, `SpringBootAotPlugin.setClasspath`) | 0 | **1 (link deleted)** | 2 (`resolveMainClassName.setClasspath` × 2) | 0 |
| B | [verify-help `e5d2f7c5`](https://github.com/abstratt/spring-boot/commit/e5d2f7c5b67223ff9a22857b0126b41a009b2ac5) | 4 | 4 (`pom.setPackaging`, `options.setIncremental`, `repository.getUrl().get()` × 2, `mavenArtifact.setClassifier`) | 0 | 0 | **0** | 1 (checkstyle dep reflow) |
| B | [verify-assemble `ea31a6c0`](https://github.com/abstratt/spring-boot/commit/ea31a6c004367d81f0fc38eb6e6ca3222b72d38c) | 3 | 2 (`isPresent`/`compilerArgs.get().contains` fix, `SpringBootAotPlugin.setClasspath`) | 0 | 1 (link URL updated, not deleted) | 2 (`resolveMainClassName.setClasspath` × 2) | 0 |

**Migration-bug revert totals: A = 7, B = 2.** Both hit the same `ResolveMainClassName` pair at `assemble` time. Run A additionally carried five receiver-type mis-classifications into `MIGRATION_NOTES.md`'s own "Broken rewrites" section — which Run A's verify-help had to untangle, Run B caught pre-commit.

A clean migration lands "0–3 files of verify-time fixes"; Run B is on the high side of clean (7 files touched across verify commits, but 5 are genuine Cat-A/edge-case fixes and 2 are the shared `ResolveMainClassName` miss). Run A's 7 files are mostly occupied with reverts, i.e. verification is functioning as a rescue step rather than as verification.

## Verdict

1. **Behavior preservation → Run B.** A has 5 additional migration-bug rewrites in the migrate commit ([`c1216c30`](https://github.com/abstratt/spring-boot/commit/c1216c30f876e596dac788a50fa1f01f7513c882) vs [`d264526c`](https://github.com/abstratt/spring-boot/commit/d264526ca7f55f671f28c854dbdfdcab569f9e63)) and deletes the Gradle javadoc link in [`6bdbe565`](https://github.com/abstratt/spring-boot/commit/6bdbe5656b1b699f5875845721f7785841ea9821) where B preserves it in [`ea31a6c0`](https://github.com/abstratt/spring-boot/commit/ea31a6c004367d81f0fc38eb6e6ca3222b72d38c).

2. **Lazy vs. eager → tie, slight edge to A.** Both runs pick the same lazy shapes across `BootRun.java`, `configureUtf8Encoding`, `configureParametersCompilerArg`, and `ApplicationPluginAction.java`. A comments both `BootRun` self-references; B comments only the classpath case.

3. **Coverage → Run B.** B migrates 12 Cat-C DSL operator sites ([across `core/`, `module/`, `integration-test/`, `loader/` and the `JavaPluginActionIntegrationTests-...` fixture](https://github.com/abstratt/spring-boot/commit/d264526ca7f55f671f28c854dbdfdcab569f9e63)); A migrates 1 (the `-=` that happened to break verify-help), leaving 11 `<<` / `+=` sites unreviewed on the branch tip.

4. **Self-reporting → Run B.** Both use the wrong trailer key (`A:` vs `Assistant:`) equally. B's [`MIGRATION_NOTES.md`](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/MIGRATION_NOTES.md) is a 95-line punch list; A's [`MIGRATION_NOTES.md`](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/MIGRATION_NOTES.md) is a 1432-line raw scanner dump. B's [`REPORT-20260422-1904.md`](https://github.com/abstratt/spring-boot/blob/58cd7c3a8a138725ec2ead203396feb6f6d58a75/REPORT-20260422-1904.md) distinguishes legitimate verify-time fixes from migration-bug reverts; A's [`REPORT-20260422-1647.md`](https://github.com/abstratt/spring-boot/blob/2502494934fe7deb9d6091dfb0e8c983116def79/REPORT-20260422-1647.md) conflates them.

**Recommendation: accept Run B (v3).** There is nothing to salvage from Run A — every migration Run B performs is a strict superset (or equivalent) of Run A's, and the places where Run A differs (Cat-C operators left behind, Gradle javadoc link deleted, noise dumped into `MIGRATION_NOTES.md`, 5 extra `apply_migrations.py` false positives leaked through) are strictly worse. The single advantage — Run A's extra comment on the `jvmArgs().set(.get())` self-reference — can be ported in a one-line follow-up edit on top of Run B if that level of comment hygiene is wanted. Before merging Run B, separately correct the `A:` → `Assistant:` trailer on the four non-report commits; both runs share that defect.
