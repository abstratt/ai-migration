# Task: Install JDK

@tasks/CONTEXT.md

## Preconditions

- Task 01 has completed: the clone directory exists with the fork checked out on the migration branch
- SDKMAN is installed at `$HOME/.sdkman` (this is a hard requirement — see step 2)

## Resume check

Check that `JAVA_HOME` is set, starts with `$HOME/.sdkman/candidates/java/`, and `java -version` reports the expected major version from a Temurin build — if so, this task is already complete.

If `JAVA_HOME` is unset, points outside SDKMAN, or reports the wrong version/vendor, do not accept it as-is — run the instructions below.

## Instructions

1. **Determine required Java version** from the build configuration of the cloned repo (e.g. `toolchain { languageVersion }`, `sourceCompatibility`, `targetCompatibility`, `JAVA_HOME` hints in CI files). Default to 21 if unclear.

2. **Install and activate the JDK via SDKMAN — this is the only supported path.**

   First, verify SDKMAN is available. If this fails, **abort the task immediately** and report the error to the user. Do not attempt to install SDKMAN yourself, and do not fall back to another JDK source.
   ```bash
   source "$HOME/.sdkman/bin/sdkman-init.sh"
   ```

   Then install the required Temurin build and activate it:
   ```bash
   sdk install java <version>-tem   # e.g. 17.0.14-tem, 21.0.7-tem
   sdk use java <version>-tem
   export JAVA_HOME="$HOME/.sdkman/candidates/java/current"
   ```

   If `sdk install` fails for any reason (network error, version not listed, checksum failure, etc.), **abort the task and surface the error to the user**. Do not retry with a different vendor, a different major version, or a different installation method.

   **Do not, under any circumstances:**
   - Install SDKMAN yourself or bootstrap it through another package manager
   - Install a JDK through Homebrew, apt, yum, `/usr/libexec/java_home`, manual tarball download, or any non-SDKMAN mechanism
   - Use a pre-existing system JDK even if `java -version` already works and happens to match
   - Substitute a different vendor (`-zulu`, `-oracle`, `-graal`, `-amzn`, etc.) for `-tem`
   - Substitute a different major version than the one determined in step 1
   - Proceed to later tasks if `JAVA_HOME` is unset or points outside `$HOME/.sdkman/candidates/java/` — stop and report to the user instead

## Done when

- `JAVA_HOME` is set and its path starts with `$HOME/.sdkman/candidates/java/`
- `java -version` succeeds, reports the exact major version determined in step 1, and identifies the build as Temurin
