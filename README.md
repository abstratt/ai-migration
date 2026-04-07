# Gradle 10 Migration

Automated migration of Gradle build scripts to the Gradle 10 Provider API. Can be run locally via Claude Code slash commands or headlessly in a container.

## Option 1: Slash commands (local)

The migration workflow is available as Claude Code slash commands.

### Full workflow

```
/migrate https://github.com/owner/repo
/migrate https://github.com/owner/repo/tree/some-branch
```

Runs all tasks in order. The repository URL (and optional branch) is passed as an argument.

### Individual tasks

| Command | Description | Arguments |
|---|---|---|
| `/setup <repo-url>` | Clone repo, create migration branch, install JDK | Repository URL (required) |
| `/upgrade-gradle-9` | Upgrade Gradle wrapper to 9.4 | None (uses cloned repo) |
| `/swap-distribution` | Swap to custom Provider API distribution | None |
| `/migrate-build-scripts` | Apply migration rules to build scripts | None |
| `/verify-help` | Run `./gradlew help` and fix errors | None |
| `/verify-assemble` | Run `./gradlew assemble` and fix errors | None |
| `/report` | Generate migration report | None |

Tasks after `/setup` operate on the already-cloned repository and don't require additional arguments.

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
  --user 1000 \
  --memory="16g" \
  -e REPO_URL \
  -e CLAUDE_CODE_OAUTH_TOKEN \
  -v "$REPO_DIR":/workspace \
  -v ~/.claude:/home/claude/.claude:ro \
  -v ~/.config/gh:/home/claude/.config/gh:ro \
  localhost/gradle-migration \
  claude --dangerously-skip-permissions \
  --system-prompt-file /MIGRATION.md \
  --verbose \
  -p "run the migration, then print a summary of everything you did, and include the timing for the entire execution"
```
