#!/usr/bin/env bash
set -euo pipefail

# Default distribution URLs
DEFAULT_G10_URL="https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip"
DEFAULT_BASE_URL="https://downloads.gradle.org/distributions/gradle-9.4.0-bin.zip"

G10_URL="${1:-$DEFAULT_G10_URL}"
BASE_URL="${2:-$DEFAULT_BASE_URL}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK_DIR="$(mktemp -d)"

cleanup() {
    echo "Cleaning up $WORK_DIR"
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

echo "=== Gradle 10 Migration Data Extraction ==="
echo "Gradle 10 URL: $G10_URL"
echo "Baseline Gradle URL: $BASE_URL"
echo "Working directory: $WORK_DIR"
echo ""

# 1. Download
echo "--- Downloading distributions ---"
curl -sL -o "$WORK_DIR/g10.zip" "$G10_URL"
curl -sL -o "$WORK_DIR/base.zip" "$BASE_URL"

g10_size=$(wc -c < "$WORK_DIR/g10.zip" | tr -d ' ')
base_size=$(wc -c < "$WORK_DIR/base.zip" | tr -d ' ')
if [ "$g10_size" -lt 1000000 ]; then
    echo "ERROR: Gradle 10 download looks too small ($g10_size bytes). Check the URL." >&2
    exit 1
fi
if [ "$base_size" -lt 1000000 ]; then
    echo "ERROR: Baseline Gradle download looks too small ($base_size bytes). Check the URL." >&2
    exit 1
fi
echo "Downloaded: g10=${g10_size} bytes, base=${base_size} bytes"

# 2. Extract zips
echo "--- Extracting distributions ---"
mkdir -p "$WORK_DIR/g10" "$WORK_DIR/base"
unzip -q "$WORK_DIR/g10.zip" -d "$WORK_DIR/g10"
unzip -q "$WORK_DIR/base.zip" -d "$WORK_DIR/base"

# Find the top-level directory inside each zip
G10_HOME=$(find "$WORK_DIR/g10" -maxdepth 1 -mindepth 1 -type d | head -1)
BASE_HOME=$(find "$WORK_DIR/base" -maxdepth 1 -mindepth 1 -type d | head -1)
echo "Gradle 10 home: $G10_HOME"
echo "Baseline Gradle home: $BASE_HOME"

# 3. Extract classes from ALL public API packages (lib/ AND lib/plugins/)
#    See https://docs.gradle.org/current/userguide/public_apis.html
echo "--- Extracting public API classes ---"
mkdir -p "$WORK_DIR/g10-classes" "$WORK_DIR/base-classes"

# All public API packages from Gradle docs
PUBLIC_API_PATTERNS=(
    "org/gradle/*.class"
    "org/gradle/api/**/*.class"
    "org/gradle/authentication/**/*.class"
    "org/gradle/build/**/*.class"
    "org/gradle/buildconfiguration/**/*.class"
    "org/gradle/buildinit/**/*.class"
    "org/gradle/caching/**/*.class"
    "org/gradle/concurrent/**/*.class"
    "org/gradle/deployment/**/*.class"
    "org/gradle/external/javadoc/**/*.class"
    "org/gradle/ide/**/*.class"
    "org/gradle/ivy/**/*.class"
    "org/gradle/jvm/**/*.class"
    "org/gradle/language/**/*.class"
    "org/gradle/maven/**/*.class"
    "org/gradle/model/**/*.class"
    "org/gradle/nativeplatform/**/*.class"
    "org/gradle/normalization/**/*.class"
    "org/gradle/platform/**/*.class"
    "org/gradle/plugin/devel/**/*.class"
    "org/gradle/plugin/use/*.class"
    "org/gradle/plugin/management/*.class"
    "org/gradle/plugins/**/*.class"
    "org/gradle/process/**/*.class"
    "org/gradle/swiftpm/**/*.class"
    "org/gradle/testing/**/*.class"
    "org/gradle/testfixtures/**/*.class"
    "org/gradle/testkit/**/*.class"
    "org/gradle/tooling/**/*.class"
    "org/gradle/util/**/*.class"
    "org/gradle/vcs/**/*.class"
    "org/gradle/work/**/*.class"
    "org/gradle/workers/**/*.class"
)

find "$G10_HOME/lib" -name "*.jar" | while read -r jar; do
    unzip -qo "$jar" "${PUBLIC_API_PATTERNS[@]}" -d "$WORK_DIR/g10-classes" 2>/dev/null || true
done
find "$BASE_HOME/lib" -name "*.jar" | while read -r jar; do
    unzip -qo "$jar" "${PUBLIC_API_PATTERNS[@]}" -d "$WORK_DIR/base-classes" 2>/dev/null || true
done

g10_count=$(find "$WORK_DIR/g10-classes/org/gradle" -name "*.class" | wc -l | tr -d ' ')
base_count=$(find "/base-classes/org/gradle" -name "*.class" | wc -l | tr -d ' ')
echo "Classes extracted: g10=$g10_count, base=$base_count"

# 4. Find annotated classes
echo "--- Finding @ReplacesEagerProperty annotations ---"
cd "$WORK_DIR/g10-classes"
grep -rla "ReplacesEagerProperty" org/gradle --include="*.class" | sort > "$WORK_DIR/annotated-classes.txt"
ann_count=$(wc -l < "$WORK_DIR/annotated-classes.txt" | tr -d ' ')
echo "Annotated classes found: $ann_count"

if [ "$ann_count" -eq 0 ]; then
    echo "ERROR: No annotated classes found. Something is wrong." >&2
    exit 1
fi

# 5. Build classpaths
G10_CP=$(find "$G10_HOME/lib" -name "*.jar" | tr '\n' ':')
BASE_CP=$(find "$BASE_HOME/lib" -name "*.jar" | tr '\n' ':')

# 6. Run javap -v on annotated classes (Gradle 10 only)
echo "--- Running javap -v (Gradle 10) ---"
while read -r classfile; do
    classname=$(echo "$classfile" | sed 's|/|.|g; s|\.class$||')
    echo "########## $classname ##########"
    javap -v -cp "$G10_CP:." "$classname" 2>/dev/null || true
    echo ""
done < "$WORK_DIR/annotated-classes.txt" > "$WORK_DIR/g10-javap.txt"

# 7. Run javap -public on annotated classes (both versions)
echo "--- Running javap -public (both versions) ---"
while read -r classfile; do
    classname=$(echo "$classfile" | sed 's|/|.|g; s|\.class$||')
    echo "########## $classname ##########"
    echo "--- BASE ---"
    javap -public -cp "$BASE_CP" "$classname" 2>/dev/null || true
    echo "--- G10 ---"
    javap -public -cp "$G10_CP" "$classname" 2>/dev/null || true
    echo ""
done < "$WORK_DIR/annotated-classes.txt" > "$WORK_DIR/comparison.txt"

# 8. Extract class hierarchy for ALL public API classes
#    We need superclass/interface info to resolve inheritance when matching
#    migration entries against user code (e.g. Test implements JavaForkOptions).
echo "--- Extracting class hierarchy (all public API classes) ---"
cd "$WORK_DIR/g10-classes"
find org/gradle -name "*.class" ! -name '*$*' -print0 \
    | xargs -0 -P4 -n200 sh -c '
        for f in "$@"; do
            cn=$(echo "$f" | sed "s|/|.|g; s|\.class$||")
            echo "$cn"
        done | xargs javap -public -cp "'"$G10_CP"':." 2>/dev/null \
            | grep -E "^public (abstract |final )*(class|interface) "
    ' _ > "$WORK_DIR/hierarchy.txt"
hier_count=$(wc -l < "$WORK_DIR/hierarchy.txt" | tr -d ' ')
echo "Class declarations extracted: $hier_count"

# 9. Copy results to script directory
echo "--- Copying results to $SCRIPT_DIR ---"
cp "$WORK_DIR/annotated-classes.txt" "$SCRIPT_DIR/annotated-classes-v2.txt"
cp "$WORK_DIR/g10-javap.txt" "$SCRIPT_DIR/g10-javap-v2.txt"
cp "$WORK_DIR/comparison.txt" "$SCRIPT_DIR/comparison-v2.txt"
cp "$WORK_DIR/hierarchy.txt" "$SCRIPT_DIR/hierarchy-v2.txt"

echo ""
echo "=== Done ==="
echo "Updated files:"
echo "  $SCRIPT_DIR/annotated-classes-v2.txt ($ann_count classes)"
echo "  $SCRIPT_DIR/g10-javap-v2.txt ($(wc -l < "$SCRIPT_DIR/g10-javap-v2.txt" | tr -d ' ') lines)"
echo "  $SCRIPT_DIR/comparison-v2.txt ($(wc -l < "$SCRIPT_DIR/comparison-v2.txt" | tr -d ' ') lines)"
echo "  $SCRIPT_DIR/hierarchy-v2.txt ($hier_count class declarations)"
echo ""
echo "Now run:  python3 generate_report.py > gradle-10-migration-report.md"
