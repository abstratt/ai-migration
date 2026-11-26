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
| `semantic-comparisons/README.md` | The index: one row per project (migration size, differing tasks, adapters yes/no, last run, headline), the reason-mnemonic definitions, cross-project difference tables, caveats. **Published output.** |
| `semantic-comparisons/REPORT-<project>.md` | One report per project. **Published output.** Also the record of each project's settings (commits, JDK, extra args, included builds) for reruns. |
| `out/task-compare-g992/` | Workspace (git-ignored): `gradle-local/` (branch distribution), `<project>/repo` (clone of the fork), `<project>/before`, `<project>/after` (worktrees), dumps, logs, comparison output, `control/`, archived runs. |
| this skill's `scripts/` | `task-dump.init.gradle` (adapter-aware; the only copy to use), `compare_dumps.py`, `classify_diffs.py`, `skip-kotlin-metadata-check.init.gradle` |
| this skill's `references/tool-README.md` | Dump format, flags, limitations |

## Discovering projects

There is no fixed list. A project is eligible when the migration produced a branch for it:

- `NEXT_REPOSITORIES.md` ("Completed runs") lists the migrated projects;
- the migrated fork is `https://github.com/abstratt/<project>`, with branches `gradle-10-migration/<timestamp>-<pair-id>`
  (`git ls-remote --heads https://github.com/abstratt/<project> 'gradle-10-migration/*'`). Use the branch for the
  pair named in the project's existing report; for a new project, or if unclear, ask which pair. If several
  branches match, the newest timestamp, unless the existing report names another;
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
outputs in `taskGraph.afterTask` (right after it finishes). `beforeTask` is deprecated: a project that fails on deprecation warnings needs `--warning-mode=summary` on
both sides.

## Nested beans

A `@Nested` bean (`Javadoc.options`, `JavaCompile.options`, …) is recorded as `{"implementation": "<class>"}`,
the implementation type Gradle fingerprints, its properties separately as `<name>.<property>`.

## Init script changes

Never compare two dumps written by different versions of `task-dump.init.gradle`; both sides of a comparison
come from the same run. When a rerun's results differ from the previous report because the script changed
(`git log -- scripts/task-dump.init.gradle`), say so when reporting back (step 9), not in the report.

## Workflow (one project per turn)

**Which project.** Compare only the project(s) the user named. If the request names none (e.g. "run the
comparison", "re-compare", "continue"), ask which repository to compare before doing anything else
(`AskUserQuestion`). Do not pick one yourself: not the next row in the index, not the smallest migration, not
one that looks stale, not the one from an earlier turn or before a context reset. You may list the eligible
projects and which ones need a rerun (see below) as options in the question, but the user chooses.

When the user asked for several projects (or "all"), do **one project, report back, and ask for confirmation
before starting the next**. Order: smallest migration first (the index's order), unless the user said
otherwise. To tell which projects need a rerun (for the options above, or when the user asked for "all
that need a rerun"), use the index's "Branch build" column: a row whose short revision differs from
`$W/gradle-local/bin/gradle --version` still needs a rerun. So does a row with "Adapters" = no, and one whose
"Last run" is before the last commit that changed what the dump records
(`git log -- .claude/skills/provider-api-build-comparison/scripts/task-dump.init.gradle`; ignore commits that
only touch comments). A report not in the
format of step 7 is rewritten in it when rerun.

1. **Workspace.** `W=out/task-compare-g992`, `P=$W/<project>`. If `$P/repo` is missing: clone the fork to it
   and add detached worktrees `before` and `after` at the commits above. If present: check both worktrees are
   clean and at the expected commits (`git rev-parse --short HEAD`, `git status --short`).
   Move the previous run's `dump-*.json`, `comparison*.txt`, `before.log`, `after.log`, `control/` and a copy
   of the current report into `$P/run-<short revision of the branch build it used>/` rather than overwriting them; the report copy feeds the before/now table when reporting
   back (step 9). The new report does not refer to it.
2. **Distributions.**
   - Baseline: `G992=$(ls -d ~/.gradle/wrapper/dists/gradle-9.9.2-bin/*/gradle-9.9.2)`.
   - Branch: `$W/gradle-local/bin/gradle`. Record `gradle --version` (version and revision) in the report.
     If it must be rebuilt from the Provider API branch of gradle/gradle (`~/sources/gradle/trees/provider-api`,
     branch `gradle10/provider-api-migration`), use `./gradlew install -Pgradle_installPath=<abs path of
     $W/gradle-local>` there; ask first, it takes a while. When the user hands over a ready distribution
     instead (e.g. under `/tmp/gradle/`), move the old one to `$W/gradle-local-<short rev>` and copy the new one
     to `$W/gradle-local` (`/tmp` gets cleaned). Add the new short revision to the index intro's list.
     The current distribution is whatever `$W/gradle-local/bin/gradle --version` reports.
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
   checkout path (Kotlin/Android), also build the after side at the baseline's path, to tell
   path-dependent output from distribution-dependent output.
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
7. **Write `semantic-comparisons/REPORT-<project>.md`** with these sections in order:
   - header table: commits with branch name, Gradle versions with branch revision, JVM, task counts, result;
   - one sentence under it with the headline: the finding that matters most, or "no input value differs and no
     build product differs because of the distribution";
   - a paragraph with the exact command line and whatever is specific to how this project was run: workarounds,
     `build` dirs of `buildSrc`/included builds deleted first, any local state of the worktrees that could
     matter;
   - Summary table. Rows: task graph; outcomes; **differing** tasks per build (never "identical tasks", since
     the difference tables count differing tasks), plus added and removed tasks when not 0; build code changed by
     the migration (none, or a pointer to "Migrated build logic"); task inputs, including the adapter counts
     ("no value differs; N values in M tasks read through adapters"); compiled classes; jars; other outputs
     that differ;
   - "Migrated build logic", when the migration changed build code;
   - "Basis" table (Mnemonic | Basis): one row per mnemonic used in this report, with the evidence from this
     project's run (what was verified and how, or "not checked"). The mnemonic's kind and generic meaning are
     defined in the index, not here; one sentence above the table links there
     (`[index](README.md#reason-mnemonics)`). The mnemonic cells are plain code (`` `GEN-ORDER` ``), not links,
     because links around inline code in table cells render badly. Project-specific detail (which class, which file, how many)
     goes in the Basis or in the difference rows;
   - task graph;
   - one difference table per build.
   No "Read this first" section: the method (eager-API semantics, the adapters) and the caveats that apply to
   every project (version difference, scope limited to `assemble`, …) are stated once, in the index, not repeated
   per report.
   No "Control run" section by default. Once the control run (step 4) has settled what is run-to-run variance,
   its result goes into the Basis of the mnemonics it supports, in a phrase ("differs between two baseline
   runs too", "identical between two baseline runs"). Add a section only when a conclusion needs more than
   that to be convincing, e.g. an experiment that builds the after side at the baseline's path.
   When rewriting an existing report, do not carry over any section not listed above. Two rules for the report's content:
   - **No history.** The report describes the current run only: no "previously", "no longer", "now",
     "still", "instead of N", "this time", "the previous version", "an earlier run", no counts compared with an
     earlier run, no archived runs (`run-<rev>/`). Every Basis entry must rest on evidence
     from the current run: a fact that an earlier run verified is re-verified against the current dumps or
     build outputs, or marked "not checked". Do not copy it across as verified. What changed since the last
     report goes in the step 9 message only.
   - **No files outside the repository.** Do not mention the comparison's own files (dumps, logs,
     `compare_dumps.py` output, `control/` dumps, extracted classes, archives) or any `out/…` path. Name
     the evidence by what it is ("the dumps", "the control run", "a second baseline run"). The project's
     build outputs that the comparison is about (`previous-compilation-data.bin`, a jar, a generated source)
     may still be named by their path in the project. So may the skill's scripts (`task-dump.init.gradle`,
     `skip-kotlin-metadata-check.init.gradle`), which are in the repository.
   Reuse the mnemonics defined in the index's "Reason mnemonics" table before inventing new ones. A new one is
   added to that table (step 8) with a generic meaning that is not tied to the project. When an existing report
   uses a different name for a mnemonic the index defines, use the index's name.
8. **Update `semantic-comparisons/README.md`**: the project's row (differing tasks, written `74 of 497`, or
   `74 of 497, +2 added, −1 removed` when tasks were added or removed; adapters, branch build (short
   revision of the branch distribution, defined in the index's intro), last run, headline;
   keep rows ordered by migration size), the cross-project tables, and the "Reason mnemonics" table
   (Mnemonic | Kind | Meaning, one row per mnemonic used in any report, generic wording, no project names
   or evidence; anchor `#reason-mnemonics`). Drop a mnemonic from the table when no report uses it any more.
   The index follows the same two rules as the reports (step 7): current state only, no history ("no longer
   differs", "previously", "predates", "still lists"), and no files outside the repository.
9. **Report back** briefly: before/now table of the headline numbers, what changed since the last report and
   why (this message is the only place for that history), any remaining real difference and whether it changes
   effective behaviour, anything changed along the way (deleted dirs, re-runs, JDK), the report path.
   Then, if the user asked for several projects, ask whether to continue with the next one of those;
   otherwise stop. Do not commit or push unless asked.
