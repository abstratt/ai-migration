# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [abstratt/spring-boot](https://github.com/abstratt/spring-boot) (fork of `spring-projects/spring-boot`)
- **Task**: Migrate build scripts and Gradle API usages to the Gradle 10 lazy property preview (Provider API distribution)
- **Base commit**: [`09ece896a595e18d3b5b136a15e0c8560289493e`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e)
- **Date**: 2026-04-22

## Models under test

| Label | Model id | Tool | Branch | Compare vs base |
|---|---|---|---|---|
| **A (v1)** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1035`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1035) | [`09ece896...20260422-1035`](https://github.com/abstratt/spring-boot/compare/09ece896...gradle-10-migration/20260422-1035) |
| **B (v5)** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-2124`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-2124) | [`09ece896...20260422-2124`](https://github.com/abstratt/spring-boot/compare/09ece896...gradle-10-migration/20260422-2124) |

Both runs executed the same pipeline on the same base commit with the same model family. The two branches differ only in prompt/workflow revisions captured between 10:35 and 21:24 on 2026-04-22; the point of this benchmark is to see whether the later workflow version produces a measurably better migration.

## Executive summary

**v5 is the stronger migration overall and is the branch to accept**, though it pays a steeper verification tax than v1. v5's final tip ships cleaner lazy patterns (pure `.map` chains instead of `project.provider(() -> …get())`, `getOrNull()` where the original API was null-tolerant, preserved public-API test intent, and a richer site-by-site `MIGRATION_NOTES.md`), and catches one lambda-parameter lazy-property site during the migration commit that v1 deferred to `./gradlew help`. v1 wins cleanly on verification cost — it needed no migration-bug reverts — but it wins by being more conservative, not more correct, and its quality deficits (test drift, `.get()` instead of `.getOrNull()`, an eager-inside-lazy provider wrapper) never tripped the verify steps and would persist into main.

### Headline metrics

| Metric | v1 (20260422-1035) | v5 (20260422-2124) |
|---|---|---|
| Wall-clock elapsed (per run's REPORT) | 29m 41s | 24m 01s |
| Files in migration commit | 31 | 33 |
| Files in verify-help + verify-assemble | 5 (4 + 1) | 4 (3 + 1) |
| Full branch diff vs base | 37 files | 37 files |
| `./gradlew help` passed at migration commit | No (3 compile errors fixed in verify) | No (3 compile errors + 3 Sync runtime bugs fixed in verify) |
| `./gradlew assemble` passed at migration commit | No (Javadoc URL workaround required) | No (same Javadoc URL workaround) |
| Groovy syntax errors introduced | 0 | 0 |
| Semantic regressions (`from` ≠ `setFrom`) | 0 | 0 |
| Compile errors from `.get()` on non-Gradle types | 0 (correctly skipped) | 3 sites (`Format.setEncoding`, `task.setSource` × 2) reverted in verify-help |
| `buildSrc/` migrated | Yes | Yes |
| Trailer correctly filled on every commit | Yes | Yes |

## Methodology

Pipeline commit table. Both branches contain the full April-2026 task set including task 07 (`./gradlew help`).

| Task | v1 (A) | v5 (B) |
|---|---|---|
| 04 Swap Distribution | [`6043c1b`](https://github.com/abstratt/spring-boot/commit/6043c1bdab18fc8e1a1c24da5678335cdca78410) | [`1605ee8`](https://github.com/abstratt/spring-boot/commit/1605ee8abfc251831f72b96912773e297d2cb264) |
| 06 Migrate | [`d34f3c0`](https://github.com/abstratt/spring-boot/commit/d34f3c0db3ade90b8155f734987927ca6db71e25) | [`89b4b2b`](https://github.com/abstratt/spring-boot/commit/89b4b2b3985e5a36378425d09b40dd5b48172707) |
| 07 Verify help | [`513dcde`](https://github.com/abstratt/spring-boot/commit/513dcde3598349267c439ad3ee2cdd1e1dc874a4) | [`5125d3a`](https://github.com/abstratt/spring-boot/commit/5125d3a633b12fce7fbed969ab36f1cc23ed6a77) |
| 08 Verify assemble | [`b07d378`](https://github.com/abstratt/spring-boot/commit/b07d37853ea67a430638f99fa3a9e369e5bf9d52) | [`11350930`](https://github.com/abstratt/spring-boot/commit/11350930b2d5ecf54ad407c32de1e8d349d4b274) |
| 09 Report | [`2acb0ee`](https://github.com/abstratt/spring-boot/commit/2acb0eeade20eff712797c222b21e47765ee54ae) | [`295a74a`](https://github.com/abstratt/spring-boot/commit/295a74a61f14cc342abb433dd0144dbf8041fa5b) |

No task was absent from either run. Task 03 (Upgrade Gradle 9) was a resume-skip on both branches (wrapper was already on 9.4.1); both runs documented the skip in their REPORT.

The migration commits touch an overlapping set of 31 files; v5 additionally touches [`MavenPluginPlugin.java`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/buildSrc/src/main/java/org/springframework/boot/build/mavenplugin/MavenPluginPlugin.java) and [`ConsumableContentContribution.java`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/buildSrc/src/main/java/org/springframework/boot/build/antora/ConsumableContentContribution.java) during migrate; v1 picks up those same files but only during `./gradlew help`. The full branch diffs converge at identical file counts (37 files each) by the Generate-Report commit.

## Results by criterion

### (1) Behavior preservation

**v5 wins.** Two non-equivalent rewrites in v1 drift from the original observable contract; v5 keeps the original.

**v1 changes test assertions to exercise internal API.** [`AbstractBootArchiveTests.java`](https://github.com/abstratt/spring-boot/blob/d34f3c0db3ade90b8155f734987927ca6db71e25/build-plugin/spring-boot-gradle-plugin/src/test/java/org/springframework/boot/gradle/tasks/bundling/AbstractBootArchiveTests.java) contains tests literally named `classpathCanBeSetUsingAFileCollection` and `classpathCanBeSetUsingAnObject` — their purpose is to verify the user-facing `setClasspath(...)` entry point continues to work. v1 rewrote them to call `getClasspath().setFrom(...)` instead, which no longer tests the method under test:

```diff
 void classpathCanBeSetUsingAFileCollection() throws IOException {
     this.task.getMainClass().set("com.example.Main");
     this.task.classpath(jarFile("one.jar"));
-    this.task.setClasspath(this.task.getProject().files(jarFile("two.jar")));
+    this.task.getClasspath().setFrom(this.task.getProject().files(jarFile("two.jar")));
     executeTask();
```

v5 left both test call sites on `setClasspath(...)` — the behavior the test name advertises.

**v1 uses `.get()` where the original accessor contract was nullable.** In [`BootArchiveSupport.createCopyAction`](https://github.com/abstratt/spring-boot/blob/d34f3c0db3ade90b8155f734987927ca6db71e25/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java#L132), the pre-migration source was `String encoding = jar.getMetadataCharset();` — a plain accessor that returned `null` for "not set". v1 migrates to `.get()` (throws on unset); v5 uses `.getOrNull()` (null on unset), preserving the original nullability:

```diff
-        String encoding = jar.getMetadataCharset().get();      // v1
+        String encoding = jar.getMetadataCharset().getOrNull(); // v5
```

In practice `Jar.metadataCharset` defaults to `"UTF-8"`, so v1's `.get()` works at runtime today — but this is a silent narrowing of the contract the downstream code was written against.

**No semantic regressions of the `from` / `setFrom` variety in either branch.** Every `file_collection`-kind rewrite on both sides uses `.setFrom(...)` (replace), never `from(...)` (append).

### (2) Lazy vs. eager

**v5 wins, narrowly.**

v1 wraps a migrated accessor inside `project.provider(() -> … .get())`, which is technically lazy (the outer `project.provider` is a `Provider<T>`) but eagerly resolves the inner `Property` at evaluation time. v5 rewrites the same site as a pure `.map` chain — the idiomatic lazy pattern the migration is meant to produce:

```diff
 distribution.getDistributionBaseName()
-    .convention((project.provider(() -> javaApplication.getApplicationName().get() + "-boot"))); // v1
+    .convention(javaApplication.getApplicationName().map((name) -> name + "-boot"));             // v5
```

File-at-commit: [`ApplicationPluginAction.java` (v1)](https://github.com/abstratt/spring-boot/blob/d34f3c0db3ade90b8155f734987927ca6db71e25/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java#L57) vs [`ApplicationPluginAction.java` (v5)](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java#L57).

Elsewhere the branches agree: both resort to `.getFiles()` + `.setFrom(...)` only at the `BootRun.sourceResources` self-reference site (correct — a documented break of the self-cycle), and both land `getJvmArgs().set(getJvmArgs().get())` self-referential snapshot at `BootRun.exec`. v5 adds explanatory comments on both; v1 has a single terser comment at the first site and none at the second. No rogue `.get()` inside configuration blocks was found on either tip (`git grep -E 'setFrom\([^)]*\.get\(\)\)|\.set\([^)]*\.get\(\)\)'` → 0 hits on both branches).

### (3) Coverage

**Effectively tied, with a slight edge to v5 in the migration commit.**

Both branches migrated `buildSrc/` — the `org.springframework.boot.build` package tree is fully covered on both. Both treat the 14 module-level `build.gradle` files identically (`options.compilerArgs << '…'` → `.add('…')`, `jvmArgs += "…"` → `.add("…")`). File-for-file in the 14 module build scripts, the diffs are byte-equal after stripping commit headers.

Where they diverge is **when** some files were migrated:

- **v5 migrate commit includes `ConsumableContentContribution.java`** (lambda-parameter `mavenArtifact.setClassifier(classifier)` → `.getClassifier().set(classifier)`). v1's migrate commit misses this site; the build breaks in `./gradlew help` and v1 patches it then.
- **v5 migrate commit includes `MavenPluginPlugin.java`** (pom lambda-param and Sync destination rewrites). v1's migrate leaves the file untouched; its verify-help pass picks up the pom lambda-param. The Sync destination rewrites v5 attempted here are discussed in criterion (4) — they were wrong and had to be reverted.
- **Both migrate commits miss `ConfigurationPropertiesPlugin.java`** (`compileJava.getOptions().setIncremental(false)` inside a configure lambda) and fix it in verify-help; identical patches on both branches.

Neither branch missed any files the other covered end-to-end. v5's migrate commit covers two additional files, but the net effect by final tip is equivalent file coverage with a different split between migrate and verify.

### (4) Self-reporting

**Effectively tied. Both trailers are fully populated; both REPORTs are substantive; v1's `MIGRATION_NOTES.md` is longer, v5's is more consistently per-site.**

Every commit on both branches carries `Assistant: Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]` — no `<<Tool Name>>` placeholders survive on either side.

Per-run REPORTs ([v1](https://github.com/abstratt/spring-boot/blob/2acb0eeade20eff712797c222b21e47765ee54ae/REPORT-20260422-1035.md), [v5](https://github.com/abstratt/spring-boot/blob/295a74a61f14cc342abb433dd0144dbf8041fa5b/REPORT-20260422-2124.md)) both include wall-clock elapsed, kinds applied, manual fixes, and known limitations.

- **v5's REPORT overstates its Sync handling.** It claims: *"all three `Sync.setDestinationDir(File)` call sites rewritten to `into(…)` (because `Sync.getDestinationDirectory()` is not exposed — only `into(Object)`)."* The migrate commit actually rewrote them to `task.getDestinationDir().set(...)`; only the verify-help commit replaced them with `into(...)`. The reporting conflates the final tip with what happened inside task 06. Mildly inaccurate.
- **v1's REPORT is accurate about what task 06 did**, and its note on `BootRun.sourceResources` circularity matches what the code shows.

`MIGRATION_NOTES.md`:
- **v1's file is 116 lines, grouped by category** (user-defined tasks, third-party APIs, Gradle APIs not in migration-data, etc.) with an aggregated "every entry below" preamble. Reads as a taxonomy.
- **v5's file is 57 lines, grouped by source file**, with per-entry reasons lifted from the actual receiver type at each call site. Reads as a punch list.

Both are genuine site-by-site justifications — not canonical-boilerplate regurgitation. v1's is more exhaustive in scope (it enumerates extra sites like `AutoConfigurationPlugin.java`, `StarterPlugin.java`, `EclipseConventions.java`); v5's is terser but no less concrete.

## Verification cost — the rescue effect

v1 needed 5 files of verify-time edits; v5 needed 4. The raw count hides the qualitative difference: **v1's verify edits were all forward progress; v5's were mostly bug reverts.**

| Branch | Commit | Files | Characterization |
|---|---|---|---|
| v1 | [`513dcde` verify help](https://github.com/abstratt/spring-boot/commit/513dcde3598349267c439ad3ee2cdd1e1dc874a4) | 4 | **3 genuine lambda-parameter fixes + 1 formatter reflow.** [`ConsumableContentContribution`](https://github.com/abstratt/spring-boot/blob/513dcde3598349267c439ad3ee2cdd1e1dc874a4/buildSrc/src/main/java/org/springframework/boot/build/antora/ConsumableContentContribution.java#L99) `mavenArtifact.setClassifier` → `.getClassifier().set`; [`MavenPluginPlugin`](https://github.com/abstratt/spring-boot/blob/513dcde3598349267c439ad3ee2cdd1e1dc874a4/buildSrc/src/main/java/org/springframework/boot/build/mavenplugin/MavenPluginPlugin.java#L161) `pom.setPackaging` → `.getPackaging().set`; [`ConfigurationPropertiesPlugin`](https://github.com/abstratt/spring-boot/blob/513dcde3598349267c439ad3ee2cdd1e1dc874a4/buildSrc/src/main/java/org/springframework/boot/build/context/properties/ConfigurationPropertiesPlugin.java#L99) `compileJava.getOptions().setIncremental(false)` → `.getIncremental().set(false)`. The `JavaConventions.java` change is a one-line format reflow caused by the longer `.getToolVersion().set(...)` expression pushing a chain over Spring-javaformat's width budget. |
| v1 | [`b07d378` verify assemble](https://github.com/abstratt/spring-boot/commit/b07d37853ea67a430638f99fa3a9e369e5bf9d52) | 1 | Legitimate third-party workaround — Javadoc `links` pinned to `9.0.0` because the preview distribution's reported version has no published docs. |
| v5 | [`5125d3a` verify help](https://github.com/abstratt/spring-boot/commit/5125d3a633b12fce7fbed969ab36f1cc23ed6a77) | 3 | **1 genuine lambda-parameter fix + 5 migration-bug reverts + 1 formatter reflow.** [`ConfigurationPropertiesPlugin`](https://github.com/abstratt/spring-boot/blob/5125d3a633b12fce7fbed969ab36f1cc23ed6a77/buildSrc/src/main/java/org/springframework/boot/build/context/properties/ConfigurationPropertiesPlugin.java#L99) `.setIncremental(false)` fix matches v1's. [`JavaConventions`](https://github.com/abstratt/spring-boot/blob/5125d3a633b12fce7fbed969ab36f1cc23ed6a77/buildSrc/src/main/java/org/springframework/boot/build/JavaConventions.java#L291) reverts `Format.getEncoding().set("UTF-8")` back to `Format.setEncoding("UTF-8")` because `Format` is `io.spring.javaformat.gradle.tasks.Format`, not a Gradle type. Same file reverts two user-defined `task.setSource(main.getResources())` sites on `CheckAotFactories` / `CheckSpringFactories`. [`MavenPluginPlugin`](https://github.com/abstratt/spring-boot/blob/5125d3a633b12fce7fbed969ab36f1cc23ed6a77/buildSrc/src/main/java/org/springframework/boot/build/mavenplugin/MavenPluginPlugin.java#L183) reverts three `task.getDestinationDir().set(...)` sites to `task.into(...)` — the migrate commit had attempted to treat `Sync.destinationDir` as a lazy property, but the Gradle 10 preview `Sync` API exposes only `into(Object)` for that role. |
| v5 | [`11350930` verify assemble](https://github.com/abstratt/spring-boot/commit/11350930b2d5ecf54ad407c32de1e8d349d4b274) | 1 | Same Javadoc link issue as v1; v5 points at `docs.gradle.org/current/javadoc` instead of hardcoding `9.0.0`. Both are legitimate. |

Illustrative rescue diff (v5, `MavenPluginPlugin.java`):

```diff
 TaskProvider<Sync> populateRepository = project.getTasks()
     .register("populateTestMavenRepository", Sync.class, (task) -> {
-        task.getDestinationDir().set(
-                project.getLayout().getBuildDirectory().dir("test-maven-repository").get().getAsFile());
+        task.into(project.getLayout().getBuildDirectory().dir("test-maven-repository"));
```

Illustrative rescue diff (v5, `JavaConventions.java`):

```diff
 private void configureSpringJavaFormat(Project project) {
     project.getPlugins().apply(SpringJavaFormatPlugin.class);
-    project.getTasks().withType(Format.class, (Format) -> Format.getEncoding().set("UTF-8"));
+    project.getTasks().withType(Format.class, (Format) -> Format.setEncoding("UTF-8"));
```

Net verify-time forward-progress ratio:

- **v1**: 4 legitimate edits / 4 files = 100% forward progress.
- **v5**: 2 legitimate edits (lambda-param + Javadoc) / 4 files ≈ 50% forward progress; the other half is reverting migration-commit bugs.

## Verdict

1. **Behavior preservation — winner: v5.** The `AbstractBootArchiveTests` regression and `jar.getMetadataCharset().get()` contract narrowing in v1 ([tests diff](https://github.com/abstratt/spring-boot/blob/d34f3c0db3ade90b8155f734987927ca6db71e25/build-plugin/spring-boot-gradle-plugin/src/test/java/org/springframework/boot/gradle/tasks/bundling/AbstractBootArchiveTests.java#L218), [metadataCharset](https://github.com/abstratt/spring-boot/blob/d34f3c0db3ade90b8155f734987927ca6db71e25/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java#L132)) are absent from v5.
2. **Lazy vs. eager — winner: v5.** The `.map(name -> name + "-boot")` pattern at [`ApplicationPluginAction.java:57`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java#L57) is idiomatic; v1's `project.provider(() -> … .get())` works but buries an eager resolution inside a synthetic provider.
3. **Coverage — tie.** File-by-file, both branches land the same 37-file diff at their tip, covering `buildSrc/`, module build scripts, and the build-plugin sources equivalently.
4. **Self-reporting — tie.** Both trailers are correct; both REPORTs are substantive. v1's `MIGRATION_NOTES.md` is broader (116 lines, categorical); v5's is narrower but more per-site (57 lines, grouped by source file). v5's REPORT misdescribes when its Sync rewrites landed (migrate vs. verify-help) — minor inaccuracy.

**Recommendation: accept v5.** The final tip is cleaner (idiomatic `.map`, nullable-preserving `.getOrNull()`, intact test intent, explanatory comments) and is the branch that would merge to `main`. v5's higher verify-commit churn is real — five of its migrate-commit rewrites were wrong — but every wrong rewrite was caught by `./gradlew help` and reverted; the bad state is not in the final tree. v1, by contrast, shipped a migrate commit that the verify steps happily accepted, but its final tree carries three soft regressions (test drift, `.get()` contract narrowing, synthetic-provider laziness) that no automated gate would catch.

**Salvage from v1**: its `MIGRATION_NOTES.md` categorisation (§"Category A user-defined tasks", §"Third-party plugin APIs") covers several call sites v5's notes don't enumerate (e.g. [`AutoConfigurationPlugin.java:132-141`](https://github.com/abstratt/spring-boot/blob/2acb0eeade20eff712797c222b21e47765ee54ae/MIGRATION_NOTES.md), `StarterPlugin.java`, `EclipseConventions.java`). Before merging v5, fold those additional entries into v5's notes so the deferred-hits log is complete.
