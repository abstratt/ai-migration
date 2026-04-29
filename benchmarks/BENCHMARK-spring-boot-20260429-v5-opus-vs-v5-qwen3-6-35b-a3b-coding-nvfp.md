# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [`abstratt/spring-boot`](https://github.com/abstratt/spring-boot.git) (fork of `spring-projects/spring-boot`)
- **Task**: Migrate the build (build scripts + `buildSrc/` + `build-plugin/`) from Gradle 9.x to Gradle 10 lazy-property semantics; verify with `./gradlew help` and `./gradlew assemble`.
- **Base commit**: [`09ece896a595e18d3b5b136a15e0c8560289493e`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e) (`Merge branch '4.0.x'`, 2026-04-02).
- **Date**: 2026-04-29.

## Models under test

| Label | Description | Tool (per `Assistant:` trailer) | Friendly model id (per trailer) | Branch |
|---|---|---|---|---|
| **A** | `v5-opus` | Claude Code | Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]` | [`gradle-10-migration/20260422-2124`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-2124) |
| **B** | `v5-qwen3.6:35b-a3b-coding-nvfp` | (declared) qwen3.6 35b a3b-coding (nvfp); (per trailers) Claude Code / Sonnet on swap, Opus 4.7 on migrate — see Self-reporting | (none coherent — see below) | [`gradle-10-migration/20260429-1028`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260429-1028) |

Branch compare vs base:
- A: <https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260422-2124>
- B: <https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260429-1028>

## Executive summary

**A (v5-opus) wins, decisively.** A produced a small, surgical, mostly-correct migration (33 files, 125+/60-) that compiles cleanly and passes both `./gradlew help` and `./gradlew assemble`, with the verify pass adding only minor follow-up fixes on top. B (v5-qwen3.6:35b) ran ~7× longer, touched almost twice as many files (57), and produced a broken tree: a literal Java syntax error, ~17 invented `Project.getVersion().get()` rewrites that don't compile, ~14 invented `JavaPluginExtension.getSourceSets().get()` rewrites that don't compile, ~6 `getClasspath().setFrom(...)` rewrites against plain `FileCollection` (no such method), 2 self-reference cycles in `BootRun`, 2 semantic regressions where `.get()` replaced `.getOrNull()`, and a missed migration site (`AbstractAot.super.getArgs()`) whose absence alone would fail compilation. B never executed verify (no task 07/08 commits) and never produced a report — the run aborted after task 06. B is unsalvageable as-is.

### Headline metrics

| Metric | A (v5-opus) | B (v5-qwen3.6:35b) |
|---|---|---|
| Wall-clock elapsed (first → last commit) | **~26 min** (21:25:49 → 21:51:35 UTC-3) | **~178 min** (10:31:08 → 13:29:28 UTC-3) |
| Pipeline commits present | 5 (swap, migrate, verify-help, verify-assemble, report) | **2** (swap, migrate) — verify and report missing |
| Files in migration commit | 32 code + `MIGRATION_NOTES.md` (33 total) | 56 code + `MIGRATION_NOTES.md` (57 total) |
| Files in verify commits | 3 (verify-help) + 1 (verify-assemble) = 4 | n/a — verify never ran |
| Full branch-vs-base diff | 37 files / +199 / -63 | 58 files / +154 / -129 |
| `./gradlew help` passed at migration commit | **Yes** (per per-run report; verify commit added 3 follow-up fixes) | **No** (never executed; would not compile) |
| `./gradlew assemble` passed at migration commit | **Yes** (per per-run report; one javadoc-link tweak) | **No** (never executed) |
| Source-level Groovy/Java syntax errors introduced | 0 | 1 (`RepositoryTransformersExtension.java:61` — extra `))`) |
| Compile errors from rule misapplication | 0 | **~30+** (Project.getVersion, getSourceSets, custom getClasspath, Task.enabled, BuildInfoMojo, etc.) |
| Semantic regressions (`.get()` instead of `.getOrNull()`) | 0 | 2 (`BootArchiveSupport.java:132`, `JavaPluginAction.java:252`) |
| Self-reference cycles | 0 | 2 (`BootRun.java:62, 67`) |
| Eager-`.get()` anti-pattern (compiles but loses laziness) | 0 | 1 (`ApplicationPluginAction.java:76`) |
| `Configuration.canBe*` over-migration (likely needless) | 0 | ~10 sites |
| `buildSrc/` migrated | **Yes** | Yes (broader, but broken) |
| `Assistant:` trailer correctly filled on all commits | **Yes** (5/5: `Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]`) | **No** — both commits mis-identified: swap claims `Claude Code / Sonnet / claude-sonnet-4-6`; migrate uses a `Co-Authored-By: Claude Opus 4.7` trailer instead of the required `Assistant:` form. Run was supposed to be qwen3.6:35b. |

## Methodology

Per-task commits per branch (linked SHA):

| Task | A (v5-opus) | B (v5-qwen3.6:35b) |
|---|---|---|
| 04 Swap Distribution | [`1605ee8`](https://github.com/abstratt/spring-boot/commit/1605ee8abfc251831f72b96912773e297d2cb264) | [`0810d86`](https://github.com/abstratt/spring-boot/commit/0810d860b9d5ab79f93706da25164c4505ae93c9) |
| 06 Migrate | [`89b4b2b`](https://github.com/abstratt/spring-boot/commit/89b4b2b3985e5a36378425d09b40dd5b48172707) | [`4566fe2`](https://github.com/abstratt/spring-boot/commit/4566fe26512a135b540e74e39fbc719138837586) |
| 07 Verify help | [`5125d3a`](https://github.com/abstratt/spring-boot/commit/5125d3a633b12fce7fbed969ab36f1cc23ed6a77) | **— missing —** |
| 08 Verify assemble | [`11350930`](https://github.com/abstratt/spring-boot/commit/11350930b2d5ecf54ad407c32de1e8d349d4b274) | **— missing —** |
| 09 Report | [`295a74a`](https://github.com/abstratt/spring-boot/commit/295a74a61f14cc342abb433dd0144dbf8041fa5b) | **— missing —** |

B's pipeline halted after task 06. The lack of a verify commit means *neither* `./gradlew help` nor `./gradlew assemble` was ever executed against the migrated tree on B; the migration's compile-correctness and runtime behavior were never checked by the model. (For comparison, A's verify commits surfaced and fixed 3 problems on `help` and 1 on `assemble`; B would have to surface and fix many more — see "Verification cost" below.)

Common base: [`09ece89`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e). Shared file count (in both migration commits, excluding `MIGRATION_NOTES.md`): 31. A-only files: 2. B-only files: 26.

## Results by criterion

### (1) Behavior preservation

A makes the smallest set of edits that flip removed accessors and changed-return-type getters to their lazy equivalents, and explicitly preserves user-defined setters where the migration data does not classify them. B over-applies rules to types not in the migration data (`Project.version`, `JavaPluginExtension.sourceSets`, `Configuration.canBe*`, `Task.enabled`, custom `getClasspath()` returning plain `FileCollection`), introducing dozens of compile errors and changing observable semantics in two places.

**Source-level syntax error (B):** [`RepositoryTransformersExtension.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/buildSrc/src/main/java/org/springframework/boot/build/RepositoryTransformersExtension.java) line 61 in B's migration commit:

```diff
-			URI url = repository.getUrl();
+			URI url = repository.getUrl().get()));
```

The trailing `));` is a literal syntax error. `buildSrc` does not compile. A's diff for the same line is correct: `URI url = repository.getUrl().get();`.

**Misapplied rule — `.get()` on `Project.getVersion()`** (returns `Object`, not `Provider`). 11 sites in B, 0 in A. Representative: [`BootBuildImage.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootBuildImage.java) line 91:

```diff
-			.convention(project.provider(() -> project.getVersion().toString()));
+			.convention(project.provider(() -> project.getVersion().get().toString()));
```

`Project.version` is **not** in `migration-data.json`. `Object.get()` does not exist. Compile failure.

**Cross-project rule misapplication (B):** B applied the same Project-version rewrite to a **Maven plugin** source file: [`spring-boot-maven-plugin/.../BuildInfoMojo.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-maven-plugin/src/main/java/org/springframework/boot/maven/BuildInfoMojo.java) line 138:

```diff
-		String version = getIfNotExcluded("version", this.project.getVersion());
+		String version = getIfNotExcluded("version", this.project.getVersion().get());
```

`this.project` here is `org.apache.maven.project.MavenProject`, whose `getVersion()` returns `String`. The migration scope is Gradle. A correctly left this file alone.

**Misapplied rule — `getSourceSets().get()`.** `JavaPluginExtension.getSourceSets()` returns `SourceSetContainer` (no `.get()` no-arg). 14+ sites in B, 0 in A. Representative: [`NativeImagePluginAction.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/NativeImagePluginAction.java) line 56:

```diff
-			SourceSetContainer sourceSets = javaPluginExtension.getSourceSets();
+			SourceSetContainer sourceSets = javaPluginExtension.getSourceSets().get();
```

`SourceSetContainer` is a `NamedDomainObjectContainer<SourceSet>`, not a `Provider<SourceSetContainer>`. Compile failure (and obvious type mismatch on the LHS).

**Drive-by/dropped-comment migration on user-defined setters (B).** [`JavaPluginAction.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/JavaPluginAction.java), `ResolveMainClassName extends DefaultTask` with a custom `void setClasspath(FileCollection)` and `FileCollection getClasspath()` (returns plain `FileCollection`, *not* `ConfigurableFileCollection`):

```diff
-		resolveMainClassName.setClasspath(classpath);
+		resolveMainClassName.getClasspath().setFrom(classpath);
```

Compile failure: `FileCollection` has no `.setFrom(...)`. A correctly preserved the user-defined setter ([`A's JavaPluginAction.java at the migrate commit`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/JavaPluginAction.java) — left as `resolveMainClassName.setClasspath(classpath)`) and documented the preservation in `MIGRATION_NOTES.md`.

**Semantic regression — `.getOrNull()` → `.get()` (B).** [`BootArchiveSupport.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java) line 132:

```diff
-		String encoding = jar.getMetadataCharset();
+		String encoding = jar.getMetadataCharset().get();
```

vs A at the same line ([A's BootArchiveSupport.java](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java)):

```diff
-		String encoding = jar.getMetadataCharset();
+		String encoding = jar.getMetadataCharset().getOrNull();
```

Original `getMetadataCharset()` returned `@Nullable String`; downstream `BootZipCopyAction` accepts a nullable encoding. B's `.get()` throws `IllegalStateException` on archives that don't set `metadataCharset`. Same shape recurs in [`JavaPluginAction.java:252`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/JavaPluginAction.java) where B uses `getEncoding().get() == null` for a "configure-if-unset" guard, so the guard now throws instead of evaluating false.

### (2) Lazy vs. eager

**Self-reference cycle in `setFrom` (B).** [`BootRun.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java) line 62:

```diff
-		setClasspath(getProject().files(srcDirs, getClasspath()).filter((file) -> !file.equals(resourcesDir)));
+		getClasspath().setFrom(getProject().files(srcDirs, getClasspath()).filter((file) -> !file.equals(resourcesDir)));
```

`ConfigurableFileCollection.setFrom(self-derived)` produces a circular dependency at resolve time. A's same line ([A's BootRun.java](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java)) snapshots via `.getFiles()` to break the cycle, with an explanatory leave-alone note in `MIGRATION_NOTES.md`:

```diff
-		setClasspath(getProject().files(srcDirs, getClasspath()).filter((file) -> !file.equals(resourcesDir)));
+		getClasspath().setFrom(getProject().files(srcDirs, getClasspath().getFiles()).filter((file) -> !file.equals(resourcesDir)));
```

**Self-reference in `Property.set` (B).** Same file, line 67:

```diff
-		setJvmArgs(getJvmArgs());
+		getJvmArgs().set(getJvmArgs());
```

`Property.set(provider)` where the provider is the property itself → circular dependency at runtime. A used `.set(getJvmArgs().get())` to snapshot eagerly (the surrounding code then appends an extra arg, so eager snapshotting is the right shape).

**Eager `.get()` where lazy wiring was already in place (B).** [`ApplicationPluginAction.java`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java) line 76:

```diff
-			javaApplication.getMainModule().convention(boot.getMainModule());
-			javaApplication.getMainClass().convention(boot.getMainClass());
+			javaApplication.getApplicationDefaultJvmArgs().convention(/* unchanged */);
+			run.convention(javaApplication.getApplicationDefaultJvmArgs().get());
```

The original code already passed the lazy `Provider`. B added an unnecessary `.get()`, eagerly resolving at configuration time.

**Lazy `Provider.map` (A).** Same file, line 57: A converts a Groovy-string-concat-in-provider into a clean `.map`:

```diff
-		.convention((project.provider(() -> javaApplication.getApplicationName() + "-boot")))
+		.convention(javaApplication.getApplicationName().map((name) -> name + "-boot"));
```

B's variant of the same line wraps a `.get()` inside `project.provider(...)` — works at run time but loses the rule-encoded laziness:

```diff
+		.convention((project.provider(() -> javaApplication.getApplicationName().get() + "-boot")))
```

### (3) Coverage

A and B both migrate `buildSrc/`. B touches more files in `buildSrc/` (24 vs. A's 11) but a sizeable fraction of those B-only files are the rule-misapplications enumerated above; the *surface area* is broader, but the *correctness* is worse.

**Coverage gap in B — `AbstractAot.super.getArgs()`.** A migrates [`AbstractAot.java`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/aot/AbstractAot.java) line 109:

```diff
-		args.addAll(super.getArgs());
+		args.addAll(super.getArgs().get());
```

In Gradle 10 `JavaExec.getArgs()` returns `ListProperty<String>`. B did not touch this file; in B's tree, `args.addAll(super.getArgs())` becomes `List.addAll(ListProperty)` — compile failure. Note that B *did* migrate `ProcessAot.java` and `ProcessTestAot.java` (the subclasses), but those changes are moot because the parent class no longer compiles. This is a pure coverage gap.

**Coverage gap in B — test resource.** A migrates the test fixture [`JavaPluginActionIntegrationTests-javaCompileTasksUseParametersAndAdditionalCompilerFlags.gradle`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/test/resources/org/springframework/boot/gradle/plugin/JavaPluginActionIntegrationTests-javaCompileTasksUseParametersAndAdditionalCompilerFlags.gradle): `options.compilerArgs << '-Xlint:all'` → `options.compilerArgs.add('-Xlint:all')`. The `<<` operator is removed for `ListProperty` on Gradle 10; the fixture would fail at script evaluation when the integration test runs. B missed this site.

### (4) Self-reporting

**A's commit trailers** are uniform and correctly identify the model on all 5 commits:

```
Assistant: Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]
```

**A's per-run report** — [`REPORT-20260422-2124.md`](https://github.com/abstratt/spring-boot/blob/295a74a61f14cc342abb433dd0144dbf8041fa5b/REPORT-20260422-2124.md) — accurately catalogs kinds applied, names the leave-alone files (with site-specific reasons), discloses the 28 remaining `[CONFIRMED]` scanner hits as documented false positives, and notes the verify-time follow-ups. The `MIGRATION_NOTES.md` audit it claims (26 entries / 26 distinct reasons) is correct.

**B's commit trailers are wrong on both commits and inconsistent with each other:**

- Swap-distribution commit [`0810d86`](https://github.com/abstratt/spring-boot/commit/0810d860b9d5ab79f93706da25164c4505ae93c9) trailer: `Assistant: Claude Code / Sonnet / claude-sonnet-4-6`.
- Migrate commit [`4566fe2`](https://github.com/abstratt/spring-boot/commit/4566fe26512a135b540e74e39fbc719138837586) has **no `Assistant:` trailer at all**, only `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`.

The run is documented (in the benchmark argument) as `v5-qwen3.6:35b-a3b-coding-nvfp` — i.e., a qwen3.6 35b model. Neither trailer says "qwen". The model failed to substitute its real identity; on the swap commit it falsely claimed Sonnet, on the migrate commit it produced a different placeholder shape entirely. This is the textbook trailer red flag from the `tasks/CONTEXT.md` self-reporting criterion. (Note also: qwen-derived models trained on Claude-generated synthetic data sometimes self-identify as Claude — the trailers may genuinely be the model's "best guess" rather than a deliberate edit, but they are still wrong, and a correct pipeline trailer is supposed to reflect the actual model id, not the model's self-image.)

**B has no per-run `REPORT-*.md`** — task 09 was never run. The `MIGRATION_NOTES.md` that exists in B's tree contains a brief per-file processing summary (correct in tone) but cannot serve as a substitute for the report because (a) it predates verify, (b) it doesn't enumerate the bugs we found, and (c) it claims the false positives include `Project.*` and `Configuration.*` while B's own diff contains dozens of `Project.getVersion().get()` and `Configuration.getCanBe*().set(...)` rewrites — a self-contradiction.

## Verification cost — the rescue effect

| Branch | Verify commit | Files | Characterization |
|---|---|---|---|
| A | [`5125d3a` "Verify with `./gradlew help`"](https://github.com/abstratt/spring-boot/commit/5125d3a633b12fce7fbed969ab36f1cc23ed6a77) | 3 | **Mixed.** 2 sites are migration-bug reverts (`Format.setEncoding` on `io.spring.javaformat.gradle.tasks.Format` — third-party type, not a Gradle setter; and `task.setSource(main.getResources())` on the user-defined `CheckFactoriesFile`/`CheckSpringFactories` whose `setSource` is *not* a removed Gradle accessor). 1 site is a legitimate forward-fix that task 06 missed (`compileJava.getOptions().setIncremental(false)` → `getIncremental().set(false)`). 3 sites are forward-fixes in `MavenPluginPlugin.java` switching the migrated `task.getDestinationDir().set(File)` form to `task.into(Provider<Directory>)` — the task-06 form was a mismatch (`Sync.destinationDir` returns `File`, the lazy property is `getDestinationDirectory()`); these are migration-bug fixes that compile and behave correctly. |
| A | [`11350930` "Verify with `./gradlew assemble`"](https://github.com/abstratt/spring-boot/commit/11350930b2d5ecf54ad407c32de1e8d349d4b274) | 1 | **Genuine workaround.** Switched the gradle-plugin javadoc `links` from the `gradle.gradleVersion`-templated URL to `current/javadoc` because the Provider API preview distribution publishes no Javadoc under its version path. Not a migration bug; an environmental constraint of the verification distribution. |
| B | (none) | — | B never ran verify. Counterfactually, given the spotted defects (1 syntax error + ~30 compile errors + 2 self-reference cycles + 2 semantic regressions + 1 missing-coverage compile gap), a verify pass would have to revert or rewrite ≥30 of B's 56 code-file changes before the build would even reach `help`. |

A's verify cost (4 files, of which ~3 are clean migration-bug reverts and 1 is an environmental workaround) is within the "0–3 file" healthy band when you exclude the environmental Javadoc tweak. B's counterfactual verify cost is an order of magnitude larger and would require the model to recognize that ~half its rule applications were against types not in `migration-data.json` — a kind of self-review B did not perform.

## Verdict

1. **Behavior preservation — A wins.** A's diff applies removed-accessor and changed-return-type rules narrowly to the types the migration data covers, preserving user-defined setters at [`JavaPluginAction.java:117,144`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/JavaPluginAction.java) and noting them in `MIGRATION_NOTES.md`. B introduces a literal syntax error ([`RepositoryTransformersExtension.java:61`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/buildSrc/src/main/java/org/springframework/boot/build/RepositoryTransformersExtension.java)), ~30+ compile errors from invented rules on `Project.version`, `JavaPluginExtension.sourceSets`, `Configuration.canBe*`, `Task.enabled`, and plain-`FileCollection` `getClasspath()`, plus 2 semantic regressions where `.get()` replaced `.getOrNull()` ([`BootArchiveSupport.java:132`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/bundling/BootArchiveSupport.java), [`JavaPluginAction.java:252`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/JavaPluginAction.java)).
2. **Lazy vs. eager — A wins.** A produces the only correct lazy chain at [`ApplicationPluginAction.java:57`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java) (`.map(...)` instead of `provider(() -> .get() + ...)`), and breaks the two `BootRun` self-references correctly ([`BootRun.java:62,67`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java)) where B leaves both as runtime-circular. B also adds an unnecessary eager `.get()` at [`ApplicationPluginAction.java:76`](https://github.com/abstratt/spring-boot/blob/4566fe26512a135b540e74e39fbc719138837586/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/plugin/ApplicationPluginAction.java) that wasn't in the original code.
3. **Coverage — A wins on correctness; B is broader but compounding.** B touches 26 files A did not, but 24 of those introduce one or more bugs from the rule-misapplication families above. Conversely, B *misses* two sites A caught: [`AbstractAot.java:109`](https://github.com/abstratt/spring-boot/blob/89b4b2b3985e5a36378425d09b40dd5b48172707/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/aot/AbstractAot.java) (mandatory — its absence makes B's `ProcessAot`/`ProcessTestAot` migrations moot) and the integration-test fixture `.gradle` file with `compilerArgs <<`. The `buildSrc/` scope is comparable in both runs (both crawled past the default-scanner `build`-directory exclusion), but B's broader scope is a net liability, not an asset.
4. **Self-reporting — A wins decisively.** A's 5 commits all carry the correct `Assistant: Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]` trailer; the per-run [`REPORT-20260422-2124.md`](https://github.com/abstratt/spring-boot/blob/295a74a61f14cc342abb433dd0144dbf8041fa5b/REPORT-20260422-2124.md) accurately characterizes scope, leave-aloners, and the `MIGRATION_NOTES.md` audit. B's swap commit [`0810d86`](https://github.com/abstratt/spring-boot/commit/0810d860b9d5ab79f93706da25164c4505ae93c9) falsely identifies the model as Claude Sonnet 4.6, B's migrate commit [`4566fe2`](https://github.com/abstratt/spring-boot/commit/4566fe26512a135b540e74e39fbc719138837586) has no `Assistant:` trailer at all (only a `Co-Authored-By:` referencing Opus 4.7), and B never produced a `REPORT-*.md`. The run was supposed to be `qwen3.6:35b-a3b-coding-nvfp`; both trailers misidentify the model.

### Recommendation

**Accept A. Discard B.** B is not a candidate even for partial cherry-picking:

- Of B's 26 unique files, every one introduces at least one of: a literal syntax error, a `Project.getVersion().get()` rewrite that doesn't compile, a `getSourceSets().get()` rewrite that doesn't compile, a `Configuration.canBe*` over-migration, or a `Task.setEnabled` over-migration. None of those is a "clever insight A missed" — all are rule misapplications.
- B's wider `buildSrc/` coverage (e.g., `BomExtension`, `OptionalDependenciesPlugin`, `ToolchainPlugin`, the various `*Plugin` files) is not worth salvaging because every B-only `buildSrc/` file is contaminated by the same `getSourceSets().get()` and `Project.getVersion().get()` patterns; the corresponding correct migration would be **no change at all**, since `JavaPluginExtension.sourceSets` and `Project.version` are not in `migration-data.json`.
- The pipeline-incompleteness alone (no verify, no report) would be a hard blocker on accepting B even if its diff were correct.

If a future iteration of qwen3.6:35b is attempted, the model needs explicit guardrails against (a) rewriting accessors that are not in `migration-data.json`, (b) treating any `getX()` call as a `Provider` candidate without confirming the receiver type, and (c) the self-reference shapes that broke `BootRun`. The model's self-identification capability also needs hardening — a trailer claiming "Sonnet" or "Opus" when the run is qwen is the kind of red flag the self-reporting criterion is designed to catch.
