---
name: provider-api-build-comparison
description: Semantic before/after comparison of a migrated project's build. Builds the baseline commit on the released Gradle and the migration branch tip on the Provider API branch distribution, dumps task graph and task inputs/outputs (inputs read through the eager-getter adapters), classifies every difference with a reason mnemonic, and publishes the report and the index under semantic-comparisons/. Use when asked to compare, re-compare, or regenerate the semantic comparison / task-dump comparison for a project (or all projects) before vs after the Provider API migration, or to list which projects have been compared and when.
---

# Provider API migration: semantic before/after build comparison

Goal: show, for one project at a time, that building the migrated project on the Provider API
branch distribution gives the same task graph, the same task inputs (by **eager-API semantics**) and the
same build products as building the unmigrated project on the released Gradle, and explain every
difference that remains.

Not to be confused with `comparisons/COMPARISON-*.md` (`/g10-compare`), which compares two *migration runs*
of a project; this skill compares the project's *build* before and after one migration.

## Where things are (paths relative to the repo root)

| Path | What |
|---|---|
| `semantic-comparisons/README.md` | The index: one row per project (migration size, differing tasks, adapters yes/no, last run, headline), cross-project difference tables, caveats. **Published output.** |
| `semantic-comparisons/REPORT-<project>.md` | One report per project. **Published output.** Also the record of each project's settings (commits, JDK, extra args, included builds) for reruns. |
| `out/task-compare-g992/` | Workspace (git-ignored): `gradle-local/` (branch distribution), `<project>/repo` (clone of the fork), `<project>/before`, `<project>/after` (worktrees), dumps, logs, comparison output, `control/`, `pre-adapter/` (superseded runs). |
| this skill's `scripts/` | `task-dump.init.gradle` (adapter-aware; source of truth, `out/task-compare-g992/tools/` holds an older copy), `compare_dumps.py`, `classify_diffs.py`, `skip-kotlin-metadata-check.init.gradle` |
| this skill's `references/tool-README.md` | Dump format, flags, limitations |

## Discovering projects

There is no fixed list. A project is eligible when the migration produced a branch for it:

- `NEXT_REPOSITORIES.md` ("Completed runs") and `comparisons/COMPARISON-<project>-*.md` name the migrated projects;
- the migrated fork is `https://github.com/abstratt/<project>`, with branches `gradle-10-migration/<timestamp>-<pair-id>`
  (`git ls-remote --heads https://github.com/abstratt/<project> 'gradle-10-migration/*'`). Use the branch for the
  pair currently being compared (now `…-g951-to-PAPI-20260609`); if several, the newest timestamp, unless the
  existing report names another;
- already compared: `semantic-comparisons/REPORT-*.md` and the index; workspaces in `out/task-compare-g992/*/`.

Commits for a project:
- **after** = the migration branch tip;
- **before** = the parent of the branch's "Swap Gradle Distribution" commit (normally the "Upgrade Baseline Gradle"
  commit; if the project was already on the baseline version, the upstream commit the branch started from).
  Check with `git log --oneline -8 <branch>`.

Per-project settings come from the project's existing report header (JVM row, the command line, included
builds, workarounds). For a new project, find the JDK the build needs (toolchain config, CI workflow,
`.sdkmanrc`; JDKs are in `~/.sdkman/candidates/java/`), and check whether it has `buildSrc` or included builds
(`settings.gradle*`: `includeBuild`).

When asked which projects were compared and when: read the index, and for each workspace take the
modification time of the newest `out/task-compare-g992/<project>/dump-after*.json`.

## Eager-API semantics: the adapters

A lazy property that replaced an eager one is annotated `@ReplacesEagerProperty`. For code compiled
against an older Gradle, the bytecode upgrade routes calls to the old getter to a static accessor:

- default: `org.gradle.internal.classpath.generated.<DeclaringType>_Adapter.access_get_<originalAccessorName>(owner)`, e.g. `Delete_Adapter.access_get_isFollowSymlinks`;
- custom adapter (`adapter = X.class`): `<package>.$$BridgeFor$$<Outer>$$<X>.access_get_<method>(owner)`.

The init script reads every input property that has such an accessor through it, and records the
names in `inputPropertiesViaAdapter` (not compared). So an unset `Property<Boolean>` that replaced `boolean isX()`
reads `false`, as the old getter did, instead of `null`. A value that **still** differs when read through the
adapter is a real change in what the eager getter returns: report it (`EAGER-DEFAULT` when the old getter
computed a default the lazy property lacks, e.g. `JavaExec.defaultCharacterEncoding`), and confirm it in the
Gradle source of both versions (in a gradle/gradle checkout: `git show v9.9.2:<path>` vs the branch).
`classify_diffs.py` lists such cases under "differing inputs that WERE read through an adapter".

Known gap: when the script cannot follow a nested property's path to its owning bean, it silently reads the
lazy value instead of the adapter, and does not record that it did. A `null` where the old getter would
return a value is the symptom.

## When properties are read

Inputs are read in `taskGraph.beforeTask` (right before the task's actions, when Gradle fingerprints them),
outputs in `taskGraph.afterTask` (right after it finishes). Reports written before 2026-11-26 15:00 read
everything after the build; that produced `EXEC-MUTATION` (a task action mutating its own input, groovy
`Javadoc` `JFlags`) and most `QUERY-ERROR`s ("resolution … without an exclusive lock"). When rerunning such a
project, expect those to change or disappear, and say so in "Changes from the previous version".
`beforeTask` is deprecated: a project that fails on deprecation warnings needs `--warning-mode=summary` on
both sides.

## Workflow (one project per turn)

When doing several projects, do **one project, report back, and ask for confirmation before starting the
next**. Default order: smallest migration first (the index's order). After a context reset, work out what is
done from the index's "Branch build" column: a row whose short revision differs from
`$W/gradle-local/bin/gradle --version` still needs a rerun (also "Adapters" = no, and "Last run" for rows
built before the read-timing change above).

1. **Workspace.** `W=out/task-compare-g992`, `P=$W/<project>`. If `$P/repo` is missing: clone the fork to it
   and add detached worktrees `before` and `after` at the commits above. If present: check both worktrees are
   clean and at the expected commits (`git rev-parse --short HEAD`, `git status --short`).
   Move the previous run's `dump-*.json`, `comparison*.txt`, `before.log`, `after.log`, `control/` and a copy
   of the current report into `$P/run-<short revision of the branch build it used>/` (older archives:
   `pre-adapter/`) rather than overwriting them; the report copy feeds "Changes from the previous version".
2. **Distributions.**
   - Baseline: `G992=$(ls -d ~/.gradle/wrapper/dists/gradle-9.9.2-bin/*/gradle-9.9.2)`.
   - Branch: `$W/gradle-local/bin/gradle`. Record `gradle --version` (version and revision) in the report.
     If it must be rebuilt from the Provider API branch of gradle/gradle (`~/sources/gradle/trees/provider-api`,
     branch `gradle10/provider-api-migration`), use `./gradlew install -Pgradle_installPath=<abs path of
     $W/gradle-local>` there; ask first, it takes a while. When the user hands over a ready distribution
     instead (e.g. under `/tmp/gradle/`), move the old one to `$W/gradle-local-<short rev>` and copy the new one
     to `$W/gradle-local` (`/tmp` gets cleaned). Add the new short revision to the index intro's list.
     Current: `10.0.0-20261126124457+0000`, revision `018f16a2641`; earlier: `8779a723` in `gradle-local-8779a723`.
   - Run each side with the distribution's `bin/gradle` directly, never the project's wrapper.
3. **Run both builds** in the background (large projects take several minutes per side):
   ```sh
   export JAVA_HOME=<JDK>
   ARGS=(clean assemble --no-scan --no-build-cache --no-configuration-cache -I $SKILL/scripts/task-dump.init.gradle <extra args>)
   cd $P/before && rm -rf <buildSrc/build and included builds' build dirs> && $G992/bin/gradle "${ARGS[@]}" -Dtaskdump.out=$P/dump-before.json > $P/before.log 2>&1
   cd $P/after  && rm -rf <same> && $W/gradle-local/bin/gradle "${ARGS[@]}" -Dtaskdump.out=$P/dump-after.json > $P/after.log 2>&1
   ```
   - Use an **array** for the arguments. A plain `$ARGS` string is not word-split in zsh: the whole thing
     becomes one task name, `--no-scan` is lost, and a build scan of the failed run is published.
   - `clean` reaches neither `buildSrc` nor included builds: delete their `build` dirs on both sides first.
   - Apply any workaround (`-I $SKILL/scripts/skip-kotlin-metadata-check.init.gradle`, `-Prelease.version=…` for
     versions derived from git) to **both** sides.
   - Each included build / `buildSrc` writes its own dump next to the root one (`dump-before-<build>.json`).
4. **Control run** when outputs or outcomes differ in ways that might be run-to-run variance: run the baseline
   build again the same way into `$P/control/dump-before-rerun2.json`. What differs between the two baseline
   runs is not caused by the distribution (`KT-STATE` timestamps, `DISK-STATE` outcomes). If outputs embed the
   checkout path (Kotlin/Android), also build the after side at the baseline's path (see the kotest report).
5. **Compare**, per build (root, `-buildSrc`, each included build):
   ```sh
   python3 -I $SKILL/scripts/compare_dumps.py dump-before.json dump-after.json > comparison.txt
   python3 -I $SKILL/scripts/compare_dumps.py dump-before.json dump-after.json --verbose > comparison-verbose.txt
   python3 -I $SKILL/scripts/classify_diffs.py dump-before.json dump-after.json [control/dump-before-rerun2.json]
   ```
   Account for **every** differing task: tasks covered by classified rows must equal the differing tasks
   reported by `compare_dumps.py`. Hunt down the rest (often `propertyErrors` text only, `QUERY-ERROR`).
   The differing count covers tasks present in both builds only; added and removed tasks are counted
   separately (`Tasks added: N, removed: M`) and each one must be explained too.
6. **Verify before attributing.** Classes: `javap -c -p` (code) and `javap -v` (metadata) on both sides.
   Generated files: `diff`. Jars: entry names, order, sizes and CRCs with Python's `zipfile`
   (`infolist()`); a per-entry `unzip -p | shasum` loop takes minutes on large jars.
   Mark anything not verified as "not checked" in the Basis column; never guess.
7. **Write `semantic-comparisons/REPORT-<project>.md`**, following the existing reports there (the detekt and
   micronaut-core ones are adapter-aware): header table (commits with branch name, Gradle versions with branch
   revision, JVM, task counts, result), exact command line, "Read this first" (adapter sentence with counts,
   number of **differing** tasks per build, never "identical tasks", since the difference tables count differing tasks,
   plus added and removed tasks when not 0,
   build code changed by the migration, how it was run), summary, reason-mnemonic table
   (Mnemonic | Kind | Meaning | Basis), control run, task graph, one difference table per build,
   "Changes from the previous version of this report", files (located in `out/task-compare-g992/<project>/`).
   Reuse mnemonics before inventing new ones: `EAGER-DEFAULT`, `API-RECOMPILE`, `KOTLIN-COMPILER`, `KOTLIN-DSL`,
   `GRADLE-LIBS`, `IMPLICIT-IMPORTS`, `CHECKOUT-PATH`, `KT-STATE`, `COMPILE-STATE`, `DISK-STATE`, `GEN-ORDER`,
   `UPSTREAM`, `QUERY-ERROR`, `TOSTRING`, `VERSION-STRING`, `API-ADDED`, `MIGRATED`, `EXEC-MUTATION`,
   `DSL-TRANSFORM`, `BUILD-METADATA`, `GIT-REV`, `DERIVED-CP`, `BUILD-TIME`.
8. **Update `semantic-comparisons/README.md`**: the project's row (differing tasks, written `74 of 497`, or
   `74 of 497, +2 added, −1 removed` when tasks were added or removed; adapters, branch build (short
   revision of the branch distribution, defined in the index's intro), last run, headline;
   keep rows ordered by migration size) and the cross-project tables.
   The index describes the current state only: no history ("no longer differs", "previously", "predates",
   "still lists"). History belongs in each report's "Changes from the previous version" section.
9. **Report back** briefly: before/now table of the headline numbers, any remaining real difference and whether
   it changes effective behaviour, anything changed along the way (deleted dirs, re-runs, JDK), the report path.
   Then ask whether to continue with the next project. Do not commit or push unless asked.
