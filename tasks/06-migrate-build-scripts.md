# Task: Migrate Build Scripts and Gradle API Usages

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- `gradle-wrapper.properties` points to the custom Provider API distribution
- JAVA_HOME is set to a working JDK

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Hard rule: no Gradle execution in this task

This task is a **static, data-driven transformation**. Do **not** run `./gradlew`, `gradle`, `gradle help`, `gradle assemble`, `gradle build`, `gradle tasks`, or any other Gradle invocation at any point during this task — not for validation, not for sanity checks, not to "see what breaks", not to iterate on fixes. Build validation is the job of tasks 07 and 08; running Gradle here will produce failures that you must not react to.

If you feel the urge to run Gradle to check your work, stop and commit what you have instead. Any iteration loop driven by Gradle output belongs in task 07 or later, never here.

## Resume check

1. Check `git log` for a commit message matching "Migrate Build Scripts and Gradle API Usages" (the task title)
2. If such a commit exists on the current branch, this task is already complete

## Instructions

1. **Load the migration reference files** from `migration-reference/`:
   - `migration-reference/migration-data.json` — lookup table of every changed property (class, old type, new type, kind, removed accessors)
   - `migration-reference/MIGRATION_RULES.md` — transformation rules for each property kind

   **Leave-alone list.** The following constructs are outside the scope of this migration and must be kept as-is even if they superficially resemble a scan hit:

   > **Intent:** bound the set of code affected by this task to exactly the accessors driven by `migration-data.json`, so unrelated APIs are not modified.

   - `org.gradle.api.Task` accessors: `setDescription`, `setGroup`, `setEnabled`, `setDependsOn`, `setOnlyIf`, `setActions`, `setFinalizedBy`, `setMustRunAfter`, `setShouldRunAfter`, `setTimeout`, `setDidWork` (not lazy-migrated in Gradle 10).
   - Task lifecycle/wiring APIs: `doFirst`, `doLast`, `dependsOn(…)`, `finalizedBy(…)`, `mustRunAfter(…)`, `shouldRunAfter(…)`.
   - `Project` methods called on `project` itself (e.g. `project.file(...)`, `project.files(...)`, `project.layout.*`).
   - Third-party plugin types — any receiver in a non-`org.gradle` package. These are handled in task 07/08 if they produce build errors.
   - `@Input` / `@InputFile` / `@OutputDirectory` annotated fields on custom task classes declared in `buildSrc` — these require a different migration path (declaring the field as `Property<T>` rather than rewriting call sites) and are out of scope for this task.
   - Deprecation warnings reported by the scanner or the compiler — ignore them; this task covers removals only.
   - Comments, KDoc, Javadoc, and string literals that mention removed accessor names — leave them as-is.

2. **Run the automated usage scanner** to get a comprehensive, pre-filtered list of every candidate change site:

   ```bash
   python3 ../migration-reference/scan_usages.py . 2>&1 | tee /tmp/scan-results.txt
   ```

   The scanner produces three sections:
   - **Cat-A** — removed accessors (`set*` / `is*` methods listed in `removed_accessors`)
   - **Cat-B** — changed-return-type getters (`get<Prop>()` used without `.get()` / `.set(` / etc.)
   - **Cat-C** — Groovy DSL operator mutations (`-=`, `+=`, `<<` on lazy `list`/`set`/`map` properties)

   The scanner already:
   - Restricts Java/Kotlin/Groovy files to those that import `org.gradle` (avoids application code and Maven plugin false positives)
   - Skips comment lines and method declarations
   - Skips Category B for test source directories (too many generic-name false positives)
   - Skips common Task-only accessors like `setDescription`, `setGroup` (not lazy-migrated in Gradle 10)
   - Annotates each hit with `[CONFIRMED: ClassName]` when a relevant Gradle type is found in the file's imports, or `[unconfirmed - check type]` when no import match was found

   **Review each hit** and decide if it is a real migration site:
   - **`[CONFIRMED]` hits**: the file imports a Gradle API type that owns the property. Almost always real — fix them. The only exception is if the method name is called on a *different* local variable of a non-Gradle type (check the receiver at the call site).
   - **`[unconfirmed]` hits in production source** (`buildSrc/src/main/java/`, `build-plugin/...src/main/java/`): the type may be accessed through a method chain rather than imported directly (e.g. `compile.getOptions().setEncoding(...)` where `CompileOptions` is returned by `getOptions()` but not imported; `publication.pom((pom) -> pom.setPackaging(...))` where `MavenPom` is a lambda parameter). **Treat these as real** and apply the fix — unless you can positively identify the receiver as a non-Gradle type (check the variable declaration or method chain).
   - **`[unconfirmed]` hits in test source or DSL files**: more likely to be false positives. Still check the receiver type before skipping.

   **Receiver-type decision procedure.** For each hit where the owning type is not obvious, walk this ladder in order and stop at the first matching step:

   > **Intent:** convert the ambiguous "is this call on a Gradle type?" judgment into a mechanical check that produces the same answer every time.

   1. Is the method name in the Task-only list (`setDescription`, `setGroup`, `setEnabled`, `setDependsOn`, `setOnlyIf`, `setActions`, `setFinalizedBy`, `setMustRunAfter`, `setShouldRunAfter`, `setTimeout`, `setDidWork`)? → **skip** (not migrated in Gradle 10).
   2. Does the file `import` a class that appears in `migration-data.json` and owns this property? → **apply** the transformation.
   3. Is the receiver a local variable? Find its declaration.
      - Declared type is in `migration-data.json`? → **apply**.
      - Declared type is in a non-`org.gradle` package? → **skip**.
   4. Is the receiver a method chain (`a.b().c()`)? Find `b()`'s declared return type. If that return type is in `migration-data.json` (directly or via `also_known_as`), → **apply**.
   5. Is the receiver a lambda parameter (e.g. `publication.pom(pom -> pom.setX(...))`)? Check the enclosing method's signature — the parameter's type is usually a Gradle configuration type. → **apply** if found in the JSON.
   6. None of the above → **leave unchanged and note in a comment for review**.

3. **Apply mechanical rewrites first with `apply_migrations.py`**:

   ```bash
   python3 ../migration-reference/apply_migrations.py . 2>&1 | tee /tmp/apply-results.txt
   ```

   The tool is data-driven from `migration-data.json` and only rewrites the safe, unambiguous cases:
   - **Category A only** — removed accessors (`setX(...)` call sites)
   - **`[CONFIRMED]` hits with exactly one matching class** (no ambiguous receivers)
   - **Kinds it handles**: `boolean`, `scalar`, `list`, `set`, `map`, `dir`, `file`, `file_collection`, `other`
   - **Rewrite shape**: `obj.setX(arg)` → `obj.getX().set(arg)` (or `.setFrom(arg)` for `file_collection`) — safe in Java, Groovy DSL, and Kotlin DSL
   - **Single-line only**: multi-line setter calls are deferred
   - **Circular-ref guard**: `file_collection` setters whose argument references the same property (e.g. `task.setClasspath(files(extra, task.getClasspath().getFiles()))`) are deferred — the `getFiles()` snapshot trick has to be applied by hand

   Everything it does not rewrite — Category B, Category C, `[unconfirmed]` hits, ambiguous multi-match hits, `isX()` boolean reads, `read_only` kinds, multi-line calls, circular-ref file collections — is appended to `MIGRATION_NOTES.md` at the root of the cloned repo with the file, line, class, property, source text, and a reason string.

   > **Intent:** remove the mechanical bulk of rewrites from the model's per-site `Edit` loop (faster and more reproducible than hand-edits), while keeping every judgment call — receiver-type disambiguation, Cat-B/C decisions, multi-line restructures, circular-ref handling — in the model's hands via `MIGRATION_NOTES.md`.

   **The tool's `MIGRATION_NOTES.md` output is NOT a deliverable — it is the input to step 4.** Expect it to contain hundreds of entries with boilerplate reason strings like `category B is out of scope for this tool`, `unconfirmed receiver — no matching import`, and `kind '…' has no mechanical rewrite`. Those reasons mean *"the tool declined to guess"*, not *"this is a confirmed false positive"*. Committing this file unchanged — with its raw boilerplate reason strings intact — is a **task failure**; step 5 includes a hard audit that will force a rollback if it detects unprocessed tool output.

4. **Process every entry in `MIGRATION_NOTES.md`, line by line.** This is the core of the task. Open the file. For each entry, decide one of three outcomes, and act on the decision before moving to the next entry:

   **(a) Real rewrite.** Apply the rule from `migration-data.json` + `MIGRATION_RULES.md` via an `Edit` call, then **delete the entry from `MIGRATION_NOTES.md`**. Guidelines for the rewrite itself:
   - Prefer lazy wiring (`taskB.foo.set(taskA.foo)`) over eagerly resolving values
   - Use `.get()` only when the resolved value is needed (e.g., passing to an API that does not accept `Provider`)
   - Add a code comment explaining the reason for each non-trivial change
   - Ignore deprecations for now

   **(b) Confirmed false positive.** Walk the receiver-type ladder below. If the receiver is not a migrated Gradle type, **rewrite the entry's `reason` string** to a **site-specific** explanation of *why this particular receiver* is not a Gradle property. The reason must name the actual type or construct at the call site, not the category of problem. Examples of acceptable vs. unacceptable reasons:

   | Acceptable (site-specific) | Unacceptable (category label or tool-speak) |
   |---|---|
   | `receiver is user-defined ResolveMainClassName with own setClasspath(Object)` | `Cat-A setter — receiver is not a migrated Gradle type` |
   | `io.spring.javaformat.Format.setEncoding, not a Gradle accessor` | `unconfirmed receiver — no matching import` |
   | `java.util.zip.ZipEntry.setComment — JDK API, not Gradle` | `receiver type not statically confirmable via imports` |
   | `Project.setVersion — Task-only accessor not lazy-migrated in Gradle 10` | `category A is out of scope for this tool` |

   A good reason mentions the fully-qualified type name or the specific non-Gradle construct at that call site. If the same reason applies to many entries (e.g. several `Sync.setDestinationDir` calls), group them under a `### Heading` and let the heading carry the shared context — the per-entry reason can then be shorter but must still name the specific site (e.g. `Sync in buildSrc MavenPluginPlugin`).

   **(c) Cannot decide yet.** If the fix requires compile-error context (e.g. multi-line restructure whose correctness depends on which overload the compiler picks), leave the entry but **still rewrite its `reason` string** to name the specific uncertainty at *this site* (e.g. `overload selection unclear: MavenPom.setPackaging(String) vs. AbstractBootArchiveTests.setPackaging(Object) — resolve against task 07 compile output`). Do not leave any boilerplate string in place, including:

   - Any canonical `apply_migrations.py` reason (`category B is out of scope for this tool`, `unconfirmed receiver — no matching import`, `kind '…' has no mechanical rewrite`, `setter call not found or spans multiple lines`, `read_only property has no setter to rewrite`, `{method}() boolean read: context-dependent rewrite`, `ambiguous receiver (matched N classes)`, `file_collection argument references same property (possible circular ref)`, `confirmed class has no matching data entry`, `rewrite produced no change`).
   - **Templated substitutes** that preserve the boilerplate shape with different words — e.g. `defer to task 07: Cat-B getter rewrite depends on downstream usage`, `let compile errors disambiguate`, `verify against compile output`, `multiple candidate Gradle types — pick the right one from compile errors`, or any other category-level-but-generic text reused verbatim across many entries. These are the shape the boilerplate-detector in step 5(b) fails on, and they are indistinguishable from raw tool output for audit purposes.

   **Entries you must always process, never skip wholesale:**
   - **Category C hits on `.gradle` / `.gradle.kts` files** are almost always real — the scanner marks them "unconfirmed" only because DSL files have no typed imports for it to match against. `jvmArgs += [...]`, `compilerArgs << "..."`, `prop -= [...]` on `ListProperty`/`SetProperty`/`MapProperty` all need rewriting. Do **not** defer these as "unconfirmed."
   - **Category B `[CONFIRMED]` hits** require manual review — they were deferred only because auto-rewriting return-type-changed getters without knowing the consumer context is unsafe, not because they're false positives.
   - **Category A hits with `kind '<X>' has no mechanical rewrite`** reasons mean the kind is `read_only` or an unhandled kind — inspect each one.

   Use the **Receiver-type decision procedure** from step 2 (the numbered ladder above) to classify each entry. Also recall:

   **Inheritance lookup via `also_known_as`.** A property may be defined on a base class and inherited by many public-API subtypes (e.g. `maxHeapSize` is on `JavaForkOptions` and inherited by `Test`, `JavaExec`, and others). If a direct class + property lookup returns no entry, search `migration-data.json` for the property name alone and check each match's `also_known_as` field. Example: `Test.setMaxHeapSize("2g")` resolves via `JavaForkOptions.maxHeapSize` (with `Test` under `also_known_as`).

   **Per-category rewrite rules for the hand-applied subset:**

   - **`is*` boolean getter sites**: replace `task.isFoo()` with `task.getFoo().get()` (inside task actions or when a resolved value is needed), or wire lazily with `task.getFoo()` (returns `Property<Boolean>`) elsewhere.
   - **Changed-return-type getter sites (Cat-B)**: when `getX()` is used as the old plain type, add `.get()` to resolve it: `task.getArgs()` → `task.getArgs().get()`. When it is passed to an API that accepts `Provider<T>`, no `.get()` is needed.
   - **Groovy DSL operator mutations (Cat-C)**: replace `prop -= [value]` / `prop += [value]` with `prop.set(prop.get() - [value])` / `prop.add(value)` respectively. `prop << value` → `prop.add(value)`.
   - **`file_collection` kind**: replace `task.setX(fc)` with `task.getX().setFrom(fc)`. `.from(...)` appends and is not a migration for `setX(...)` — never use it to rewrite an old setter. Watch for circular references: if the new value references the same property, snapshot first with `.getFiles()`: `task.getX().setFrom(project.files(extra, task.getX().getFiles()).filter(...))`.

   **The shape of a completed `MIGRATION_NOTES.md`.** After step 4, the file should either be empty (delete it) or read like a curated false-positive analysis: entries grouped by receiver-type category, each with a one-line human reason. A file that still looks like `apply_migrations.py`'s raw output — hundreds of entries with identical boilerplate reason strings — means step 4 was not done. Commit the file only if it passes step 5's audit.

5. **Self-check before commit — two audits.**

   **(a) Scanner audit.** Re-run the scanner on the transformed tree:

   ```bash
   python3 ../migration-reference/scan_usages.py . 2>&1 | tee /tmp/scan-results-after.txt
   ```

   > **Intent:** provide a deterministic pass/fail signal that the migration covered every site the scanner can detect, without relying on Gradle execution (which is forbidden in this task).

   Expectations:
   - **Zero `[CONFIRMED]` Cat-A hits** (removed accessors) should remain — every confirmed hit means a real call site was missed.
   - **Zero `[CONFIRMED]` Cat-B hits** (changed-return-type getters without `.get()`/`.set(`) should remain.
   - **Zero Cat-C hits on `.gradle` / `.gradle.kts` files, confirmed or unconfirmed.** DSL files have no typed imports, so the scanner cannot confirm their receivers; nearly every Cat-C hit in a DSL file is a real `jvmArgs += ...` / `compilerArgs << ...` / `prop -= ...` that needs rewriting. Do not exempt these because they say "unconfirmed."
   - `[unconfirmed]` hits in `.java` / `.kt` / `.groovy` files may remain if step 4 recorded them as false positives; each must be reflected in `MIGRATION_NOTES.md` with a specific human reason.

   If any of the above fail, return to step 4 and address them before committing.

   **(b) `MIGRATION_NOTES.md` audit — two checks.** If the file exists after step 4, run both:

   **(b.1) Canonical-boilerplate check.** Catches any canonical `apply_migrations.py` reason string left intact:

   ```bash
   grep -cE "category [ABC] is out of scope for this tool|unconfirmed receiver — no matching import|kind '[a-z_]+' has no mechanical rewrite|boolean read: context-dependent rewrite|possible circular ref|ambiguous receiver \(matched|setter call not found or spans multiple lines|read_only property has no setter|confirmed class has no matching data entry|rewrite produced no change" MIGRATION_NOTES.md || true
   ```

   The count must be **zero**. Non-zero = raw tool output committed; return to step 4.

   **(b.2) Distinct-reason check.** Catches *templated substitutes* — reason strings that were mass-rewritten into new boilerplate (different words, same shape, still reused across many entries). This is the failure mode that passes (b.1) but still represents zero per-site analysis:

   ```bash
   python3 - <<'PY'
   import re, sys, collections
   try:
       text = open("MIGRATION_NOTES.md").read()
   except FileNotFoundError:
       sys.exit(0)
   entries = re.findall(r"^- line \d+.*?— (.+)$", text, re.M)
   if not entries:
       sys.exit(0)
   norm = [re.sub(r"\s+", " ", e).strip().lower() for e in entries]
   counts = collections.Counter(norm)
   offenders = [(r, c) for r, c in counts.most_common() if c > 3]
   if offenders:
       print(f"FAIL: {len(entries)} entries, {len(counts)} distinct reasons.")
       print("Reasons repeated >3 times (boilerplate):")
       for r, c in offenders[:10]:
           print(f"  {c}× {r[:120]}")
       sys.exit(1)
   print(f"OK: {len(entries)} entries, {len(counts)} distinct reasons, max repeat {max(counts.values())}.")
   PY
   ```

   > **Intent:** the only honest reason strings name the specific type at the specific call site, so they naturally don't repeat. A reason that appears on more than 3 entries is boilerplate — either a canonical tool-generated string or a mass-rewritten substitute. Legitimate clusters of >3 sibling false positives (e.g. five `setDestinationDir` calls across `buildSrc`) should be grouped under a `### Heading` and given per-entry reasons that name the site (`Sync in buildSrc MavenPluginPlugin`, `Sync in buildSrc RepoConfigurer`, …).

   **Both checks must pass.** If either fails, return to step 4 and process the offending entries. Do not commit.

   - If `MIGRATION_NOTES.md` has zero entries or only a small curated set of grouped false positives with site-specific reasons, good — proceed to the commit checkpoint.
   - If the file ends up empty, delete it. It should not be committed with no body.

## Commit checkpoint (mandatory before moving on)

Before starting task 07, commit the changes from this task:

- Subject: `Migrate Build Scripts and Gradle API Usages` (the task title)
- Include the `Assistant:` trailer (see CONTEXT.md)
- If `MIGRATION_NOTES.md` has any entries after step 4, stage it alongside the transformed files — but **only after** both step 5 audits have passed. A `MIGRATION_NOTES.md` that still contains raw `apply_migrations.py` boilerplate reasons must not be committed.
- After committing, run `git status` and confirm the working tree is clean

Do **not** run `./gradlew` (or any other Gradle invocation) to validate the changes. See the "Hard rule" at the top of this task. We want only changes derivable from `migration-data.json` in this changeset; build validation and iteration happen in tasks 07 and 08.

Do not combine these changes with a later task's commit. See the "Commit Discipline" section in CONTEXT.md.

## Done when

- All build scripts **and** all Java/Kotlin/Groovy source files that use Gradle API types have been scanned and transformed according to `migration-data.json`
- Re-running `scan_usages.py` shows zero `[CONFIRMED]` Cat-A / Cat-B hits and zero Cat-C hits in `.gradle` / `.gradle.kts` files
- `MIGRATION_NOTES.md` has either been deleted (no remaining deferrals) or contains only human-curated entries with site-specific reasons. Both step-5(b) audits pass: the canonical-boilerplate grep returns `0`, and the distinct-reason Python script prints `OK` with no reason repeating more than 3 times
- A commit with subject `Migrate Build Scripts and Gradle API Usages` exists on the migration branch and `git status` is clean
- No Gradle command was executed during this task (validation belongs to tasks 07 and 08)
