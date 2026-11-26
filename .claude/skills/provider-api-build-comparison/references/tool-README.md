# Comparing Gradle task graphs and task inputs/outputs across Gradle versions

Develocity build scan comparison stops being useful when the two builds ran on different Gradle versions: the Gradle version is part of every task's cache key, so every task is reported as having different inputs.

`task-dump.init.gradle` sidesteps that. It writes, for one build, a JSON file with the executed task graph and each task's inputs and outputs in a form that does not include the Gradle version or the task implementation classpath. Two such files can be compared directly.

## Files

| File | Purpose |
|---|---|
| `task-dump.init.gradle` | Init script that writes the dump |
| `compare_dumps.py` | Prints the differences between two dumps as plain text |
| `skip-kotlin-metadata-check.init.gradle` | Example of a workaround applied to both builds (see below) |
| `classify_diffs.py` | Groups differences by kind, counts adapter reads, compares against a control run |

## Invocation sample

Run the same tasks in both checkouts, each with its own Gradle distribution:

```sh
# before: baseline commit, Gradle 9.9.2 via the wrapper
cd ~/work/project-before
./gradlew clean assemble \
    --no-build-cache --no-configuration-cache --no-scan \
    -I ~/tools/skip-kotlin-metadata-check.init.gradle \
    -I ~/tools/task-dump.init.gradle \
    -Dtaskdump.out=$HOME/work/dump-before.json

# after: migrated commit, a locally built Gradle distribution
cd ~/work/project-after
~/gradle-dists/provider-api/bin/gradle clean assemble \
    --no-build-cache --no-configuration-cache --no-scan \
    -I ~/tools/skip-kotlin-metadata-check.init.gradle \
    -I ~/tools/task-dump.init.gradle \
    -Dtaskdump.out=$HOME/work/dump-after.json

# compare (add --verbose to list every file instead of the first few)
python3 compare_dumps.py ~/work/dump-before.json ~/work/dump-after.json
```

Flags that matter:

- `-Dtaskdump.out=<file>` is required; the script fails the build without it.
- `--no-configuration-cache` is required: the script uses `taskGraph.whenReady`, `taskGraph.beforeTask` / `afterTask` and `buildFinished`.
- `clean` and `--no-build-cache` make every task actually run, so outputs are produced by the build being measured.
- `--no-scan` is only there for builds that publish a build scan on every invocation.
- If one build needs a workaround to run at all, apply it to **both** builds, as the sample does with `skip-kotlin-metadata-check.init.gradle`. Otherwise the workaround itself shows up as a difference. Here both builds need it: the project's Kotlin 2.2.0 compiler rejects the Kotlin 2.4 metadata of either Gradle distribution. Leave that `-I` line out when no workaround is needed.
- If the project derives its version from Git (as `gradle-lint-plugin` does through Nebula), pin it on both sides, for example `-Prelease.version=0.0.0-compare`, so archive names match.

## What the dump contains

```json
{
  "gradleVersion": "9.9.2",
  "requestedTasks": ["clean", "assemble"],
  "buildFailed": false,
  "executionOrder": [":clean", ":compileGroovy", "..."],
  "tasks": {
    ":compileGroovy": {
      "type": "org.gradle.api.tasks.compile.GroovyCompile",
      "outcome": "executed",
      "dependsOn": [],
      "inputProperties": { "groovyOptions.encoding": "UTF-8" },
      "inputFiles":  { "classpath": { "attrs": "...", "files": { "<gradle-home>/lib/groovy-4.0.29.jar": "9c1f…" } } },
      "outputFiles": { "destinationDirectory": { "attrs": "...", "files": { "<root>/build/classes/groovy/main/Foo.class": "41ab…" } } },
      "publicInputProperties": {},
      "allInputFiles": {},
      "allOutputFiles": {}
    }
  }
}
```

- `outcome` is one of `executed`, `up-to-date`, `no-source`, `skipped:<message>`, `failed`, `not-run`.
- `dependsOn` lists the task's direct dependencies in the execution graph.
- File entries map a normalized path to the first 16 hex digits of the SHA-256 of the content. Input directories get one tree hash; output directories are expanded to individual files.
- Paths are normalized so two machines or checkouts line up: `<root>` (project root), `<gradle-home>` (distribution), `<gradle-user-home>`, `<home>`, `<gradle-version>`, and `/transforms/<hash>/`.
- `attrs` is the property's declaration (optional, normalizer, sensitivity, file or directory).

## Limitations

- Per-property data (`inputProperties`, `inputFiles`, `outputFiles`) is read through Gradle internals (`TaskPropertyUtils` and `PropertyWalker`). If that fails on some Gradle version the task gets a `propertyWalkError` and only the public-API totals (`publicInputProperties`, `allInputFiles`, `allOutputFiles`) are available.
- Inputs are read in `beforeTask`, immediately before each task's actions run (when Gradle fingerprints them); outputs in `afterTask`, immediately after it finishes. A task that never started or finished (failed build) is read at the end instead and marked `inputsReadAfterBuild` / `outputsReadAfterBuild`.
- File content is hashed raw. Classpath normalization (ABI-only comparison, ignored manifest attributes) is not applied, so a jar that Gradle would treat as unchanged can still show as changed.
- Objects without a stable `toString()` are recorded as text with identity hashes stripped; a difference there says nothing about the object's content.
- Each build writes its own file: the root build writes the file named by `-Dtaskdump.out`, and every included build and `buildSrc` writes `<name>-<rootProject.name>.json` next to it (for example `dump-before-buildSrc.json`). Compare them pair by pair.
- A difference in an output file is not necessarily caused by the Gradle version. Before attributing one, rerun the task on both sides in fresh daemons (`--stop`, then `<task> --rerun`) and compare again; in `micronaut-core` three generated classes differed in the dumps but were identical when recompiled that way.
- Tested on Gradle 9.5.1, 9.9.2 and a Gradle 9.9.0 development build.

## Reports

Finished reports are in `semantic-comparisons/` of the ai-migration repo. The reason mnemonics in them are not produced by the scripts; they are assigned per project and checked by hand, and each report's legend states the basis for each one.
