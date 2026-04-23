# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [abstratt/spring-boot](https://github.com/abstratt/spring-boot) (fork of `spring-projects/spring-boot`)
- **Task**: migrate the spring-boot build to the Gradle 10 lazy property API using the custom Provider API dev distribution
- **Base commit**: [`09ece896`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e) — `Merge branch '4.0.x'` (common ancestor of both runs)
- **Date**: 2026-04-22

## Models under test

Both runs used the same model/tool stack; the `v3` / `v4` labels distinguish two sequential migration attempts on the same base, 42 minutes apart.

| Label | Model | Tool | Branch |
|---|---|---|---|
| A (v3) | Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1904`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1904) |
| B (v4) | Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1946`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1946) |

Branch vs. base compare links:

- A: [`09ece896...gradle-10-migration/20260422-1904`](https://github.com/abstratt/spring-boot/compare/09ece896...gradle-10-migration/20260422-1904)
- B: [`09ece896...gradle-10-migration/20260422-1946`](https://github.com/abstratt/spring-boot/compare/09ece896...gradle-10-migration/20260422-1946)

## Executive summary

**Run A (v3) wins overall, 2-1-1 across the four criteria.** Both runs end with `./gradlew help` and `./gradlew assemble` green, and in the end-state diff only six files distinguish the tips: `MIGRATION_NOTES.md`, `REPORT-*.md`, the plugin's javadoc block, `JavaPluginAction.java`, `BootArchiveSupport.java`, and `BootRun.java`. The gap that matters is process integrity: Run B crams more Cat-A migrations into the task-06 commit (setPackaging, setIncremental, setClassifier, `MavenArtifactRepository.url`, `SpringBootAotPlugin.setClasspath`, the `isPresent` / `ListProperty<String>` rewrites in `JavaPluginAction`) — work Run A defers to verify-help / verify-assemble — but in the process it replays five of the same `apply_migrations.py` receiver-type misses that plagued the v2 run (`Format.setEncoding`, `CheckAotFactories.setSource` × 2, `Sync.setDestinationDir` × 2). Run B's verify-help commit is therefore dominated by reverts (5 of 6 edits); Run A's is dominated by legitimate catch-ups. On top of that, Run B deletes the Gradle javadoc link (where Run A repoints it), commits the 1432-line raw scanner dump as `MIGRATION_NOTES.md` (where Run A ships a 95-line curated punch list), and uses the wrong `A:` trailer on *every* commit (where Run A at least gets `Assistant:` right on the report commit). Run B does have two real micro-advantages: `BootArchiveSupport.getMetadataCharset().getOrNull()` preserves the original nullable-String semantics where Run A's `.get()` would throw on an unset property, and Run B comments both `BootRun` self-references (Run A comments only the classpath one).

### Headline metrics

| Metric | A (v3) | B (v4) |
|---|---|---|
| Wall-clock elapsed (per report) | 14m 41s (19:06:37 → 19:21:18) | 17m 03s (19:49:45 → 20:06:48) |
| Files in migrate commit (excl. `MIGRATION_NOTES.md`) | 28 | 33 |
| Files in verify-help commit | 4 | 2 |
| Files in verify-assemble commit | 3 | 2 |
| Cat-A sites covered inside the migrate commit | partial (defers 6 sites to verify-help/assemble) | full (handles all sites in task 06) |
| Migration-bug reverts inside verify commits | 2 (shared `ResolveMainClassName` × 2) | 7 (`ResolveMainClassName` × 2 + `Format.setEncoding` + `CheckAotFactories.setSource` + `CheckSpringFactories.setSource` + `Sync.setDestinationDir` × 2) |
| Cat-C DSL operator mutations migrated in task 06 | 12 of 12 | 12 of 12 |
| `buildSrc/` migrated | ✅ | ✅ |
| Groovy syntax errors introduced | 0 | 0 |
| Compile errors from `.get()` on non-Gradle types | 0 | 0 |
| Gradle javadoc link behavior preserved | ✅ (URL repointed to `current/javadoc`) | ❌ (link deleted, replaced with a comment) |
| `BootArchiveSupport.metadataCharset` preserves nullable semantics | ❌ (`.get()` — throws if unset) | ✅ (`.getOrNull()`) |
| `MIGRATION_NOTES.md` is a curated punch list | ✅ (95-line summary) | ❌ (1432-line raw scanner dump) |
| Assistant trailer contents filled in | ✅ | ✅ |
| Assistant trailer uses the required `Assistant:` key | partial (correct on `Generate Report`; `A:` on the other 4) | ❌ (all 5 commits use `A:`) |

## Methodology

Per-task commit mapping:

| Task | Subject | Run A (v3) | Run B (v4) |
|---|---|---|---|
| 04 Swap Distribution | `Swap Gradle Distribution` | [`4908f07e`](https://github.com/abstratt/spring-boot/commit/4908f07e1b6f52bb65577ddd0f434a4e948c86ce) | [`2fd09961`](https://github.com/abstratt/spring-boot/commit/2fd09961cab392c5ff66e03324a73b9b4c4fb6ce) |
| 06 Migrate | `Migrate Build Scripts and Gradle API Usages` | [`d264526c`](https://github.com/abstratt/spring-boot/commit/d264526ca7f55f671f28c854dbdfdcab569f9e63) | [`ab4b6c72`](https://github.com/abstratt/spring-boot/commit/ab4b6c727dfc8d2378e237fecf794250b871ba8e) |
| 07 Verify help | `Verify with ./gradlew help` | [`e5d2f7c5`](https://github.com/abstratt/spring-boot/commit/e5d2f7c5b67223ff9a22857b0126b41a009b2ac5) | [`d300d56d`](https://github.com/abstratt/spring-boot/commit/d300d56d2da5f5d1a747ca289376012f100841f1) |
| 08 Verify assemble | `Verify with ./gradlew assemble` | [`ea31a6c0`](https://github.com/abstratt/spring-boot/commit/ea31a6c004367d81f0fc38eb6e6ca3222b72d38c) | [`8b19722b`](https://github.com/abstratt/spring-boot/commit/8b19722bdcb84c18ecb050c252dced81c74eac28) |
| 09 Report | `Generate Report` | [`58cd7c3a`](https://github.com/abstratt/spring-boot/commit/58cd7c3a8a138725ec2ead203396feb6f6d58a75) | [`b2e74a2a`](https://github.com/abstratt/spring-boot/commit/b2e74a2ab82696e00bc126ba85c5fd7d8d9883c9) |

Every pipeline task commit is present on both branches. The wrapper swap in task 04 is byte-identical.

## Results by criterion

### 1. Behavior preservation

**(1a) Five extra `apply_migrations.py` false-positive rewrites leaked into Run B's migrate commit.** Each targets a receiver whose class is *not* in `migration-data.json` — only the property name collides with a migrated one. Run A caught and removed these pre-commit; Run B committed them and then reverted during verify-help.

[`JavaConventions.java` in B's migrate commit](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java) (lines 291, 372, 379):

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

`io.spring.javaformat.gradle.tasks.Format` is a third-party task; `CheckAotFactories` / `CheckSpringFactories` extend the in-tree `CheckFactoriesFile` with their own `setSource(Object)`. Neither is lazy-migrated.

[`MavenPluginPlugin.java` in B's migrate commit](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/buildSrc/src/main/java/org/springframework/boot/build/mavenplugin/MavenPluginPlugin.java) (lines 238, 290):

```diff
 		return project.getTasks().register("syncHelpMojoInputs", Sync.class, (task) -> {
-			task.setDestinationDir(helpMojoDir.get().getAsFile());
+			task.getDestinationDir().set(helpMojoDir.get().getAsFile());
```

`Sync.setDestinationDir(File)` is inherited from `AbstractCopyTask` and is not in `migration-data.json`.

[Run B's verify-help commit `d300d56d`](https://github.com/abstratt/spring-boot/commit/d300d56d2da5f5d1a747ca289376012f100841f1) reverts all five. Run A's migrate commit never touched any of them — its [`MIGRATION_NOTES.md`](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/MIGRATION_NOTES.md) explicitly enumerates them in a "Broken rewrites by `apply_migrations.py` that had to be reverted" section. Run B's [report](https://github.com/abstratt/spring-boot/blob/b2e74a2ab82696e00bc126ba85c5fd7d8d9883c9/REPORT-20260422-1946.md) lists the same reverts under "Hand edits of note" without disclosing that they happened in task 07 rather than inline.

**(1b) Javadoc link — Run A repoints, Run B deletes.** The original `build-plugin/spring-boot-gradle-plugin/build.gradle` linked `https://docs.gradle.org/$gradle.gradleVersion/javadoc`, which 404s on the dev-distribution's `9.5.0-…` version.

[Run A verify-assemble `ea31a6c0`](https://github.com/abstratt/spring-boot/commit/ea31a6c004367d81f0fc38eb6e6ca3222b72d38c):

```diff
 		windowTitle = "Spring Boot Gradle Plugin ${project.version} API"
-		links "https://docs.gradle.org/$gradle.gradleVersion/javadoc"
+		links "https://docs.gradle.org/current/javadoc"
 		links "https://docs.oracle.com/en/java/javase/17/docs/api"
```

[Run B verify-assemble `8b19722b`](https://github.com/abstratt/spring-boot/commit/8b19722bdcb84c18ecb050c252dced81c74eac28):

```diff
 		windowTitle = "Spring Boot Gradle Plugin ${project.version} API"
-		links "https://docs.gradle.org/$gradle.gradleVersion/javadoc"
+		// Gradle dev-distribution versions have no published javadoc; link only the JDK.
 		links "https://docs.oracle.com/en/java/javase/17/docs/api"
```

Run A preserves observable behavior — a Gradle javadoc cross-reference is still emitted. Run B silently drops it; the explanatory comment softens the blow but per CONTEXT.md §"Code Change Guidelines" — "Do not change observable functionality" — this is a small regression.

**(1c) `BootArchiveSupport.getMetadataCharset` nullability — Run B wins.** The pre-migration code read `String encoding = jar.getMetadataCharset();`, where `getMetadataCharset()` returned a nullable `String`.

[Run A in migrate commit](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java):

```diff
-		String encoding = jar.getMetadataCharset();
+		String encoding = jar.getMetadataCharset().get();
```

`.get()` throws `IllegalStateException` if the property has no value — a semantic regression when the property is unset. [Run B in migrate commit](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java):

```diff
-		String encoding = jar.getMetadataCharset();
+		String encoding = jar.getMetadataCharset().getOrNull();
```

`.getOrNull()` preserves the original nullable semantics. Small but real win for Run B. (Same idea applies to `configureUtf8Encoding` in `JavaPluginAction.java`: Run A's `!getEncoding().isPresent()` is idiomatic; Run B's `getEncoding().getOrNull() == null` is more literal to the pre-migration `== null` check. Either works.)

**(1d) Both runs share the `ResolveMainClassName.setClasspath` bug.** Both migrate commits incorrectly rewrite the custom task's `setClasspath(classpath)` to `.getClasspath().setFrom(classpath)` at lines 120/147 of `JavaPluginAction.java`; both revert in verify-assemble. Wash.

**(1e) Both verify-help commits include the same formatter-driven reflow of `checkstyleDependencies.add(...)`.** Equal on both sides.

### 2. Lazy vs. eager

Both runs converge on the same fundamental shapes for self-reference and lazy wiring; the only visible gap is comment discipline on `BootRun`.

[Run A `BootRun.java` tip](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260422-1904/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java):

```java
		// Snapshot the existing classpath entries before replacing, to avoid a circular reference
		// now that getClasspath() returns a ConfigurableFileCollection.
		getClasspath().setFrom(
				getProject().files(srcDirs, getClasspath().getFiles()).filter((file) -> !file.equals(resourcesDir)));
...
			getJvmArgs().set(getJvmArgs().get());
```

[Run B `BootRun.java` tip](https://github.com/abstratt/spring-boot/blob/gradle-10-migration/20260422-1946/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java):

```java
		// Snapshot the current classpath files before reassigning to avoid a circular reference.
		getClasspath().setFrom(getProject().files(srcDirs, getClasspath().getFiles())
				.filter((file) -> !file.equals(resourcesDir)));
...
			// Snapshot current jvmArgs before reassigning to avoid a circular reference.
			getJvmArgs().set(new java.util.ArrayList<>(getJvmArgs().get()));
```

Run B comments both self-reference sites and adds an explicit defensive copy for `jvmArgs` (`new ArrayList<>(...)`), matching the existing self-reference rule in `CONTEXT.md` that requires a comment whenever `.getFiles()` / `.get()` snapshots are used to break a cycle. Run A comments the classpath case but leaves `getJvmArgs().set(getJvmArgs().get())` uncommented. No other lazy-vs-eager divergence surfaced across `ApplicationPluginAction.java`, `configureUtf8Encoding`, `configureParametersCompilerArg`, or `SpringBootAotPlugin.java` — all lazy shapes are equivalent.

Minor edge to Run B.

### 3. Coverage

Both runs migrate `buildSrc/` and `build-plugin/` to the same end state; both work around the scanner-excludes-`build/` caveat; both migrate all 12 Cat-C DSL operator mutations (`jvmArgs +=`, `options.compilerArgs <<`, `options.compilerArgs -=`) inside the migrate commit.

The discriminator is **how much Cat-A work the migrate commit itself carries.** Run B is more thorough; Run A defers six sites to verify-help/assemble:

| Site | Run A (v3) | Run B (v4) |
|---|---|---|
| `MavenPublication.pom → pom.setPackaging` in `MavenPluginPlugin.java` | deferred to verify-help | migrated in task 06 |
| `MavenArtifact.setClassifier` in `ConsumableContentContribution.java` | deferred to verify-help | migrated in task 06 |
| `MavenArtifactRepository.getUrl()` in `MavenMetadataVersionResolver.java` (2 call sites) | deferred to verify-help | migrated in task 06 |
| `CompileOptions.setIncremental(false)` in `ConfigurationPropertiesPlugin.java` | deferred to verify-help | migrated in task 06 |
| `SpringBootAotPlugin` `ProcessAot` / `ProcessTestAot` `setClasspath` (2 call sites) | deferred to verify-assemble | migrated in task 06 |
| `JavaPluginAction` `configureUtf8Encoding` / `configureParametersCompilerArg` | deferred to verify-assemble | migrated in task 06 |

Run B's migrate commit therefore presents closer to the final state when reviewed in isolation — a legitimate coverage win. The cost (paid in criterion 1) is five false-positive rewrites Run B had to revert in verify-help. Net: Run B does a better job of *finding* the Cat-A sites but a worse job of *triaging* which scanner-confirmed sites are genuine migrations vs. receiver-name collisions.

### 4. Self-reporting

**Assistant trailer.** Both runs fill in a real model identifier (`claude-opus-4-7[1m]`) on every commit, so neither leaves template placeholders. But both use the wrong **key**: `A:` instead of the mandatory `Assistant:`. Run A gets this right on the `Generate Report` commit only; Run B uses `A:` on all 5 commits. Run A is less-wrong (4 of 5 commits non-compliant) but neither is compliant.

**`MIGRATION_NOTES.md` at repo root.**

- [Run A — 95 lines](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/MIGRATION_NOTES.md): four curated sections (handled-in-this-commit, broken rewrites reverted, remaining CONFIRMED scan hits judged non-applicable with per-site reasoning, expected follow-up).
- [Run B — 1432 lines](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/MIGRATION_NOTES.md): the raw `apply_migrations.py` deferral log, one entry per scanner hit with the boilerplate "defer to task 07" reason attached to every Cat-B entry. Run B's own report acknowledges it covers "558 scanner-flagged sites" — i.e. it commits the log, not an audit.

Same delta as the v2-vs-v3 comparison: Run A is actionable, Run B is logs-as-docs.

**Per-run `REPORT-*.md`.** Run A's [`REPORT-20260422-1904.md`](https://github.com/abstratt/spring-boot/blob/58cd7c3a8a138725ec2ead203396feb6f6d58a75/REPORT-20260422-1904.md) is 163 lines, structured by task number (build infra, build-script / plugin source migration, Cat-C DSL, incorrect rewrites reverted, build-driven fixes in tasks 07/08). Run B's [`REPORT-20260422-1946.md`](https://github.com/abstratt/spring-boot/blob/b2e74a2ab82696e00bc126ba85c5fd7d8d9883c9/REPORT-20260422-1946.md) is 63 lines — covers the same ground at higher level but doesn't distinguish what Run B did in task 06 vs. what task 07 had to rescue. Run B's "Auto-rewrites for `JavaConventions.java` that needed reverting" bullet, for example, lists the 5 migration bugs but doesn't flag that they survived into a committed migrate commit before verify-help pulled them back.

Run B also discloses a workflow anomaly: "JDK 25-tem was required for `assemble` because `buildSrc` enforces `BUILD_JAVA_VERSION = 25`. Task 02 installed JDK 21 and used it through `help`; the `assemble` run swapped to JDK 25-tem." Run A does not mention any such swap. Whether that's a silent omission on A's part or a difference in how each run interpreted task 02 is unclear — noting it here for the record, not as a verdict input.

## Verification cost — the rescue effect

| Run | Commit | Files | Legitimate Cat-A catch-ups | Legitimate Cat-C catch-ups | Behavior changes / URL edits | Migration-bug reverts | Cosmetic (formatter) |
|---|---|---:|---:|---:|---:|---:|---:|
| A | [verify-help `e5d2f7c5`](https://github.com/abstratt/spring-boot/commit/e5d2f7c5b67223ff9a22857b0126b41a009b2ac5) | 4 | 4 (`pom.setPackaging`, `options.setIncremental`, `repository.getUrl().get()` × 2, `mavenArtifact.setClassifier`) | 0 | 0 | **0** | 1 (checkstyle dep reflow) |
| A | [verify-assemble `ea31a6c0`](https://github.com/abstratt/spring-boot/commit/ea31a6c004367d81f0fc38eb6e6ca3222b72d38c) | 3 | 2 (`isPresent`/`compilerArgs.get().contains` fix, `SpringBootAotPlugin.setClasspath` × 2) | 0 | 1 (link URL updated) | 2 (`resolveMainClassName.setClasspath` × 2) | 0 |
| B | [verify-help `d300d56d`](https://github.com/abstratt/spring-boot/commit/d300d56d2da5f5d1a747ca289376012f100841f1) | 2 | 0 | 0 | 0 | **5** (`Format.setEncoding`, 2× `Check*.setSource`, 2× `Sync.setDestinationDir`) | 1 (checkstyle dep reflow) |
| B | [verify-assemble `8b19722b`](https://github.com/abstratt/spring-boot/commit/8b19722bdcb84c18ecb050c252dced81c74eac28) | 2 | 0 | 0 | 1 (link deleted + comment) | 2 (`resolveMainClassName.setClasspath` × 2) | 0 |

**Migration-bug revert totals: A = 2, B = 7.** Both pay for the shared `ResolveMainClassName` pair at assemble time (that bug survives in both migrate commits because `ResolveMainClassName` *does* inherit from a type whose `setClasspath` looks Gradle-migrated until you chase the receiver down to the custom `DefaultTask`). Run B additionally carried the five Sync/Format/Check*-setSource bugs into the migrate commit; Run A enumerated and reverted them pre-commit, visible as the "Broken rewrites" section in its `MIGRATION_NOTES.md`.

Run A's verify-help commit is mostly deferred Cat-A work being collected; Run B's verify-help is mostly rescue. Run A's verify-assemble mixes legitimate catch-ups with the two shared reverts; Run B's verify-assemble is pure revert + the javadoc deletion. Either branch leaves the target clean, but Run A's process looks like forward progress and Run B's looks like cleanup.

## Verdict

1. **Behavior preservation → Run A (v3).** Run B introduces 5 extra migration-bug rewrites in the migrate commit ([`JavaConventions.java` lines 291/372/379](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java) and [`MavenPluginPlugin.java` lines 238/290](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/buildSrc/src/main/java/org/springframework/boot/build/mavenplugin/MavenPluginPlugin.java)) that Run A avoided, and deletes the Gradle javadoc link where Run A repoints it. Run B earns partial credit for `BootArchiveSupport.getMetadataCharset().getOrNull()` preserving nullable semantics that Run A's `.get()` loses, but that's a single-line concession against seven net-negative deltas.

2. **Lazy vs. eager → Run B (v4), slight edge.** Both land the same lazy shapes; Run B additionally comments the `getJvmArgs().set(getJvmArgs().get())` self-reference and adds an explicit defensive copy via `new ArrayList<>(...)`. Run A leaves that self-reference uncommented.

3. **Coverage → Run B (v4).** Run B's migrate commit [`ab4b6c72`](https://github.com/abstratt/spring-boot/commit/ab4b6c727dfc8d2378e237fecf794250b871ba8e) lands 6 additional Cat-A sites that Run A's migrate commit [`d264526c`](https://github.com/abstratt/spring-boot/commit/d264526ca7f55f671f28c854dbdfdcab569f9e63) defers (setPackaging, setClassifier, `MavenArtifactRepository.url` × 2, setIncremental, `SpringBootAotPlugin` × 2, the `configureUtf8Encoding` / `configureParametersCompilerArg` pair). Both branches reach the same tip state, but Run B's task-06 snapshot is closer to that tip.

4. **Self-reporting → Run A (v3).** Run B uses `A:` on all 5 commits ([`2fd09961`](https://github.com/abstratt/spring-boot/commit/2fd09961cab392c5ff66e03324a73b9b4c4fb6ce), [`ab4b6c72`](https://github.com/abstratt/spring-boot/commit/ab4b6c727dfc8d2378e237fecf794250b871ba8e), [`d300d56d`](https://github.com/abstratt/spring-boot/commit/d300d56d2da5f5d1a747ca289376012f100841f1), [`8b19722b`](https://github.com/abstratt/spring-boot/commit/8b19722bdcb84c18ecb050c252dced81c74eac28), [`b2e74a2a`](https://github.com/abstratt/spring-boot/commit/b2e74a2ab82696e00bc126ba85c5fd7d8d9883c9)) where Run A gets `Assistant:` right on the report commit ([`58cd7c3a`](https://github.com/abstratt/spring-boot/commit/58cd7c3a8a138725ec2ead203396feb6f6d58a75)). Run A's [`MIGRATION_NOTES.md`](https://github.com/abstratt/spring-boot/blob/d264526ca7f55f671f28c854dbdfdcab569f9e63/MIGRATION_NOTES.md) is a 95-line curated punch list; Run B's [`MIGRATION_NOTES.md`](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/MIGRATION_NOTES.md) is a 1432-line raw scanner dump. Run A's report is more detailed and more honest about what happened in task 07 vs. task 06.

**Recommendation: accept Run A (v3).** The 2-1-1 split understates the gap — Run A wins on the two weightier criteria (behavior preservation, self-reporting), and Run B's coverage win is neutralized by the fact that Run A reaches the same end-state; it just spreads the work across verify commits cleanly, where Run B folds more of it into task 06 at the cost of shipping false positives. The two things worth cherry-picking from Run B onto Run A are:

- The one-line change in [`BootArchiveSupport.java`](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java): `jar.getMetadataCharset().get()` → `.getOrNull()` to preserve nullable semantics.
- The `jvmArgs` self-reference comment in [`BootRun.java`](https://github.com/abstratt/spring-boot/blob/ab4b6c727dfc8d2378e237fecf794250b871ba8e/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java) (and optionally the `new ArrayList<>(...)` defensive copy).

Both runs still need the `A:` → `Assistant:` trailer correction before merge — that's a pre-existing issue against both branches, carried forward from the v2 run.
