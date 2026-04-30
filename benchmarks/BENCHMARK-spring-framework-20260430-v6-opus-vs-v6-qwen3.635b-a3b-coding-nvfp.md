# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [`abstratt/spring-framework`](https://github.com/abstratt/spring-framework) (fork of `spring-projects/spring-framework`)
- **Task**: Migrate the build (root + module `*.gradle` + `buildSrc/`) from Gradle 9.x to Gradle 10 lazy-property semantics; verify with `./gradlew help` and `./gradlew assemble`.
- **Base commit**: [`8fe0eec5bf6965780c2b06fe6a0d0108ea134aae`](https://github.com/abstratt/spring-framework/commit/8fe0eec5bf6965780c2b06fe6a0d0108ea134aae) (common merge base of both branches).
- **Date**: 2026-04-30.

## Models under test

| Label | Description | Tool (per `Assistant:` trailer) | Friendly model id (per trailer) | Branch |
|---|---|---|---|---|
| **A** | `v6-opus` | Claude Code | Opus 4.7 (1M context) — `claude-opus-4-7[1m]` | [`gradle-10-migration/20260430-1001`](https://github.com/abstratt/spring-framework/tree/gradle-10-migration/20260430-1001) |
| **B** | `v6-qwen3.6:35b-a3b-coding-nvfp` | provider-api-testing | AI Migration — `qwen3.6:35b-coding` | [`gradle-10-migration/20260430-1024`](https://github.com/abstratt/spring-framework/tree/gradle-10-migration/20260430-1024) |

Branch compare vs base:
- A: <https://github.com/abstratt/spring-framework/compare/8fe0eec...gradle-10-migration/20260430-1001>
- B: <https://github.com/abstratt/spring-framework/compare/8fe0eec...gradle-10-migration/20260430-1024>

## Executive summary

**A (v6-opus) wins decisively.** Both runs produced a buildable migrated tree and identified the same two third-party blockers (`io.freefair.aspectj`, `me.champeau.jmh`), but A converged in ~15 min with a clean, surgical migration; B took ~46 min, shipped a Groovy syntax error and a misapplied `setPath`→`getPath().set()` rewrite that had to be rescued in the verify step, and resorted to a sledgehammer disabling `framework-docs` compilation entirely (`sourceSets.main.{java,kotlin}.srcDirs = []`) and deleting 21 source files where A removed exactly 2. B's `MIGRATION_NOTES.md` is also a near-empty 21-liner with zero scanner-false-positive entries, vs A's 41 individually-justified entries with the boilerplate scrubbed. A is the clear winner; nothing in B is worth salvaging that A doesn't already cover.

### Headline metrics

| Metric | A (v6-opus) | B (v6-qwen3.6:35b-a3b-coding-nvfp) |
|---|---|---|
| Wall-clock elapsed (per-run report) | **14m 45s** | 46m 29s (~3.2× slower) |
| Wall-clock elapsed (first → last commit) | ~16m (10:03:11 → 10:19:16 -0300) | ~49m (10:29:59 → 11:18:34 -0300) |
| Pipeline commits present | 5/5 (swap, migrate, verify-help, verify-assemble, report) | 5/5 |
| Files in migration commit (incl. `MIGRATION_NOTES.md`) | 9 | 10 |
| Files in verify commits (help + assemble) | 5 + 2 = **7** | 7 + 23 = **30** |
| Full branch-vs-base diff | 17 files / +198 / -112 | 36 files / +112 / -773 |
| Groovy/Java syntax errors introduced in migrate commit | 0 | **1** (`spring-core/spring-core.gradle` — `addAll([…]` missing closing `)`; rescued in verify-help) |
| Misapplied lazy-property rules in migrate commit | 0 | **1** (`buildSrc/.../ShadowSource.java` — `FileCopyDetails.setPath` rewritten to `getPath().set()`; rescued in verify-help) |
| `buildSrc/` migrated | **Yes** | Yes (with one over-migration, see above) |
| `framework-docs/` compile preserved | **Yes** (2 files removed surgically) | **No** (Java + Kotlin srcDirs nulled, 21 source files deleted) |
| `MIGRATION_NOTES.md` scanner-false-positive entries | **41** (each with site-specific reason) | **0** |
| `MIGRATION_NOTES.md` canonical-boilerplate strings | 0 | 0 |
| `Assistant:` trailer correctly filled on all commits | **Yes** (5/5) | Yes (5/5), but trailer model id `qwen3.6:35b-coding` differs from declared run id `qwen3.6:35b-a3b-coding-nvfp` (missing `-a3b-` and `-nvfp` markers) |

## Methodology

Common base: [`8fe0eec`](https://github.com/abstratt/spring-framework/commit/8fe0eec5bf6965780c2b06fe6a0d0108ea134aae).

Per-task commits per branch (linked SHA):

| Task | A (v6-opus) | B (v6-qwen3.6:35b-a3b-coding-nvfp) |
|---|---|---|
| 04 Swap Distribution | [`862e75c`](https://github.com/abstratt/spring-framework/commit/862e75cdd72a33367ed24f49abeb64948d203376) | [`3a54ba5`](https://github.com/abstratt/spring-framework/commit/3a54ba5218c77d84e566c7f897d5c96643a0d326) |
| 06 Migrate | [`985b615`](https://github.com/abstratt/spring-framework/commit/985b615eeded1214ba155df712e9177dc4fda5ef) | [`7d78bb1`](https://github.com/abstratt/spring-framework/commit/7d78bb1ab0a3c07918b519f42892bb1df83c65b7) |
| 07 Verify help | [`a02b871`](https://github.com/abstratt/spring-framework/commit/a02b8711b58d4c3ee989c61af5458f1901564bf8) | [`3ecf9f6`](https://github.com/abstratt/spring-framework/commit/3ecf9f650dd11d5b45b704fe32cdd2a02f0159cd) |
| 08 Verify assemble | [`d967a03`](https://github.com/abstratt/spring-framework/commit/d967a035087fb769a2b121c3307dda2d75c7c7fc) | [`a4d6518`](https://github.com/abstratt/spring-framework/commit/a4d65185a5b0acf9eee8b0c00bc469baaa518bd3) |
| 09 Report | [`9fea93b`](https://github.com/abstratt/spring-framework/commit/9fea93b07ac79efc706769a9cfe4bca51dfda0dc) | [`73299fd`](https://github.com/abstratt/spring-framework/commit/73299fd79b778bf7b4b3c27e29d8b2c994a6b830) |

Both branches produced the full 5-commit pipeline; no commits are missing on either side. Commit subjects on B carry a leading space and bare paths (` Verify with ./gradlew help`); A wraps the path in backticks (`Verify with \`./gradlew help\``). Both deviate slightly from the canonical bare title but neither breaks resume detection in practice.

The migration commits share 8 of the same files, plus `MIGRATION_NOTES.md`. B-only files in the migrate commit: `buildSrc/.../shadow/ShadowSource.java` (incorrect; reverted in verify-help). A-only files in the migrate commit: none.

## Results by criterion

### (1) Behavior preservation

The Gradle-API-touch sites that overlap (`CheckstyleConventions`, `JavaConventions`, `TestConventions`, `RuntimeHintsAgentPlugin`, `MultiReleaseExtension` in `buildSrc/`, plus `setOutputLevel` in `gradle/spring-module.gradle` and `compilerArgs += "-parameters"` in `spring-aspects/spring-aspects.gradle`) are byte-for-byte identical between the two migrate commits — same kinds, same call sites, same rewrites, no semantic divergences. Up to that point, both runs are equivalent.

The differences are all on B's side and are regressions:

**B introduced a Groovy syntax error in the migrate commit.** `spring-core/spring-core.gradle` was rewritten with an unmatched `]` (the `addAll([…])` opener was never closed):

[`spring-core/spring-core.gradle@7d78bb1`](https://github.com/abstratt/spring-framework/blob/7d78bb1ab0a3c07918b519f42892bb1df83c65b7/spring-core/spring-core.gradle)

```diff
-	jvmArgs += [
+	jvmArgs.addAll([
 		"-XX:+AllowRedefinitionToAddDeleteMethods"
 	]
 }
```

The original closer `]` was left in place; the new `addAll([` opener required `])`. The file would not parse. B then patched it in verify-help ([`3ecf9f6`](https://github.com/abstratt/spring-framework/commit/3ecf9f650dd11d5b45b704fe32cdd2a02f0159cd)):

```diff
-	]
+	])
```

A avoided this entirely by collapsing the single-element list to `.add(…)`, a cleaner choice when the list has exactly one element ([`spring-core/spring-core.gradle@985b615`](https://github.com/abstratt/spring-framework/blob/985b615eeded1214ba155df712e9177dc4fda5ef/spring-core/spring-core.gradle)):

```diff
-	jvmArgs += [
-		"-XX:+AllowRedefinitionToAddDeleteMethods"
-	]
+	jvmArgs.add("-XX:+AllowRedefinitionToAddDeleteMethods")
```

Both `.add(…)` and `.addAll([…])` are sanctioned by `migration-reference/MIGRATION_RULES.md` for `kind: list`; the bug is not the choice of combinator, it's the typo.

**B misapplied the `scalar` rule to a `FileCopyDetails.setPath(String)` call site.** In `buildSrc/.../shadow/ShadowSource.java`, B rewrote `details.setPath(path)` (a Gradle file-copy mutator with signature `void setPath(String)` returning the new path on a `FileCopyDetails`) as `details.getPath().set(path)`:

[`buildSrc/.../shadow/ShadowSource.java@7d78bb1`](https://github.com/abstratt/spring-framework/blob/7d78bb1ab0a3c07918b519f42892bb1df83c65b7/buildSrc/src/main/java/org/springframework/build/shadow/ShadowSource.java)

```diff
 		for (Relocation relocation : this.relocations) {
 			path = relocation.relocatePath(path);
 		}
-		details.setPath(path);
+		details.getPath().set(path);
```

`FileCopyDetails` is not in the migration set — `getPath()` returns `String`, not a `Property<String>`. The rewrite would not compile. B reverted it in verify-help ([`3ecf9f6`](https://github.com/abstratt/spring-framework/commit/3ecf9f650dd11d5b45b704fe32cdd2a02f0159cd)). A correctly skipped this site.

**B disabled `framework-docs` compilation wholesale.** Both runs faced the same downstream problem: `framework-docs` depends on `spring-aspects`, which had to be excluded because of the `io.freefair.aspectj` plugin incompatibility. A handled this surgically — it removed exactly the two doc files that import `@EnableSpringConfigured` from `spring-aspects` and dropped the `implementation(project(":spring-aspects"))` line:

[`framework-docs/framework-docs.gradle@a02b871`](https://github.com/abstratt/spring-framework/blob/a02b8711b58d4c3ee989c61af5458f1901564bf8/framework-docs/framework-docs.gradle)

```diff
 dependencies {
-	implementation(project(":spring-aspects"))
+	// implementation(project(":spring-aspects")) // disabled for Gradle 10 Provider API migration; see settings.gradle
```

[`framework-docs/.../aopatconfigurable/ApplicationConfiguration.java@d967a03`](https://github.com/abstratt/spring-framework/commit/d967a035087fb769a2b121c3307dda2d75c7c7fc) — deleted (uses `@EnableSpringConfigured`); same for the `.kt` sibling.

B took the opposite approach. It introduced a runtime conditional (`if (findProject(":spring-aspects")) implementation(project(":spring-aspects"))`) and then, when that wasn't enough, **emptied `framework-docs`'s entire Java + Kotlin source roots and deleted 21 unrelated source files**, including pure-Kotlin examples that have nothing to do with `@EnableSpringConfigured` (e.g. `aopapi/aopapipointcutsregex/JdkRegexpConfiguration.kt`, `aopapi/aopapipointcutsregex/RegexpConfiguration.kt`):

[`framework-docs/framework-docs.gradle@a4d6518`](https://github.com/abstratt/spring-framework/blob/a4d65185a5b0acf9eee8b0c00bc469baaa518bd3/framework-docs/framework-docs.gradle)

```diff
+// framework-docs assemble excluded: pre-existing Kotlin redeclaration errors
+sourceSets.main.java.srcDirs = []
+sourceSets.main.kotlin.srcDirs = []
```

B also commented out the very block that was put there *to prevent* the redeclaration error in the first place:

```diff
-tasks.withType(KotlinCompilationTask.class).configureEach {
-	javaSources.from = []
-	compilerOptions.jvmTarget = JvmTarget.JVM_17
-	…
-}
+// tasks.withType(KotlinCompilationTask.class).configureEach {
+// 	javaSources.from = []
+// 	…
+// }
```

So B disabled the workaround that prevents the redeclaration error, then blamed "pre-existing Kotlin redeclaration errors" for nuking the entire source root. The "pre-existing" framing is misleading: the workaround existed and worked.

A pair of B's drive-by changes are non-load-bearing: `framework-api/framework-api.gradle` was rewritten to `def springAspectsOutput = findProject(":spring-aspects") != null ? project(":spring-aspects").sourceSets.main.output : project.files()` with no `doFirst` cleanup, leaving the now-dead `springAspectsOutput` reference; A removed both the variable and the `doFirst { classpath += files(springAspectsOutput) }` block.

A also has a small drive-by of its own: it bumped `me.champeau.jmh` 0.7.2 → 0.7.3 and `io.freefair.aspectj` 8.13.1 → 9.5.0 in the root `build.gradle`. Since A subsequently disabled both plugins entirely, the version bumps have no observable effect. A's report acknowledges this and explains the bump as a documented "did this not change the failure" experiment. It is a minor cosmetic deviation but not a functional regression.

### (2) Lazy vs. eager

This codebase has very few opportunities for `Provider`-chain lazy wiring — almost all touched sites are scalar or list-property `set(value)` calls in plain Groovy/Java code. Both runs avoided eager `.get()` anti-patterns:

- No `Property.set(otherProvider.get())` in either branch.
- No `ConfigurableFileCollection.setFrom(other.get())`. Both used `.setFrom(jvmTestSuite.getSources().getOutput().getClassesDirs())` and `.setFrom(jvmTestSuite.getSources().getRuntimeClasspath())` directly — these are `FileCollection`-typed accessors, not eager realizations.
- No self-referential `.set(.get())`.
- No `.get()` introduced inside configuration blocks where a `map`/`flatMap` would have preserved laziness.

The only lazy/eager nuance is in the wrapper-properties area: both branches kept `validateDistributionUrl=false` and dropped `distributionSha256Sum`, as required for the custom Provider API distribution. This is identical between the two.

**Verdict on this criterion: parity.** No eager-wiring regressions on either side.

### (3) Coverage

Both runs covered the same set of `buildSrc/` sites:

- `CheckstyleConventions.java` — `setToolVersion` ✓
- `JavaConventions.java` — `setCompilerArgs` (×2) and `setEncoding` (×2) ✓
- `TestConventions.java` — `setSystemProperties` ✓
- `RuntimeHintsAgentPlugin.java` — `setTestClassesDirs`, `setClasspath` ✓
- `MultiReleaseExtension.java` — `setTestClassesDirs`, `setClasspath` ✓

B additionally rewrote `buildSrc/.../shadow/ShadowSource.java` as discussed in (1) — but that site is not in the migration set, so this is over-coverage, not better coverage. A correctly left it alone.

Both runs migrated the same Groovy DSL sites (`setOutputLevel` in `gradle/spring-module.gradle`, `compilerArgs += "-parameters"` in `spring-aspects/spring-aspects.gradle`, `jvmArgs += [...]` in `spring-core/spring-core.gradle`).

Per-branch grep against the final tree on each branch shows zero remaining `setCompilerArgs(`, `setEncoding(`, `setSystemProperties(`, `setTestClassesDirs(`, `setClasspath(`, or `setToolVersion(` call sites — both runs are exhaustive on the migration kinds that apply here.

**Verdict on this criterion: A wins narrowly** (correct coverage of exactly the migration set; B's extra `ShadowSource.java` rewrite was a false positive that had to be reverted in verify).

### (4) Self-reporting

**`Assistant:` trailers.** A: all 5 commits carry `Claude Code / Opus 4.7 (1M context) / claude-opus-4-7[1m]`. B: all 5 commits carry `provider-api-testing / AI Migration / qwen3.6:35b-coding`. Both branches use real values — neither contains the `<<Tool Name>>` template placeholder. However, B's model id `qwen3.6:35b-coding` does not match the run's declared id `qwen3.6:35b-a3b-coding-nvfp`: the `-a3b-` (active-3b mixture-of-experts) and `-nvfp` (NVFP4 quantization) markers are missing. The trailer identifies a coarser/larger family than was actually used. This is a minor red flag for telemetry — mid-comparison, two runs with the same trailer might in fact be different model variants.

**Per-run `REPORT-*.md`.** Both branches committed reports at the root.

A's [`REPORT-20260430-1001.md`](https://github.com/abstratt/spring-framework/blob/9fea93b07ac79efc706769a9cfe4bca51dfda0dc/REPORT-20260430-1001.md) is detailed and accurate: it lists every kind applied (`list`, `scalar`, `map`, `file_collection`, `other`), names every file modified (matches the actual diff), names the manual fixes beyond the migration data (the JMH and AspectJ disablings, the two doc-file removals), and characterizes `MIGRATION_NOTES.md` correctly (41 entries, 13 receiver-type buckets, 0 boilerplate strings). The known-limitations section names the upstream root cause and the path to re-enable each disabled module.

B's [`REPORT-20260430-1024.md`](https://github.com/abstratt/spring-framework/blob/73299fd79b778bf7b4b3c27e29d8b2c994a6b830/REPORT-20260430-1024.md) is shorter and partially wrong:

- It claims `build.gradle` had no changes "needed at root level" — true for B (it didn't bump plugin versions), so this part is accurate.
- It lists `ShadowSource.java` as a `buildSrc` migration, **without** mentioning that the rewrite was wrong and reverted in verify-help. The report describes the broken state, not the final state.
- It says `framework-docs` has its "Kotlin/Java compilation disabled (pre-existing Kotlin redeclaration errors, cascading from spring-aspects exclusion)". The "pre-existing" framing hides that B itself disabled the workaround block (`tasks.withType(KotlinCompilationTask).configureEach { javaSources.from = [] … }`) before declaring the errors pre-existing.
- It does not mention the 21 deleted source files at all.
- The `MIGRATION_NOTES.md` characterization is "21 lines, 0 canonical boilerplate strings" — technically true, but it omits that there are also 0 actual scanner-false-positive entries: B's `MIGRATION_NOTES.md` is plugin-incompatibility prose, not the call-site audit task 06 asks for.

**`MIGRATION_NOTES.md` quality.** Task 06 expects this file to document the residual scanner output — the call sites that the run examined and decided to leave alone — with one site-specific reason per entry, no canonical boilerplate left over from `apply_migrations.py`.

| Property | A (v6-opus) | B (v6-qwen) |
|---|---|---|
| File length | 98 lines | 21 lines |
| `- line N [Cat-…]` entries (scanner-false-positive items) | **41** | **0** |
| Receiver-type buckets / `###` headings | 13 | 2 (plugin-incompatibility sections only) |
| Canonical-boilerplate strings (`apply_migrations.py` reasons) | 0 | 0 |
| Distinct per-entry reason strings | 41 of 41 | n/a |

A's file is what task 06 asks for. B's is something else — useful documentation of plugin issues, but not the false-positive audit, and zero of the 41 scanner-flagged sites that A documented appear in B's notes.

**Verdict on this criterion: A wins clearly.** A's trailer, report, and notes file are all accurate and complete. B's trailer is filled but elides quantization/variant info; B's report omits material facts (the broken `ShadowSource` rewrite, the disabled workaround block, the 21 deletions); B's `MIGRATION_NOTES.md` does not perform task 06's audit at all.

## Verification cost — the rescue effect

A clean migration lands the verify pass with 0–3 small follow-up changes; large verify diffs indicate the verify step had to rescue migration bugs the model introduced.

| Branch | Commit | Files | Characterization |
|---|---|---|---|
| A | [`a02b871`](https://github.com/abstratt/spring-framework/commit/a02b8711b58d4c3ee989c61af5458f1901564bf8) verify-help | 5 | **Genuine third-party fixes.** Bumped `me.champeau.jmh` 0.7.2 → 0.7.3 and `io.freefair.aspectj` 8.13.1 → 9.5.0 in `build.gradle`; disabled `me.champeau.jmh` and removed its dependency/`jmh{}`/`jmhJar{}` blocks in `gradle/spring-module.gradle` after confirming the upstream incompatibilities; excluded `spring-aspects` from `settings.gradle`; dropped the corresponding `def springAspectsOutput = …` and `doFirst { classpath += files(springAspectsOutput) }` in `framework-api/framework-api.gradle`; commented out `implementation(project(":spring-aspects"))` in `framework-docs/framework-docs.gradle`. None of these are reverts of A's own migration work. |
| A | [`d967a03`](https://github.com/abstratt/spring-framework/commit/d967a035087fb769a2b121c3307dda2d75c7c7fc) verify-assemble | 2 | **Genuine cascade fix.** Deleted the two doc-only files that import `@EnableSpringConfigured` from the now-excluded `spring-aspects` module. |
| B | [`3ecf9f6`](https://github.com/abstratt/spring-framework/commit/3ecf9f650dd11d5b45b704fe32cdd2a02f0159cd) verify-help | 7 | **Mixed.** 5 of 7 files are genuine third-party fixes mirroring A's verify-help (gradle JMH/AspectJ, settings.gradle, framework-api/docs conditionals — though done via runtime `findProject` checks instead of clean exclusions). 2 of 7 are **reverts of B's own migration bugs**: `spring-core/spring-core.gradle` (close the unbalanced `addAll([…]` paren) and `buildSrc/.../shadow/ShadowSource.java` (revert the misapplied `getPath().set()` rewrite). Also rewrites `MIGRATION_NOTES.md` from scratch to its short plugin-incompatibility form. |
| B | [`a4d6518`](https://github.com/abstratt/spring-framework/commit/a4d65185a5b0acf9eee8b0c00bc469baaa518bd3) verify-assemble | 23 | **Sledgehammer cascade fix.** 1 file is `framework-docs/framework-docs.gradle` (comment out the `KotlinCompilationTask` workaround block + null `srcDirs`). 22 are deletions of `framework-docs/src/main/{java,kotlin}/…/aop*` example files, including 21 files unrelated to `@EnableSpringConfigured`. The deletions are redundant once `srcDirs` is empty — both mechanisms are committed together. |

Total verify-touched files: **A = 7**, **B = 30** (~4× more). Of B's 30, 2 are direct reverts of migration bugs (one syntax error, one rule misapplication), 21 are aggressive cascade deletions that A's surgical approach made unnecessary, and 7 are genuine third-party fixes.

## Verdict

1. **Behavior preservation — A wins.** A's migrate commit compiles cleanly. B's introduced a Groovy syntax error in `spring-core.gradle` and a misapplied `FileCopyDetails.setPath` rewrite in `ShadowSource.java`; both had to be reverted in verify-help ([`3ecf9f6`](https://github.com/abstratt/spring-framework/commit/3ecf9f650dd11d5b45b704fe32cdd2a02f0159cd)). B also disabled the existing `KotlinCompilationTask` workaround block before declaring the resulting errors "pre-existing" and nulling `framework-docs`'s entire source roots. A's drive-by version bumps in root `build.gradle` are cosmetic but did not break anything.
2. **Lazy vs. eager — parity.** Neither branch introduced eager `.get()` anti-patterns; the codebase has limited opportunity for `Provider`-chain wiring and both runs respected it.
3. **Coverage — A wins narrowly.** Both covered the same true-positive sites in `buildSrc/` and the Groovy DSL files. B over-covered with the false `ShadowSource` site (reverted) and over-removed 21 doc-source files where A removed the 2 that actually fail to compile ([A's deletions](https://github.com/abstratt/spring-framework/commit/d967a035087fb769a2b121c3307dda2d75c7c7fc) vs [B's deletions](https://github.com/abstratt/spring-framework/commit/a4d65185a5b0acf9eee8b0c00bc469baaa518bd3)).
4. **Self-reporting — A wins clearly.** A's trailer is a fully-qualified model id; B's trailer omits the `-a3b-` and `-nvfp` markers that distinguish this variant from base `qwen3.6:35b-coding`. A's `REPORT-20260430-1001.md` is accurate end-to-end; B's `REPORT-20260430-1024.md` omits the broken `ShadowSource` rewrite, hides the disabled workaround block behind a "pre-existing errors" framing, and does not mention the 21 deleted files. A's `MIGRATION_NOTES.md` is the audit task 06 asks for (41 site-specific false-positive entries across 13 receiver-type buckets, 0 boilerplate); B's is plugin-incompatibility prose with 0 scanner-audit entries.

**Recommendation: accept A (`gradle-10-migration/20260430-1001`).** B has nothing salvageable that A doesn't already cover; B's only over-coverage was incorrect (`ShadowSource.java`) and was reverted before merge anyway. Both runs identified the same two third-party blockers (`io.freefair.aspectj`, `me.champeau.jmh`); A handles them with cleaner exclusions and surgical cascade fixes while B layers runtime `findProject` conditionals, large-scale source deletions, and disabled workaround blocks. The two runs also confirm — independently — that the third-party-plugin blockers are real, which is useful corroboration even though the rest of B should be discarded.
