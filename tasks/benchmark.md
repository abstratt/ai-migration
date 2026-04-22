# Task: Benchmark Two Migration Runs

@tasks/CONTEXT.md

This task is **off-pipeline** — it compares two already-completed migration branches on the same repository and writes a benchmark report. It does not commit anything to the migrated repo.

## Arguments

Expected argument format:

    <repo-url> <branch-1>=<description-1> <branch-2>=<description-2>

- `<repo-url>` — git URL of the remote where **both branches exist** (typically the fork used by the migration workflow, e.g. `https://github.com/abstratt/spring-boot`). This is the base for every link in the report.
- `<branch-N>` — full branch name as it exists on that remote (e.g. `gradle-10-migration/20260420-1932`).
- `<description-N>` — short human-readable label identifying the run (typically the model, e.g. `qwen3.5-35b`, `opus-4-7`). Used in section headers and in the output filename.

If the arguments are missing or malformed, stop and ask the user.

## Preconditions

- Both branches exist on the remote and are reachable from the local clone at `migrated/<repo-name>/`. If the clone is missing, clone first; if the branches are not local, `git fetch origin <branch-1> <branch-2>`.
- Each branch follows the Gradle 10 migration pipeline (at minimum a `Migrate Build Scripts and Gradle API Usages` commit on top of a shared base).

## Output file

Write to the **project root** (sibling of `MIGRATION.md`, not inside `migrated/`):

    BENCHMARK-<repo-name>-<YYYYMMDD>-<slug-1>-vs-<slug-2>.md

- `<repo-name>` — last path segment of `<repo-url>`, stripped of any trailing `.git`.
- `<YYYYMMDD>` — today's date (run `date +%Y%m%d`).
- `<slug-N>` — `<description-N>` slugified: lowercase, spaces/underscores → `-`, drop non-alphanumeric except `-` and `.`, collapse repeated `-`. Example: `Opus 4.7 (1M)` → `opus-4-7-1m`.

If the output file already exists, overwrite it.

## Procedure

1. **Parse the arguments.** Compute `<repo-name>`, slugs, and the final output filename.

2. **Fetch and locate branches.** From `migrated/<repo-name>/`, run `git fetch` for the remote that matches `<repo-url>`, then confirm both branches resolve (`git rev-parse origin/<branch>`).

3. **Identify the common base.** `git merge-base origin/<branch-1> origin/<branch-2>`. This is the pre-migration commit both runs diverged from. Save its SHA.

4. **Catalog commits per branch.** For each branch, `git log --oneline <base>..<branch>` and map each commit to its pipeline task by subject. Expected subjects:

   | Task | Subject |
   |---|---|
   | 04 Swap Distribution | `Swap Gradle Distribution` |
   | 06 Migrate | `Migrate Build Scripts and Gradle API Usages` |
   | 07 Verify help (optional) | `Verify with ./gradlew help` |
   | 08 Verify assemble | `Verify with ./gradlew assemble` |
   | 09 Report | `Generate Report` |

   Note any missing task commits — e.g. task 07 was added to the pipeline in April 2026, so older runs may not have it.

5. **Read per-run reports.** If each branch has a `REPORT-<YYYYMMDD-HHMM>.md` at its root (produced by task 09), read it for the `Assistant` trailer, elapsed time, and each run's self-described scope and limitations. Note whether the trailer is genuine or left as the `<<Tool Name>> / <<Friendly Model Name>> / <<model-id>>` template placeholder.

6. **Collect headline metrics.**
   - Wall-clock elapsed (from per-run report or computed from first → last commit timestamps).
   - Files in migration commit (`git show --stat --format= <migrate-sha>`).
   - Files in each verify commit (same command).
   - Full branch-diff file count (`git diff --stat <base>..<branch>` — bottom line).
   - Trailer correctly filled? (yes/no, per branch.)

7. **Compare migration commits file-by-file.** For each file touched by either migration commit:
   - **Overlap**: classify the change as **equivalent** (same effect, perhaps cosmetic differences) or **non-equivalent** (different approach, different lines touched, or different semantics).
   - **Unique**: list files only one branch touched.

   For large diffs, delegate the file-by-file walk to a general-purpose subagent with the two commit SHAs and the criteria below — then incorporate its findings.

8. **Evaluate against the primary criteria** from `tasks/CONTEXT.md` §"Code Change Guidelines":

   **(1) Behavior preservation.** The rule is the one stated in `tasks/CONTEXT.md` §"Code Change Guidelines": the migrated code must not change observable functionality, and must not make cosmetic changes outside what the migration requires. `migration-reference/MIGRATION_RULES.md` defines what each `kind` should rewrite to. Read both, then flag any regression a diff introduces against them — syntax errors, semantic changes (e.g. replace → append), misapplied rules to types the rules don't cover, dropped defaults/conventions, changed resolution timing, dead code left behind, or drive-by edits unrelated to the migration.

   **(2) Lazy vs eager.** Flag each occurrence of:
   - `.get()` inside a configuration block or task wiring where `Provider.map` / `.flatMap` / `.zip` would keep the chain lazy.
   - `Property.set(otherProvider.get())` instead of `Property.set(otherProvider)`.
   - `ConfigurableFileCollection.setFrom(other.get())` / `.setFrom(other.getFiles())` instead of passing the live collection (`.getFiles()` is correct only to break an explicit self-reference — if so, require a comment explaining it).
   - Self-referential `.set(.get())` on the same property.

   **(3) Coverage.** Does each branch migrate `buildSrc/`? (The default scanner excludes directories named `build`, which silently hides `org.springframework.boot.build`-style package trees inside `buildSrc`. A good run will have noticed and worked around this.) List files each branch missed entirely vs. files the other covered.

   **(4) Self-reporting.** Is the `Assistant:` commit trailer correctly filled on all commits? Is the per-run `REPORT-*.md` accurate about kinds applied, leave-alone list, and known limitations? A trailer left as `<<Tool Name>> / <<Friendly Model Name>> / <<model-id>>` is a red flag — the model failed to substitute its own identity.

9. **Compute the verification-cost ratio.** Sum files touched by verify commits per branch. A clean migration lands 0-3 files of verify-time fixes; large numbers indicate bugs the verify step had to revert or migrations that had to be performed after the fact. Distinguish in the report between "genuine edge-case fixes" and "reverts of migration bugs" — read the verify-commit diffs to tell them apart.

10. **Produce the report.** Follow the structure below. Include concrete `diff`-fenced snippets for each representative finding and link every cited commit, file, and branch back to `<repo-url>`.

    Link formats (use the supplied `<repo-url>` verbatim as the base, not `upstream`):
    - Commit: `<repo-url>/commit/<full-40-char-sha>`
    - File at commit: `<repo-url>/blob/<full-sha>/<relative-path>`
    - Branch tree: `<repo-url>/tree/<branch-name>`
    - Branch compare vs base: `<repo-url>/compare/<base-short-sha>...<branch-name>`

    When showing a diff in the report, prefer a fenced ```diff block with `-` / `+` lines lifted verbatim from `git show`.

## Report structure

Match the tone and depth of `BENCHMARK-spring-boot-20260420.md` at the project root (the canonical example produced by hand before this task existed). Required sections, in order:

1. **Title** — `# Benchmark Report — Gradle 10 Lazy-Property Migration`
2. **Metadata** — repository (linked), task description, base commit (linked SHA), date.
3. **Models under test** — table with columns: label (A / B), model id, tool, branch (linked). Also include branch-compare-vs-base links.
4. **Executive summary** — one-paragraph verdict naming the winner, followed by a **Headline metrics** table. Table rows at minimum: wall-clock elapsed; files in migration commit; files in verify commits; `./gradlew help` passed at migration commit; `./gradlew assemble` passed at migration commit; Groovy syntax errors introduced; semantic regressions (`from` ≠ `setFrom`); compile errors (`.get()` on non-Gradle types); `buildSrc/` migrated; trailer correctly filled.
5. **Methodology** — per-task commit table with linked SHAs for each branch. Note any task commits absent from one branch and why.
6. **Results by criterion** — four subsections, one per criterion (Behavior preservation / Lazy vs. eager / Coverage / Self-reporting). Each subsection must include at least one concrete `diff` snippet with a file-at-commit link whenever divergences are found.
7. **Verification cost — the rescue effect** — table of verify commits with file counts and one-line characterizations distinguishing legitimate fixes from migration-bug reverts.
8. **Verdict** — numbered list (1-4) mapping each criterion to a winner with specific file/commit citations; close with a recommendation for which branch to accept and what (if anything) needs salvaging from the losing branch.

## Commit policy

- Do **not** commit anything inside `migrated/<repo-name>/` — this is a read-only comparison.
- Do **not** auto-commit the generated `BENCHMARK-*.md` to the tooling repo. Leave it in the working tree for the user to review.

## Done when

- `BENCHMARK-<repo-name>-<YYYYMMDD>-<slug-1>-vs-<slug-2>.md` exists at the project root.
- It contains every section listed under "Report structure" with concrete diff snippets and working links to `<repo-url>`.
- No changes have been committed to either the migrated repo or the tooling repo.
