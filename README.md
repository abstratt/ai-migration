# Gradle 10 Migration

Automated migration of Gradle build scripts to the Gradle 10 Provider API. Can be run locally via Claude Code slash commands or headlessly in a container.

## Option 1: Slash commands (local)

The migration workflow is available as Claude Code slash commands.

### Full workflow

```
/g10-migrate https://github.com/owner/repo
/g10-migrate https://github.com/owner/repo/tree/some-branch
```

Runs all tasks in order. The repository URL (and optional branch) is passed as an argument.

### Individual tasks

| Command | Description | Arguments |
|---|---|---|
| `/g10-prepare-repository <repo-url>` | Clone repo and create migration branch | Repository URL (required) |
| `/g10-install-jdk` | Install the JDK required by the repository | None |
| `/g10-upgrade-gradle-9` | Upgrade Gradle wrapper to 9.x | None |
| `/g10-swap-distribution` | Swap to custom Provider API distribution | None |
| `/g10-record-start-time` | Record migration start time for reporting | None |
| `/g10-migrate-build-scripts` | Apply migration rules to build scripts | None |
| `/g10-verify-help` | Run `./gradlew help` and fix errors | None |
| `/g10-verify-assemble` | Run `./gradlew assemble` and fix errors | None |
| `/g10-report` | Generate migration report | None |

Tasks after `/g10-prepare-repository` operate on the already-cloned repository and don't require additional arguments.

### Running the migrations in an unattended mode

#### Using Claude default cloud-based model


Notice `--permission-mode auto`, use at your own peril.

```
claude --permission-mode auto "/g10-migrate https://github.com/abstratt/spring-boot.git"
```

#### Using Ollama+Claude to leverage a local model

(requires installing Ollama and pulling the local model beforehand)


Notice `--dangerously-skip-permissions`, use at your own peril.
```
ollama launch claude --model qwen3.5:35b-a3b-coding-nvfp4 -- \
    --dangerously-skip-permissions \
    "/g10-migrate https://github.com/abstratt/spring-boot.git"
```



### Benchmarking

```
/g10-benchmark <repo-url> <branch-1>=<label-1> <branch-2>=<label-2>
```

Off-pipeline command that compares two already-completed migration branches on the same repository and writes a `BENCHMARK-*.md` report to the project root. Does not commit to the migrated repo.

## Option 2: Container (headless)

### Build the image

```
podman build -t gradle-migration .
```

### Run a migration

```
export REPO_URL=https://github.com/androidx/androidx.git ; \
export REPO_DIR="$(pwd)/androidx" ; \
mkdir $REPO_DIR ; \
podman run --rm \
  --user 1001 \
  --memory="16g" \
  -e REPO_URL \
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
