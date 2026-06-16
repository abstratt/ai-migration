# Task: Verify with `./gradlew assemble`

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- `./gradlew help` succeeds (previous task completed)
- JAVA_HOME is set to a working JDK

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

## Resume check

1. Run `./gradlew assemble`
2. If it succeeds on the first attempt with no changes needed, this task is already complete
3. Also check `git log` for a commit message matching "Verify with `./gradlew assemble`" (the task title)

## Instructions

1. **Run `./gradlew assemble`** and inspect errors

2. **Fix any additional issues** following the same approach:
   - Look up in `migration-data.json` first
   - Then fix manually based on error output
   - Use task 07's **Common compile-error → fix mapping** table and **lazy-first note** — `assemble`
     compiles main source (not just build logic), so the same Provider-API patterns recur there.

3. **Iterate** until `./gradlew assemble` succeeds

## Iteration strategy

Apply the same techniques as task 07's *Iteration strategy* (run with `--continue` to surface many
errors per run; `grep`-and-batch repeated patterns across the tree before re-running;
`--no-configuration-cache` while iterating with a final clean run; separate `e:` errors from `w:`
deprecation noise).

Assemble-specific issue seen in practice: **build-tooling that processes bytecode can hit ASM/toolchain
incompatibilities** under the preview distribution — e.g. IntelliJ's Java `@NotNull` instrumentation
(`com.intellij.ant.InstrumentIdeaExtensions`) failing with
`NoSuchMethodError: org.jetbrains.org.objectweb.asm.ClassReader.<init>(InputStream)`. These are
**classpath/version issues, not Provider-API issues**. Typical fixes: read bytes first
(`ClassReader(inputStream.readBytes())` instead of `ClassReader(inputStream)`), and isolate the
instrumentation classloader so the worker's ASM doesn't shadow the task's (e.g. child-first
`reverseloader="true"` on the ant `taskdef`, dropping a shared `loaderref`). Fix based on the
stacktrace; don't mistake them for migration data gaps.

## Commit checkpoint (mandatory before moving on)

Before starting task 09, resolve this task's changes:

- If the task made changes, commit them with subject `` Verify with `./gradlew assemble` `` (the task title — the backticks around `./gradlew assemble` make it clear these fixes were driven by `assemble` failures). Include the `Assistant:` trailer (see CONTEXT.md).
- If `./gradlew assemble` passed on the first try with no edits, skip the commit — but only if `git status` is already clean.
- Either way, run `git status` before starting task 09 and confirm the working tree is clean.

See the "Commit Discipline" section in CONTEXT.md.

## Done when

- `./gradlew assemble` exits 0
- Either a commit with subject `` Verify with `./gradlew assemble` `` exists on the migration branch, or no changes were needed; in both cases `git status` is clean
