# Context for AI sessions

> **Scope:** this file is for sessions working **on the generator itself** — editing `extract_data.sh` or `generate_report.py`, or rerunning the pipeline against new Gradle distributions. It is **not** for Gradle-10 migration sessions; those should load `../tasks/CONTEXT.md` plus the selected pair's `../migration-reference/distro-pairs/<pair-id>/migration-data.json` and `../migration-reference/MIGRATION_RULES.md` instead. If you arrived here during a migration run, back out — nothing under `generator/` is part of the migration workflow.

## What this is

A report generator that compares a Gradle 10 preview ("target") distribution against a baseline Gradle release to catalog every `@ReplacesEagerProperty`-annotated property under all public API packages (see https://docs.gradle.org/current/userguide/public_apis.html).

A migration is defined by a **distro pair** (baseline + target) declared in `../distro-pairs.json`; each pair's `id` selects a **distro mapping bundle** — the directory of generated files for that pair. See [`README.md`](README.md) for the manifest format and the end-to-end "create a new pair" walkthrough.

Outputs (both produced by `generate_report.py`, both written to the pair's distro mapping bundle `../migration-reference/distro-pairs/<pair-id>/`):
- `gradle-10-migration-report.md` — human-readable report (captured via stdout redirect)
- `migration-data.json` — structured lookup table for AI migration sessions

For AI-driven migrations, load the selected pair's `../migration-reference/distro-pairs/<pair-id>/migration-data.json` (the lookup table) together with `../migration-reference/MIGRATION_RULES.md` (transformation rules by property kind). The human report is not needed. This directory (`generator/`) holds only hand-written pipeline source (`extract_data.sh`, `generate_report.py`, docs). All generated artifacts — including the javap caches — live under `../migration-reference/distro-pairs/<pair-id>/`.

To iterate, edit `generate_report.py` and re-run for the same pair id — the cached javap data means no downloads needed.

## Prerequisites

- **Java 21+** for `javap` to read Gradle 10 class files. Install/switch via SDKMAN: `sdk use java 21.0.10-tem`

## Source distributions

Baseline/target URLs live in `../distro-pairs.json`, one entry per pair. Select a pair by id; with no argument the manifest's `default` pair is used:
```bash
./extract_data.sh [pair-id]
```

## Annotation semantics

- `@ReplacesEagerProperty` (RUNTIME retention) is placed on the new lazy getter (e.g., `Property<String> getEncoding()`). Its source is at: https://github.com/gradle/gradle/blob/95ac47459187c2ae3fd5155fb61c862ea34c0c84/platforms/core-runtime/internal-instrumentation-api/src/main/java/org/gradle/internal/instrumentation/api/annotations/ReplacesEagerProperty.java
- `@ReplacedAccessor` (CLASS retention) names the old accessor being replaced (e.g., `getAnnotationProcessorGeneratedSourcesDirectory`).
- `originalType` attribute overrides the inferred eager type when the mapping isn't straightforward (e.g., `Property<Boolean>` → `boolean` instead of `Boolean`).

## Pitfalls learned the hard way

- **Scan `lib/plugins/` too, not just `lib/`**. The initial version missed 45 classes (CompileOptions, Test, Javadoc, all publishing and code quality types) because they live in plugin JARs.
- **Use `grep -rla`** (with `-a` flag) for binary class files. Plain `grep -rl` can silently miss matches.
- **`Provider<X>` return types are read-only** (e.g., `allCompilerArgs`, `javaVersion`). Don't generate `.set()` examples for these.
- **Some properties were already lazy in 9.4** but have `@ReplacesEagerProperty` because an older accessor name was renamed (e.g., `generatedSourceOutputDirectory` replaces `annotationProcessorGeneratedSourcesDirectory`).

## Design decisions for the report

- **One example per property-type category per class**, not exhaustive. Siblings listed via `// also:` comments.
- **Lazy wiring is the primary pattern** shown in examples. `.get()` is not a mechanical replacement for the old getter.
- **`.get()` is shown where needed**: inside task actions, or when passing a value to any API that does not accept `Provider`.
- **`.convention()` vs `.set()`** is orthogonal to laziness. `.convention()` is a default (overridable); `.set()` is an explicit value. Both are lazy. Don't conflate the two.
- **Read-only `Provider` properties** are separated from mutable `Property` ones in examples.

## Data flow

Per-pair generated artifacts live under `../migration-reference/distro-pairs/<pair-id>/`. The source scripts live here; the hand-written consumer files (`MIGRATION_RULES.md`, `scan_usages.py`, `apply_migrations.py`) live one level up at `../migration-reference/` and are shared across all pairs.

```
  ../distro-pairs.json            (manifest: baseline/target URLs per pair id)
        │
        ▼
  generator/extract_data.sh [pair-id]
        │
        │  resolves pair, downloads, extracts JARs, runs javap
        ▼
  ../migration-reference/distro-pairs/<pair-id>/
    annotated-classes-v2.txt   (which classes to look at)
    g10-javap-v2.txt           (target annotation details — javap -v)
    comparison-v2.txt          (baseline vs target public signatures — javap -public)
    hierarchy-v2.txt           (class declarations for ALL public API classes — for inheritance)
        │
        ▼
  generator/generate_report.py [pair-id]   (reads the four .txt files above)
        │
        ├──▶ ../migration-reference/distro-pairs/<pair-id>/gradle-10-migration-report.md  (stdout redirect, human)
        └──▶ ../migration-reference/distro-pairs/<pair-id>/migration-data.json            (structured, written directly)

  ../migration-reference/MIGRATION_RULES.md   (hand-written, shared, transformation rules by kind)
  ../migration-reference/scan_usages.py       (hand-written, shared, scanner used by task 06)
  ../migration-reference/apply_migrations.py  (hand-written, shared, mechanical rewriter used by task 06)
```

The `.txt` files are cached intermediate data. Re-running `extract_data.sh` for a given pair id overwrites them in that pair's distro mapping bundle.

## For AI migration sessions

Load these two files into context (the first from the selected pair's distro mapping bundle, the second shared at the `migration-reference/` top level):
1. `migration-reference/distro-pairs/<pair-id>/migration-data.json` — look up class + property to get `kind`, `old_type`, `new_type`, `removed_accessors`, `changed_return_accessors`, `new_read_accessor`, `new_write_accessor`, `new_is_provider`, `inheriting_subtypes`
2. `migration-reference/MIGRATION_RULES.md` — apply the rule matching the `kind` field

Schema notes (self-explanatory from the field names; consumers only ever see this JSON):
- `old_type` / `new_type` and accessor parameter types are emitted in **fully-qualified** form (`org.gradle.api.provider.Property<java.net.URI>`, not `Property<URI>`) so OpenRewrite `MethodMatcher` patterns and similar tools resolve unambiguously.
- `removed_accessors` lists Gradle 9 accessors that are gone in Gradle 10 (typically setters and `isX()` boolean readers).
- `changed_return_accessors` lists getters whose name survived but whose return type changed to a lazy form (e.g. `boolean getShowCauses()` → `Property<Boolean> getShowCauses()`); call sites must add `.get()` to reach a primitive value.
- `new_read_accessor` and `new_write_accessor` give the replacement expressions (e.g. `getX().get()`, `getX().set(VALUE)`); `new_write_accessor` is `null` when the new type is `Provider<X>` (no `.set(...)` available — setters in `removed_accessors` need a non-property migration like a varargs builder method).
- `new_is_provider` is `true` iff the new type is `Provider<X>` (not `Property<X>`); orthogonal to whether removed setters had a lazy replacement.
- `inheriting_subtypes` lists public API subtypes that inherit the property (e.g. `JavaForkOptions.maxHeapSize` lists `Test`, `JavaExec`, etc.). When scanning user code, search for imports of both `class` and all `inheriting_subtypes` entries. Accessors removed only on a subtype (e.g. `Delete.isFollowSymlinks()` for `DeleteSpec.followSymlinks`) are unioned into the parent entry's `removed_accessors`.
