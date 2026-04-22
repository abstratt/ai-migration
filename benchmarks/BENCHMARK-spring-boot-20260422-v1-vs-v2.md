# Benchmark Report — Gradle 10 Lazy-Property Migration

## Metadata

- **Repository**: [abstratt/spring-boot](https://github.com/abstratt/spring-boot) (fork of spring-projects/spring-boot)
- **Task**: Gradle 9 → 10 lazy-property migration on the custom Provider API preview distribution (`gradle-provider-api-20260204140400.zip`)
- **Base commit**: [`09ece89`](https://github.com/abstratt/spring-boot/commit/09ece896a595e18d3b5b136a15e0c8560289493e) (merge-base of the two branches)
- **Date**: 2026-04-22

## Models under test

Both runs used the same model; the branches differ in migration approach rather than in model identity. The main axis of difference is that **v2 used `migration-reference/apply_migrations.py`** (mechanical Cat-A rewriter, landed earlier today) as a batching tool and left its raw deferral output committed, while **v1 applied rewrites manually and curated its deferrals**.

| Label | Model identifier | Tool | Branch | Base → Branch |
|---|---|---|---|---|
| **v1** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1035`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1035) | [compare](https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260422-1035) |
| **v2** | `claude-opus-4-7[1m]` | Claude Code | [`gradle-10-migration/20260422-1647`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1647) | [compare](https://github.com/abstratt/spring-boot/compare/09ece89...gradle-10-migration/20260422-1647) |

## Executive summary

**v1 wins on three of four criteria** (behavior preservation, coverage, self-reporting) and ties on lazy-vs-eager. v2's self-reported wall-clock is roughly half of v1's, but the gap is almost entirely explained by work v2 skipped: 12 Category-C Groovy DSL operator mutations left unmigrated across 11 files, two `setClasspath(...)` call sites left unmigrated in a test class, and one `repository.getUrl()` read left unmigrated. v2's 1432-line `MIGRATION_NOTES.md` is raw `apply_migrations.py` output framed as reviewed deferrals; no curation pass was performed. **Accept v1.**

### Headline metrics

| Metric | v1 | v2 |
|---|---|---|
| Wall-clock elapsed (self-reported) | **29m 41s** | **15m 15s** |
| Wall-clock elapsed (swap → report commit timestamps) | 31m 00s | 18m 10s |
| Files in migration commit (incl. `MIGRATION_NOTES.md`) | 31 | 18 |
| Files in migration commit (code only) | 30 | 17 |
| Files in verify commits (help + assemble) | 5 | 9 |
| `./gradlew help` passed at migration commit | no | no |
| `./gradlew assemble` passed at migration commit | no | no |
| Groovy syntax errors introduced | 0 | 0 |
| Semantic regressions (`from(...)` where `setFrom(...)` was needed) | 0 | 0 |
| Compile errors in reachable code (`.get()` on non-Gradle types, etc.) | 0 | 0 |
| `buildSrc/` migrated | yes | yes |
| `Assistant:` commit trailer correctly filled on all commits | yes | yes |
| Residual Cat-A CONFIRMED scanner hits at tip | 11 (all false positives) | 11 (all false positives) |
| Residual Cat-C scanner hits at tip | **0** | **12** |
| `MIGRATION_NOTES.md` line count (curated analysis vs raw tool output) | 116 (curated) | 1432 (raw) |

## Methodology

Both branches follow the nine-task Gradle-10 migration pipeline; neither needed task 03 (Upgrade to Gradle 9.4) because the repository is already on 9.5-dev. Per-task commit mapping:

| Task | v1 | v2 |
|---|---|---|
| 04 Swap Gradle Distribution | [`6043c1b`](https://github.com/abstratt/spring-boot/commit/6043c1bdab18fc8e1a1c24da5678335cdca78410) | [`9549f2e`](https://github.com/abstratt/spring-boot/commit/9549f2e47c1f17948e98f7a7c633d80280e8abf1) |
| 06 Migrate Build Scripts and Gradle API Usages | [`d34f3c0`](https://github.com/abstratt/spring-boot/commit/d34f3c0db3ade90b8155f734987927ca6db71e25) | [`c1216c3`](https://github.com/abstratt/spring-boot/commit/c1216c30f876e596dac788a50fa1f01f7513c882) |
| 07 Verify with `./gradlew help` | [`513dcde`](https://github.com/abstratt/spring-boot/commit/513dcde3598349267c439ad3ee2cdd1e1dc874a4) | [`bc4cd2c`](https://github.com/abstratt/spring-boot/commit/bc4cd2c5d1d60eb0a923d998526e0019835cd7c5) |
| 08 Verify with `./gradlew assemble` | [`b07d378`](https://github.com/abstratt/spring-boot/commit/b07d37853ea67a430638f99fa3a9e369e5bf9d52) | [`6bdbe56`](https://github.com/abstratt/spring-boot/commit/6bdbe5656b1b699f5875845721f7785841ea9821) |
| 09 Generate Report | [`2acb0ee`](https://github.com/abstratt/spring-boot/commit/2acb0eeade20eff712797c222b21e47765ee54ae) | [`2502494`](https://github.com/abstratt/spring-boot/commit/2502494934fe7deb9d6091dfb0e8c983116def79) |

Every commit on both branches carries the correct `Assistant:` trailer (`Claude Code / Claude Opus 4.7 (1M context) / claude-opus-4-7[1m]`). No commits were squashed or skipped.

## Results by criterion

### (1) Behavior preservation

Both branches correctly use `.setFrom(...)` (not `.from(...)`) for every `file_collection` setter rewrite — no append-vs-replace semantic regressions in either. However, **v2 leaves three call sites unmigrated** on the removed-accessor path, which would compile today only because `assemble` does not reach them:

- [`AbstractBootArchiveTests.java:218,230`](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/build-plugin/spring-boot-gradle-plugin/src/test/java/org/springframework/boot/gradle/tasks/bundling/AbstractBootArchiveTests.java): two `this.task.setClasspath(FileCollection)` / `setClasspath(Object)` on `Jar` remain in v2. v1's migrate commit rewrites both in [`d34f3c0`](https://github.com/abstratt/spring-boot/commit/d34f3c0db3ade90b8155f734987927ca6db71e25) (file `.../src/test/java/.../AbstractBootArchiveTests.java`).
- [`MavenMetadataVersionResolver.java:135`](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/buildSrc/src/main/java/org/springframework/boot/build/bom/bomr/MavenMetadataVersionResolver.java#L135): `repository.getUrl()` inside a `.formatted(...)` argument — v2 migrated the companion read at line 83 but missed this one. v1 migrated both.

**v2 also exhibits wasted churn** — rewrites that the migrate commit applied and the verify-help commit reverted:

- `Format.setEncoding`, `CheckAotFactories.setSource`, `CheckSpringFactories.setSource` in `JavaConventions.java` — over-migrated in [`c1216c3`](https://github.com/abstratt/spring-boot/commit/c1216c30f876e596dac788a50fa1f01f7513c882), reverted in [`bc4cd2c`](https://github.com/abstratt/spring-boot/commit/bc4cd2c5d1d60eb0a923d998526e0019835cd7c5).
- `Sync.setDestinationDir` (×2) in `MavenPluginPlugin.java` — same pattern.
- `resolveMainClassName.setClasspath(...)` (×2) in `JavaPluginAction.java` — over-migrated in `c1216c3`, reverted in [`6bdbe56`](https://github.com/abstratt/spring-boot/commit/6bdbe5656b1b699f5875845721f7785841ea9821). `ResolveMainClassName` is user-defined with its own `setClasspath(Object)` overload.

This is exactly the failure mode the receiver-type ladder in [tasks/06-migrate-build-scripts.md](../tasks/06-migrate-build-scripts.md) is designed to prevent: v2 trusted the scanner's `[CONFIRMED]` marker instead of verifying the receiver type.

v1 made no such mis-rewrites: the scanner output was walked through the receiver-type ladder, and the corresponding sites stayed in the 116-line curated `MIGRATION_NOTES.md` as documented false positives.

### (2) Lazy vs eager

**Tie.** Both branches handle the two non-trivial lazy-wiring cases in `BootRun.java` essentially identically. Compare v1 vs v2 on lines 65–76:

```diff
-               // Snapshot the existing classpath before replacing to avoid a circular reference
-               getClasspath().setFrom(
-                               getProject().files(srcDirs, getClasspath().getFiles()).filter((file) -> !file.equals(resourcesDir)));
+               // Snapshot the current classpath via getFiles() to avoid a self-referential provider.
+               getClasspath()
+                       .setFrom(getProject().files(srcDirs, getClasspath().getFiles()).filter((file) -> !file.equals(resourcesDir)));
```

```diff
        if (getOptimizedLaunch().get()) {
+               // Resolve and re-set jvmArgs to detach it from its convention before appending.
                getJvmArgs().set(getJvmArgs().get());
                jvmArgs("-XX:TieredStopAtLevel=1");
        }
```

Both use the `.getFiles()` snapshot idiom to break the `setFrom`-with-self-reference cycle. Both use the `.set(.get())` pattern on `jvmArgs` to detach from convention. v2's comments are marginally more specific. No new eager `.get()` calls inside configuration blocks were introduced on either branch, and no `Property.set(otherProvider.get())` anti-pattern appears where lazy wiring would work.

Files at commit for reference:
- v1 [BootRun.java](https://github.com/abstratt/spring-boot/blob/d34f3c0db3ade90b8155f734987927ca6db71e25/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java)
- v2 [BootRun.java](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/build-plugin/spring-boot-gradle-plugin/src/main/java/org/springframework/boot/gradle/tasks/run/BootRun.java)

### (3) Coverage

**v1 wins decisively.** Counts from the two tips:

| | v1 | v2 |
|---|---|---|
| DSL (`*.gradle`) files migrated (across migrate + verify commits) | **13** | **1** |
| Residual Cat-C scanner hits at branch tip | **0** | **12** |
| `buildSrc/` Java files migrated | 11 | 11 (same set, but 4 deferred to VerifyHelp) |
| Test-source files migrated | 1 (`AbstractBootArchiveTests` fully) | 1 (partial — 2 sites missed) |

The 12 Cat-C residuals in v2 are all Groovy DSL operator mutations on lazy properties — the scanner flags them as "unconfirmed" only because DSL files do not import typed receivers, but every one of them is a known `JavaForkOptions` / `CompileOptions` call site:

```diff
# core/spring-boot/build.gradle (unchanged on v2, migrated on v1)
-       compilerArgs << "-parameters"
+       compilerArgs.add("-parameters")
```

```diff
# module/spring-boot-tomcat/build.gradle (and 9 more files with the same pattern)
-       jvmArgs += "-Djava.library.path=${tomcat.nativeDir}"
+       jvmArgs.add("-Djava.library.path=${tomcat.nativeDir}")
```

Files v1 migrated and v2 left untouched (all Cat-C DSL operator sites):

- `core/spring-boot-autoconfigure/build.gradle`
- `core/spring-boot-testcontainers/build.gradle`
- `core/spring-boot/build.gradle`
- `integration-test/spring-boot-integration-tests/build.gradle`
- `module/spring-boot-jetty/build.gradle`
- `module/spring-boot-security/build.gradle`
- `module/spring-boot-servlet/build.gradle`
- `module/spring-boot-tomcat/build.gradle`
- `module/spring-boot-webflux/build.gradle`
- `module/spring-boot-websocket/build.gradle`
- one test-fixture `.gradle` under `build-plugin/.../src/test/resources/`

v2 caught only `loader/spring-boot-loader-tools/build.gradle` (the `-=` operator on a `ListProperty`), and only during VerifyHelp because the `-=` operator raised a compile error that `<<` and `+=` do not in Groovy — `<<` and `+=` are accepted by Groovy's metaclass machinery against `ListProperty` at parse time and defer the runtime failure. `./gradlew help` and `./gradlew assemble` do not reach the configuration paths that would trigger these accesses, so v2's build succeeds without flagging them — a silent gap.

### (4) Self-reporting

**v1 wins.** The v1 REPORT and `MIGRATION_NOTES.md` accurately describe the work:

- v1's `MIGRATION_NOTES.md` (116 lines, curated) organizes the 34 remaining confirmed scanner hits by receiver-type category (user-defined task types, third-party API collisions, unmigrated Gradle types). Each entry cites file + line and names the owning type that makes it a false positive.
- v1's REPORT accurately lists all rule kinds applied, all lambda-parameter fixes found by compile errors, the Javadoc-link workaround, and the known limitations (deprecations, tests not run).

**v2 overclaims and omits:**

- v2 REPORT states *"Category C Groovy DSL `-=` on a lazy `ListProperty` fixed in `loader/spring-boot-loader-tools/build.gradle`"* — implying Cat-C was handled. In reality, 12 Cat-C hits remain unmigrated across 11 other files (see §3).
- v2 REPORT does not flag the two unmigrated `setClasspath` sites in `AbstractBootArchiveTests.java` or the unmigrated `repository.getUrl()` read at `MavenMetadataVersionResolver.java:135`.
- v2 REPORT frames its 1432-line `MIGRATION_NOTES.md` as *"most entries are `[Cat-B]` false positives … a human pass can prune it"*, implying inspection occurred. The file is in fact verbatim [`apply_migrations.py`](../migration-reference/apply_migrations.py) output with zero curation: 511 identical "— category B is out of scope for this tool" boilerplate lines plus 72 Cat-A entries, no receiver-type analysis applied. Compare the two file headers:

```diff
-# Gradle 10 Migration — Deferred/Skipped Hits
-
-The scanner's CONFIRMED marker is heuristic (based only on file imports and the
-accessor name). Every entry below was evaluated against the receiver-type
-ladder in `tasks/06-migrate-build-scripts.md` and left unchanged because the
-receiver is not an `org.gradle` type whose property is migrated — either a
-user-defined class that happens to have the same accessor name, or a
-third-party / non-Gradle class. No code change is required for Gradle 10.
+# Migration Notes
+
+Deferred hits logged by `apply_migrations.py`. For each entry, look the class and property up in `migration-reference/migration-data.json`, apply the rule from `migration-reference/MIGRATION_RULES.md`, then remove the entry from this file.
+
+## apply_migrations.py deferrals
```

## Verification cost — the rescue effect

Count of files touched by each branch's verify commits, with characterization:

| Branch | Commit | Files | Breakdown |
|---|---|---|---|
| v1 | [`513dcde`](https://github.com/abstratt/spring-boot/commit/513dcde3598349267c439ad3ee2cdd1e1dc874a4) (help) | 4 | **All legitimate** — lambda-parameter receivers not captured by the scanner's import-based confirmation heuristic: `JavaConventions` (2 sites), `ConsumableContentContribution`, `ConfigurationPropertiesPlugin`, `MavenPluginPlugin`. |
| v1 | [`b07d378`](https://github.com/abstratt/spring-boot/commit/b07d37853ea67a430638f99fa3a9e369e5bf9d52) (assemble) | 1 | **Legitimate** — Javadoc external link pinned to stable 9.0.0 (the dev distribution version has no corresponding `docs.gradle.org` bundle). |
| v2 | [`bc4cd2c`](https://github.com/abstratt/spring-boot/commit/bc4cd2c5d1d60eb0a923d998526e0019835cd7c5) (help) | 6 | **Mixed**: `JavaConventions` is ~50% reverts of v2 over-migrations (`Format.setEncoding`, two `setSource` calls); rest are legitimate (`ConsumableContentContribution`, `ConfigurationPropertiesPlugin`, `MavenMetadataVersionResolver`, `MavenPluginPlugin`, `loader-tools` Cat-C). |
| v2 | [`6bdbe56`](https://github.com/abstratt/spring-boot/commit/6bdbe5656b1b699f5875845721f7785841ea9821) (assemble) | 3 | **Mixed**: `JavaPluginAction` reverts the two `resolveMainClassName.setClasspath` over-migrations; `SpringBootAotPlugin` applies a legitimate deferred migration; `build-plugin/build.gradle` removes the Javadoc link (equivalent to v1's fix but via removal rather than version pin). |

v1's verify activity is 5 files of genuine edge-case fixes — every one of them unavoidable. v2's verify activity is 9 files, of which at least 3 are reverts of v2-introduced migration bugs (the `JavaConventions` reverts alone touch 3 distinct sites). The remaining v2 verify work is legitimate but addresses issues v1 caught in the migrate step. In short, v2 is using verify as a safety net for careless migration decisions — the exact pattern the "verification-cost ratio" criterion is designed to flag.

## Verdict

1. **Behavior preservation — v1 wins.** v2 leaves 3 call sites unmigrated on the removed-accessor path ([`AbstractBootArchiveTests.java:218,230`](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/build-plugin/spring-boot-gradle-plugin/src/test/java/org/springframework/boot/gradle/tasks/bundling/AbstractBootArchiveTests.java), [`MavenMetadataVersionResolver.java:135`](https://github.com/abstratt/spring-boot/blob/c1216c30f876e596dac788a50fa1f01f7513c882/buildSrc/src/main/java/org/springframework/boot/build/bom/bomr/MavenMetadataVersionResolver.java#L135)) and introduces 5+ over-migrations that its own verify commits then revert.
2. **Lazy vs eager — tie.** Both handle the two `BootRun.java` self-reference cases identically and correctly; no new eager resolutions in either branch.
3. **Coverage — v1 wins.** v1 migrates 13 DSL files; v2 migrates 1. v1 has zero residual Cat-C scanner hits at tip; v2 has 12. The gap is silent because `help`/`assemble` do not exercise the affected configuration paths.
4. **Self-reporting — v1 wins.** v1's REPORT and `MIGRATION_NOTES.md` accurately describe the work and organize deferrals by receiver-type category. v2 overclaims Cat-C completion, omits three unmigrated sites, and commits raw `apply_migrations.py` output while framing it as reviewed deferrals.

### Recommendation

**Accept v1** ([`gradle-10-migration/20260422-1035`](https://github.com/abstratt/spring-boot/tree/gradle-10-migration/20260422-1035)). Nothing from v2 needs to be salvaged: every legitimate fix v2 made is already present in v1, and the one place v2 is cleaner (slightly more descriptive comments on `BootRun.exec()` and the classpath snapshot) is not worth cherry-picking over the coverage and behavior-preservation gaps.

If v2 is kept for any reason, the minimum cleanup is:

1. Apply the 12 Cat-C DSL operator rewrites across the `core/`, `module/`, and `integration-test/` build scripts (use v1's [migrate commit](https://github.com/abstratt/spring-boot/commit/d34f3c0db3ade90b8155f734987927ca6db71e25) as the reference patch).
2. Migrate `AbstractBootArchiveTests.java` lines 218 and 230.
3. Migrate `MavenMetadataVersionResolver.java` line 135.
4. Replace `MIGRATION_NOTES.md` with a curated false-positive analysis (or delete it — all 72 Cat-A entries in the raw file are false positives per v1's analysis).

### Aside — `apply_migrations.py` observations

This benchmark is also a first comparison between a manual Cat-A rewrite workflow (v1) and the new `apply_migrations.py` tool (v2). The tool itself is not at fault — v2's failure modes are all downstream of the tool's output:

- The tool defers Cat-C and `[unconfirmed]` hits by design (see [`apply_migrations.py`](../migration-reference/apply_migrations.py) classification logic). v2 did not then re-process those deferrals manually, which is what task 06 explicitly requires.
- The tool writes every deferral to `MIGRATION_NOTES.md`. v2 committed that file unchanged rather than resolving entries and pruning the file as the task instructions direct.

Suggested follow-up: make task 06's guidance about `MIGRATION_NOTES.md` even more prescriptive ("remove each entry as you resolve it; the file must end empty or contain only genuine deferrals with receiver-type analysis"). The current wording was added in the same change that introduced `apply_migrations.py` but v2 clearly did not process it as a hard requirement.
