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
   - Apply @migration-reference/MIGRATION_RULES.md — the per-kind rules, the **Code Change Guidelines**
     (refactor-only, comments for non-trivial changes, no cosmetic changes, ignore deprecations), and,
     crucially, the **Change-minimization principle** with its **operator/assignment-overload rule
     (absolute)**: when an `org.gradle.kotlin.dsl` import would keep an operator/assignment form
     (`=`, `+=`, `mapProp[k]`) compiling, add the import and keep that form — never rewrite it to
     `.set`/`.add`/`.put`/`.setFrom`/`.get()[k]`. This applies to `assemble`-phase fixes exactly as it
     does in task 07.
   - Then fix manually based on error output
   - Use task 07's **Common compile-error → fix mapping** table, **lazy-first note**, and
     **Self-reference note** — `assemble` configures and compiles main source (not just build logic),
     so the same Provider-API patterns recur there, including the self-referential update that throws
     `StackOverflowError` at configuration time (fixed with the internal `replace(transform)` method).

3. **Iterate** until `./gradlew assemble` succeeds — or until the only remaining failures are
   **environmental / out-of-scope** (see below).

## Environmental / out-of-scope build failures

> **Intent:** distinguish a failure the migration is responsible for from one the host or the project's
> own scope imposes, so the iteration loop has a principled stopping point and task 09 can assign a
> deterministic status. Without this, an unfixable host-toolchain failure (e.g. missing Xcode) makes
> "iterate until `assemble` exits 0" loop forever and forces an arbitrary FAILED verdict.

A remaining `assemble` failure is **environmental / out-of-scope** when **all** of these hold:

- it is **not attributable to the Provider API migration** — the failing task does not compile or
  configure any code this run changed, and the stacktrace is not a Provider-API symptom (lazy-property
  type mismatch, missing accessor, `StackOverflowError` from self-reference, etc.); **and**
- it would **fail identically on the unmigrated base tree under the baseline distribution** — i.e. it
  stems from the host (a missing/incomplete toolchain such as no full Xcode for Kotlin/Native Apple
  targets, an absent SDK or native compiler, no network) or from a target the project itself documents
  as conditional (e.g. an `AGENTS.md`/README note that "Apple targets require Xcode"); **and**
- it is **not** one of the predicted preview-distribution issues you are expected to fix (dependency
  verification, warnings-as-errors promotion, ASM/bytecode-instrumentation toolchain mismatches — those
  are in scope; fix them, don't classify them as environmental).

Do **not** stretch this carve-out to excuse a genuine migration defect. If you are unsure whether a
failure would also occur on the unmigrated baseline, the cheapest confirmation is to check out the base
ref and run the same `assemble` task under the baseline distribution; if it fails the same way, the
failure is environmental. When you do stop on environmental failures, **record each one** (failing
tasks, the exact error, and why it is out-of-scope) so task 09 can report it — stopping silently is not
allowed.

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

- `./gradlew assemble` exits 0 — **or** every remaining failure is **environmental / out-of-scope** per
  the section above (all migration-attributable errors are fixed, and the residual failures are recorded
  for task 09)
- Either a commit with subject `` Verify with `./gradlew assemble` `` exists on the migration branch, or no changes were needed; in both cases `git status` is clean
