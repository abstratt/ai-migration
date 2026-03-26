### Install podman

### Build the image

podman build -t gradle-migration . 

### Run a migration

Run example:


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


