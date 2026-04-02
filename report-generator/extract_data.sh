#!/usr/bin/env bash
set -euo pipefail

# Default distribution URLs
DEFAULT_G10_URL="https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip"
DEFAULT_G94_URL="https://downloads.gradle.org/distributions/gradle-9.4.0-bin.zip"

G10_URL="${1:-$DEFAULT_G10_URL}"
G94_URL="${2:-$DEFAULT_G94_URL}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK_DIR="$(mktemp -d)"

cleanup() {
    echo "Cleaning up $WORK_DIR"
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

echo "=== Gradle 10 Migration Data Extraction ==="
echo "Gradle 10 URL: $G10_URL"
echo "Gradle 9.x URL: $G94_URL"
echo "Working directory: $WORK_DIR"
echo ""

# 1. Download
echo "--- Downloading distributions ---"
curl -sL -o "$WORK_DIR/g10.zip" "$G10_URL"
curl -sL -o "$WORK_DIR/g94.zip" "$G94_URL"

g10_size=$(wc -c < "$WORK_DIR/g10.zip" | tr -d ' ')
g94_size=$(wc -c < "$WORK_DIR/g94.zip" | tr -d ' ')
if [ "$g10_size" -lt 1000000 ]; then
    echo "ERROR: Gradle 10 download looks too small ($g10_size bytes). Check the URL." >&2
    exit 1
fi
if [ "$g94_size" -lt 1000000 ]; then
    echo "ERROR: Gradle 9.x download looks too small ($g94_size bytes). Check the URL." >&2
    exit 1
fi
echo "Downloaded: g10=${g10_size} bytes, g94=${g94_size} bytes"

# 2. Extract zips
echo "--- Extracting distributions ---"
mkdir -p "$WORK_DIR/g10" "$WORK_DIR/g94"
unzip -q "$WORK_DIR/g10.zip" -d "$WORK_DIR/g10"
unzip -q "$WORK_DIR/g94.zip" -d "$WORK_DIR/g94"

# Find the top-level directory inside each zip
G10_HOME=$(find "$WORK_DIR/g10" -maxdepth 1 -mindepth 1 -type d | head -1)
G94_HOME=$(find "$WORK_DIR/g94" -maxdepth 1 -mindepth 1 -type d | head -1)
echo "Gradle 10 home: $G10_HOME"
echo "Gradle 9.x home: $G94_HOME"

# 3. Extract org.gradle.api.* classes from ALL JARs (lib/ AND lib/plugins/)
echo "--- Extracting org.gradle.api.* classes ---"
mkdir -p "$WORK_DIR/g10-classes" "$WORK_DIR/g94-classes"

find "$G10_HOME/lib" -name "*.jar" | while read -r jar; do
    unzip -qo "$jar" "org/gradle/api/*.class" "org/gradle/api/**/*.class" -d "$WORK_DIR/g10-classes" 2>/dev/null || true
done
find "$G94_HOME/lib" -name "*.jar" | while read -r jar; do
    unzip -qo "$jar" "org/gradle/api/*.class" "org/gradle/api/**/*.class" -d "$WORK_DIR/g94-classes" 2>/dev/null || true
done

g10_count=$(find "$WORK_DIR/g10-classes/org/gradle/api" -name "*.class" | wc -l | tr -d ' ')
g94_count=$(find "$WORK_DIR/g94-classes/org/gradle/api" -name "*.class" | wc -l | tr -d ' ')
echo "Classes extracted: g10=$g10_count, g94=$g94_count"

# 4. Find annotated classes
echo "--- Finding @ReplacesEagerProperty annotations ---"
cd "$WORK_DIR/g10-classes"
grep -rla "ReplacesEagerProperty" org/gradle/api --include="*.class" | sort > "$WORK_DIR/annotated-classes.txt"
ann_count=$(wc -l < "$WORK_DIR/annotated-classes.txt" | tr -d ' ')
echo "Annotated classes found: $ann_count"

if [ "$ann_count" -eq 0 ]; then
    echo "ERROR: No annotated classes found. Something is wrong." >&2
    exit 1
fi

# 5. Build classpaths
G10_CP=$(find "$G10_HOME/lib" -name "*.jar" | tr '\n' ':')
G94_CP=$(find "$G94_HOME/lib" -name "*.jar" | tr '\n' ':')

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
    echo "--- G94 ---"
    javap -public -cp "$G94_CP" "$classname" 2>/dev/null || true
    echo "--- G10 ---"
    javap -public -cp "$G10_CP" "$classname" 2>/dev/null || true
    echo ""
done < "$WORK_DIR/annotated-classes.txt" > "$WORK_DIR/comparison.txt"

# 8. Copy results to script directory
echo "--- Copying results to $SCRIPT_DIR ---"
cp "$WORK_DIR/annotated-classes.txt" "$SCRIPT_DIR/annotated-classes-v2.txt"
cp "$WORK_DIR/g10-javap.txt" "$SCRIPT_DIR/g10-javap-v2.txt"
cp "$WORK_DIR/comparison.txt" "$SCRIPT_DIR/comparison-v2.txt"

echo ""
echo "=== Done ==="
echo "Updated files:"
echo "  $SCRIPT_DIR/annotated-classes-v2.txt ($ann_count classes)"
echo "  $SCRIPT_DIR/g10-javap-v2.txt ($(wc -l < "$SCRIPT_DIR/g10-javap-v2.txt" | tr -d ' ') lines)"
echo "  $SCRIPT_DIR/comparison-v2.txt ($(wc -l < "$SCRIPT_DIR/comparison-v2.txt" | tr -d ' ') lines)"
echo ""
echo "Now run:  python3 generate_report.py > gradle-10-migration-report.md"
