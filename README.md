# Gradle 10 Migration

Automated migration of Gradle build scripts to the Gradle 10 Provider API. Can be run locally via Claude Code slash commands or headlessly in a container.

## Distro pairs

A migration is defined by a **distro pair**: a *baseline* Gradle release plus a *target* Gradle 10 preview distribution. Pairs are declared in [`distro-pairs.json`](distro-pairs.json) at the repo root, and the selected pair drives the whole workflow consistently — the baseline version the wrapper is upgraded to, the target distribution that gets installed, the `migration-data.json` that the rewrites are applied from, and the pair id appended to the migration branch name (`gradle-10-migration/<timestamp>-<pair-id>`).

Each pair's generated data — its **distro mapping bundle** — lives in `migration-reference/distro-pairs/<pair-id>/` and is produced by the `generator/` pipeline. See [`generator/README.md`](generator/README.md) for how bundles are built and what they contain.

The workflow uses the manifest's `default` pair unless you override it with the **`DISTRO_PAIR`** environment variable. **A pair must have a built bundle before you can migrate against it** — otherwise the build-script task aborts with `migration-data.json not found`.

### Managing distro pairs

| Command | Description | Arguments |
|---|---|---|
| `/g10-show-distro-pairs` | List defined pairs (id, label, baseline/target URLs, the `default` marker, and bundle status) | None |
| `/g10-build-bundle [pair-id]` | Build (or rebuild) a pair's distro mapping bundle by running the generator pipeline (downloads both distributions, runs `javap`). Prompts you to pick a pair if none is given. | Pair id (optional) |

To add a new pair, edit `distro-pairs.json` by hand (a new object in `pairs[]` with `id`, `label`, `baseline_url`, `target_url`), then build its bundle with `/g10-build-bundle <id>`.

## Option 1: Slash commands (local)

The migration workflow is available as Claude Code slash commands.

### Full workflow

```
/g10-migrate https://github.com/owner/repo
/g10-migrate https://github.com/owner/repo/tree/some-branch
```

Runs all tasks in order. The repository URL (and optional branch) is passed as an argument. The migration targets the `default` distro pair from `distro-pairs.json`; set `DISTRO_PAIR=<pair-id>` to target a different one (see [Distro pairs](#distro-pairs)).

Each run starts clean: step 0 scrubs the prior run's on-disk state for this repo (the reused `migrated/<repo>` clone and its start-time sidecar) before migrating — because clearing the conversation context does **not** reset on-disk state. To **resume** an interrupted run instead of starting clean, use `/g10-resume <partial-name>`, which runs the same workflow but skips step 0. It takes a partial repository name (not a URL): it matches every clone under `migrated/` and continues only if exactly one matches (e.g. `/g10-resume spring-boot`), aborting if the name is ambiguous or unknown. Tune the cleanup with `RESET_STATE`: unset = safe reset (default); `RESET_STATE=purge` also deletes and re-clones the repo; `RESET_STATE=keep` (or `off`) skips the cleanup (the env-var equivalent of `/g10-resume`). Run `/g10-clear-repository-state <repo-url>` to clear a repo's state on its own.

#### Example

```
claude --permission-mode auto "/g10-migrate https://github.com/abstratt/spring-framework"
```

Targeting a specific pair:

```
DISTRO_PAIR=g94-to-PAPI-20260204 claude --permission-mode auto "/g10-migrate https://github.com/abstratt/spring-framework"
```

### Individual tasks

| Command | Description | Arguments |
|---|---|---|
| `/g10-clear-repository-state <repo-url>` | Scrub a previous run's on-disk state (clone + start-time sidecar) for a clean start | Repository URL (required) |
| `/g10-prepare-repository <repo-url>` | Clone repo and create migration branch | Repository URL (required) |
| `/g10-install-jdk` | Install the JDK required by the repository | None |
| `/g10-upgrade-gradle-9` | Upgrade Gradle wrapper to the pair's baseline version | None |
| `/g10-swap-distribution` | Swap in the pair's target Provider API distribution | None |
| `/g10-record-start-time` | Record migration start time for reporting | None |
| `/g10-migrate-build-scripts` | Apply migration rules to build scripts | None |
| `/g10-verify-help` | Run `./gradlew help` and fix errors | None |
| `/g10-verify-assemble` | Run `./gradlew assemble` and fix errors | None |
| `/g10-report` | Generate migration report | None |

Tasks after `/g10-prepare-repository` operate on the already-cloned repository and don't require additional arguments.

### Running the migrations in an unattended mode

#### Using Claude's default cloud-based model

Notice `--permission-mode auto` — use at your own peril.

```
claude --permission-mode auto "/g10-migrate https://github.com/abstratt/spring-boot"
```

##### Letting Claude find skills by itself

Prompt:

> I want to run migration for git@github.com:abstratt/micronaut-core.git


#### Using Ollama + Claude to leverage a local model

Requires installing Ollama and pulling the local model beforehand. Notice `--dangerously-skip-permissions` — use at your own peril.

```
ollama launch claude --model qwen3.5:35b-a3b-coding-nvfp4 -- \
    --dangerously-skip-permissions \
    "/g10-migrate https://github.com/abstratt/spring-boot"
```



### Benchmarking

```
/g10-benchmark <repo-url> <branch-1>=<label-1> <branch-2>=<label-2>
```

Off-pipeline command that compares two already-completed migration branches on the same repository and writes a `BENCHMARK-*.md` report to the project root. Does not commit to the migrated repo.

#### Example

```
claude --permission-mode auto "/g10-benchmark https://github.com/abstratt/spring-framework gradle-10-migration/20260430-1001=v6-opus gradle-10-migration/20260430-1024=v6-qwen3.6:35b-a3b-coding-nvfp"
```

### Comparing migrations across distro-pairs

Preparation: fork the OSS repository you want to explore migrating 

Prompt:

>  I want to run migration for <forked repository git URL> using both distro pairs. Use separate agents for each so they don't share context. Do not run them in parallel as they would compete for the same local file system location. Push both migrated branches. Finally, run the comparison between the two runs.

## Option 2: Container (headless)

### Build the image

```
podman build -t gradle-migration .
```

### Run a migration

```
export REPO_URL=https://github.com/androidx/androidx ; \
export REPO_DIR="$(pwd)/androidx" ; \
mkdir $REPO_DIR ; \
podman run --rm \
  --user 1001 \
  --memory="16g" \
  -e REPO_URL \
  -e DISTRO_PAIR \
  -e CLAUDE_CODE_OAUTH_TOKEN \
  -v "$REPO_DIR":/workspace \
  -v ~/.claude:/home/claude/.claude:ro \
  -v ~/.config/gh:/home/claude/.config/gh:ro \
  localhost/gradle-migration \
  claude --dangerously-skip-permissions \
  --add-dir /migration-tooling \
  --append-system-prompt-file /migration-tooling/MIGRATION.md \
  --verbose \
  -p "run the migration, then print a summary of everything you did, and include the timing for the entire execution"
```

`DISTRO_PAIR` is optional — omit it (or leave it unset) to use the `default` pair from `distro-pairs.json`. The bundle for the chosen pair must already be built in the tooling repo (see [Distro pairs](#distro-pairs)).
