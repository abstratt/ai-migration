# Context for AI sessions

> **Scope:** this file is for sessions working **on the generator itself** — editing `extract_data.sh` or `generate_report.py`, or rerunning the pipeline against new Gradle distributions. It is **not** for Gradle-10 migration sessions; those should load `../tasks/CONTEXT.md` plus `../migration-reference/migration-data.json` and `../migration-reference/MIGRATION_RULES.md` instead. If you arrived here during a migration run, back out — nothing under `generator/` is part of the migration workflow.

## What this is

A report generator that compares Gradle 10 preview vs 9.4.0 to catalog every `@ReplacesEagerProperty`-annotated property under all public API packages (see https://docs.gradle.org/current/userguide/public_apis.html).

Outputs (both produced by `generate_report.py`, both written to the sibling `../migration-reference/` directory):
- `gradle-10-migration-report.md` — human-readable report (captured via stdout redirect)
- `migration-data.json` — structured lookup table for AI migration sessions

For AI-driven migrations, load `../migration-reference/migration-data.json` (the lookup table) together with `../migration-reference/MIGRATION_RULES.md` (transformation rules by property kind). The human report is not needed. This directory (`generator/`) holds only hand-written pipeline source (`extract_data.sh`, `generate_report.py`, docs). All generated artifacts — including the javap caches — live in `../migration-reference/`.

To iterate, edit `generate_report.py` and re-run — the cached javap data means no downloads needed.

## Prerequisites

- **Java 21+** for `javap` to read Gradle 10 class files. Install/switch via SDKMAN: `sdk use java 21.0.10-tem`

## Source distributions

Default URLs are in `extract_data.sh`. They can be overridden via positional arguments:
```bash
./extract_data.sh [gradle-10-url] [gradle-9-url]
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

All generated artifacts live in `../migration-reference/`. The source scripts live here.

```
  generator/extract_data.sh [g10-url] [g94-url]
        │
        │  downloads, extracts JARs, runs javap
        ▼
  ../migration-reference/
    annotated-classes-v2.txt   (which classes to look at)
    g10-javap-v2.txt           (Gradle 10 annotation details — javap -v)
    comparison-v2.txt          (9.4 vs 10 public signatures — javap -public)
    hierarchy-v2.txt           (class declarations for ALL public API classes — for inheritance)
        │
        ▼
  generator/generate_report.py   (reads the four .txt files above)
        │
        ├──▶ ../migration-reference/gradle-10-migration-report.md  (stdout redirect, human)
        └──▶ ../migration-reference/migration-data.json            (structured, written directly)

  ../migration-reference/MIGRATION_RULES.md   (hand-written, transformation rules by kind)
  ../migration-reference/scan_usages.py       (hand-written scanner used by task 04)
```

The `.txt` files are cached intermediate data. Re-running `extract_data.sh` overwrites them in `../migration-reference/`.

## For AI migration sessions

Load these two files into context from the `migration-reference/` sibling directory:
1. `migration-reference/migration-data.json` — look up class + property to get `kind`, `old_type`, `new_type`, `removed_accessors`, `also_known_as`
2. `migration-reference/MIGRATION_RULES.md` — apply the rule matching the `kind` field

The `also_known_as` field lists public API subtypes that inherit the property (e.g. `JavaForkOptions.maxHeapSize` lists `Test`, `JavaExec`, etc.). When scanning user code, search for imports of both `class` and all `also_known_as` entries.
