#!/usr/bin/env python3
"""
Extract @ReplacesEagerProperty annotated methods from javap -v output,
using the simple javap output for clean type names.
"""
import re
import sys
from collections import OrderedDict

def build_hierarchy(filepath):
    """Parse hierarchy-v2.txt to build a type hierarchy of all public API classes.

    Each line is a javap class declaration like:
      public abstract class org.gradle.api.tasks.testing.Test extends org.gradle.api.tasks.testing.AbstractTestTask {
      public interface org.gradle.api.artifacts.repositories.MavenArtifactRepository extends org.gradle.api.artifacts.repositories.ArtifactRepository,org.gradle.api.artifacts.repositories.UrlArtifactRepository {

    Returns:
      parents: {class_fqn: set(direct_supertype_fqns)}
      children: {class_fqn: set(direct_subtype_fqns)}  (inverted graph)
    """
    parents = {}   # class -> set of direct supertypes
    children = {}  # class -> set of direct subtypes

    with open(filepath) as f:
        for line in f:
            line = line.strip().rstrip('{').strip()
            if not line:
                continue

            # Extract the class/interface name
            # Pattern: public [abstract|final] (class|interface) FQCN [extends X] [implements Y,Z]
            m = re.match(
                r'public\s+(?:abstract\s+|final\s+)*(?:class|interface)\s+'
                r'([\w.]+)'
                r'(?:\s+extends\s+([\w.,\s<>?]+?))?'
                r'(?:\s+implements\s+([\w.,\s<>?]+?))?$',
                line
            )
            if not m:
                continue

            cls = m.group(1)
            supertypes = set()

            for group in (m.group(2), m.group(3)):
                if group:
                    for t in group.split(','):
                        t = t.strip()
                        # Strip generic params for hierarchy purposes
                        t = re.sub(r'<.*>', '', t)
                        if t and t.startswith('org.gradle.'):
                            supertypes.add(t)

            parents[cls] = supertypes
            for sup in supertypes:
                children.setdefault(sup, set()).add(cls)

    return parents, children


def find_all_subtypes(cls, children_map):
    """Walk the children graph transitively to find all subtypes of cls."""
    result = set()
    queue = list(children_map.get(cls, []))
    while queue:
        child = queue.pop()
        if child not in result:
            result.add(child)
            queue.extend(children_map.get(child, []))
    return result


def parse_simple_javap(filepath):
    """Parse simple javap output (javap -public) to get method signatures per class."""
    with open(filepath) as f:
        content = f.read()

    classes = {}
    sections = content.split("##########")
    i = 1
    while i < len(sections):
        class_name = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""
        i += 2
        if not class_name:
            continue

        for version in ("BASE", "G10"):
            marker = f"--- {version} ---"
            start = body.find(marker)
            if start == -1:
                continue
            next_marker = body.find("--- ", start + len(marker))
            section = body[start:next_marker] if next_marker != -1 else body[start:]

            methods = []
            for m in re.finditer(
                r'public\s+((?:abstract\s+|static\s+|default\s+|final\s+)*)'
                r'([\w.<>\[\]?, $]+)\s+'
                r'([\w]+)\((.*?)\);',
                section
            ):
                methods.append({
                    'modifiers': m.group(1).strip(),
                    'return_type': m.group(2).strip(),
                    'name': m.group(3).strip(),
                    'params': m.group(4).strip(),
                })
            classes[(class_name, version)] = methods

    return classes


def find_annotated_methods(filepath):
    """Find method names annotated with @ReplacesEagerProperty from javap -v."""
    with open(filepath) as f:
        content = f.read()

    results = {}  # class -> set of method names
    sections = content.split("##########")
    i = 1
    while i < len(sections):
        class_name = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""
        i += 2
        if not class_name or ".internal." in class_name:
            continue

        # Find methods section
        brace = body.find("\n{")
        if brace == -1:
            continue
        methods_section = body[brace:]

        # Split into method blocks
        method_blocks = re.split(r'\n  (?=public |protected |private )', methods_section)

        annotated = set()
        for block in method_blocks:
            if "ReplacesEagerProperty" not in block:
                continue

            sig_match = re.match(
                r'(public\s+(?:abstract\s+|static\s+|default\s+|final\s+)*)'
                r'([\w.<>\[\]?, $]+)\s+'
                r'([\w]+)\((.*?)\);',
                block.strip()
            )
            if sig_match:
                method_name = sig_match.group(3).strip()
                # Extract originalType from annotation
                original_type = None
                ot_match = re.search(r'originalType\s*=\s*class\s+L([\w/$]+);', block)
                if ot_match:
                    original_type = ot_match.group(1).replace('/', '.')
                else:
                    ot_match = re.search(r'originalType\s*=\s*(\w)\b', block)
                    if ot_match:
                        prim_map = {'Z': 'boolean', 'I': 'int', 'J': 'long', 'D': 'double', 'F': 'float'}
                        val = ot_match.group(1)
                        if val in prim_map:
                            original_type = prim_map[val]
                annotated.add((method_name, original_type))

        if annotated:
            results[class_name] = annotated

    return results


def simplify(t):
    """Simplify Java type for display."""
    if not t:
        return t
    subs = [
        ('org.gradle.api.provider.Property', 'Property'),
        ('org.gradle.api.provider.SetProperty', 'SetProperty'),
        ('org.gradle.api.provider.ListProperty', 'ListProperty'),
        ('org.gradle.api.provider.MapProperty', 'MapProperty'),
        ('org.gradle.api.provider.Provider', 'Provider'),
        ('org.gradle.api.file.DirectoryProperty', 'DirectoryProperty'),
        ('org.gradle.api.file.RegularFileProperty', 'RegularFileProperty'),
        ('org.gradle.api.file.ConfigurableFileCollection', 'ConfigurableFileCollection'),
        ('org.gradle.api.file.FileCollection', 'FileCollection'),
        ('java.lang.String', 'String'),
        ('java.lang.Boolean', 'Boolean'),
        ('java.lang.Integer', 'Integer'),
        ('java.lang.Object', 'Object'),
        ('java.lang.Iterable', 'Iterable'),
        ('java.io.File', 'File'),
        ('java.io.InputStream', 'InputStream'),
        ('java.io.OutputStream', 'OutputStream'),
        ('java.net.URI', 'URI'),
        ('java.util.List', 'List'),
        ('java.util.Set', 'Set'),
        ('java.util.Map', 'Map'),
    ]
    result = t
    for full, short in subs:
        result = result.replace(full, short)
    # Shorten remaining org.gradle.* to just class name
    result = re.sub(r'org\.gradle(?:\.\w+)+\.(\w+(?:\.\w+)?)', r'\1', result)
    return result


def infer_eager_type(g10_type, original_type_override):
    """Infer what the eager type was from the G10 lazy type."""
    if original_type_override:
        return simplify(original_type_override)

    t = simplify(g10_type)

    if t == 'DirectoryProperty':
        return 'File'
    if t == 'RegularFileProperty':
        return 'File'
    if t == 'ConfigurableFileCollection':
        return 'FileCollection'

    m = re.search(r'MapProperty<(.+)>', t)
    if m:
        return f'Map<{m.group(1)}>'

    m = re.search(r'ListProperty<(.+?)>', t)
    if m:
        return f'List<{m.group(1)}>'

    m = re.search(r'SetProperty<(.+?)>', t)
    if m:
        return f'Set<{m.group(1)}>'

    m = re.search(r'Property<(.+?)>', t)
    if m:
        inner = m.group(1)
        if inner == 'Boolean':
            return 'boolean'
        return inner

    return t



def property_name_from_getter(getter_name):
    """Convert getXxx to xxx."""
    if getter_name.startswith("get") and len(getter_name) > 3:
        return getter_name[3].lower() + getter_name[4:]
    return getter_name


def main():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ref_dir = os.path.join(script_dir, '..', 'migration-reference')
    comparison = parse_simple_javap(os.path.join(ref_dir, 'comparison-v2.txt'))
    annotated = find_annotated_methods(os.path.join(ref_dir, 'g10-javap-v2.txt'))

    # Load class hierarchy for also_known_as computation
    hierarchy_path = os.path.join(ref_dir, 'hierarchy-v2.txt')
    if os.path.exists(hierarchy_path):
        _parents, children_map = build_hierarchy(hierarchy_path)
    else:
        _parents, children_map = {}, {}
        print("WARNING: hierarchy-v2.txt not found, also_known_as will be empty. Run extract_data.sh first.", file=sys.stderr)

    sorted_classes = sorted(annotated.keys())

    # Collect all entries for the report
    all_entries = []

    for cls in sorted_classes:
        ann_methods = annotated[cls]
        base_meths = comparison.get((cls, "BASE"), [])
        g10_meths = comparison.get((cls, "G10"), [])

        # Build lookup by name for both versions
        base_by_name = {}
        for m in base_meths:
            key = m['name']
            if key not in base_by_name:
                base_by_name[key] = []
            base_by_name[key].append(m)

        g10_by_name = {}
        for m in g10_meths:
            key = m['name']
            if key not in g10_by_name:
                g10_by_name[key] = []
            g10_by_name[key].append(m)

        entries = []
        for method_name, original_type in sorted(ann_methods):
            # G10 type from simple javap (no-arg getter)
            g10_type = None
            for m in g10_by_name.get(method_name, []):
                if not m['params']:
                    g10_type = m['return_type']
                    break

            if not g10_type:
                continue

            g10_simple = simplify(g10_type)

            # baseline type
            base_type = None
            for m in base_by_name.get(method_name, []):
                if not m['params']:
                    base_type = m['return_type']
                    break

            # Check is* variant for booleans
            if base_type is None and method_name.startswith("get"):
                prop = method_name[3:]
                is_name = f"is{prop}"
                for m in base_by_name.get(is_name, []):
                    if not m['params']:
                        base_type = m['return_type']
                        break

            eager_type = infer_eager_type(g10_type, original_type)
            base_simple = simplify(base_type) if base_type else eager_type

            # Find removed accessors
            removed = []
            if method_name.startswith("get"):
                prop = method_name[3:]
                # Check setters
                setter_name = f"set{prop}"
                if setter_name in base_by_name and setter_name not in g10_by_name:
                    for m in base_by_name[setter_name]:
                        removed.append(f"`{setter_name}({simplify(m['params'])})`")
                # Check is* getter
                is_name = f"is{prop}"
                if is_name in base_by_name and is_name not in g10_by_name:
                    removed.append(f"`{is_name}()`")

            removed_str = ", ".join(removed) if removed else ""

            entries.append({
                'method': method_name,
                'prop': property_name_from_getter(method_name),
                'base': base_simple,
                'g10': g10_simple,
                'removed': removed_str,
            })

        if entries:
            all_entries.append((cls, entries))

    # Classify each entry by property-type kind and write migration-data.json
    import json

    def classify_kind(e):
        g10 = e['g10']
        base = e["base"]
        if g10.startswith('Provider<'):
            return 'read_only'
        if g10 == 'DirectoryProperty':
            return 'dir'
        if g10 == 'RegularFileProperty':
            return 'file'
        if g10 == 'ConfigurableFileCollection':
            return 'file_collection'
        if 'ListProperty' in g10:
            return 'list'
        if 'SetProperty' in g10:
            return 'set'
        if 'MapProperty' in g10:
            return 'map'
        if base == 'boolean':
            return 'boolean'
        if base in ('String', 'int', 'long'):
            return 'scalar'
        return 'other'

    def clean_removed(removed_str):
        """Strip markdown backticks from removed accessor strings."""
        return [s.strip().strip('`') for s in removed_str.split(',') if s.strip()] if removed_str else []

    # Precompute subtypes for each annotated class (public API only, exclude internal)
    subtypes_cache = {}
    for cls in sorted_classes:
        all_subs = find_all_subtypes(cls, children_map)
        subtypes_cache[cls] = sorted(s for s in all_subs if '.internal.' not in s)

    json_entries = []
    for cls, entries in all_entries:
        for e in entries:
            json_entries.append({
                'class': cls,
                'property': e['prop'],
                'old_type': e["base"],
                'new_type': e['g10'],
                'kind': classify_kind(e),
                'read_only': e['g10'].startswith('Provider<'),
                'removed_accessors': clean_removed(e['removed']),
                'also_known_as': subtypes_cache.get(cls, []),
            })

    json_path = os.path.join(ref_dir, 'migration-data.json')
    with open(json_path, 'w') as f:
        json.dump(json_entries, f, indent=2)
    print(f"Wrote {len(json_entries)} entries to {json_path}", file=sys.stderr)

    # Now generate the full report
    print("# Gradle 10 Lazy Property Migration Report")
    print()
    print("Properties annotated with `@ReplacesEagerProperty` in Gradle 10 preview (`gradle-provider-api-20260204140400`), compared against Gradle 9.4.0.")
    print()
    print("> **What does `@ReplacesEagerProperty` mean?**")
    print("> In Gradle 10, eager getters/setters (e.g. `String getFoo()` / `void setFoo(String)`) are replaced by lazy provider-based properties (e.g. `Property<String> getFoo()`). The annotation marks these new lazy accessors and instructs Gradle's bytecode instrumentation to intercept calls to the old eager API, bridging them to the new lazy one during the transition.")
    print()
    print("---")
    print()

    # Lazy wiring principles section
    print("## Lazy Wiring Principles")
    print()
    print("The migration to lazy properties is **not** just a mechanical `getFoo()` → `foo.get()` rename. The goal is to keep values **lazy** — evaluated only when needed, typically at task execution time. Calling `.get()` at configuration time defeats the purpose.")
    print()
    print("### Rules of thumb")
    print()
    print("1. **Wire providers to providers** — never unpack a `Provider` just to pass its value to another property:")
    print("   ```groovy")
    print("   // WRONG — eagerly unpacks, breaks task dependency inference")
    print("   taskB.encoding.set(taskA.encoding.get())")
    print()
    print("   // RIGHT — lazy wiring, Gradle infers the task dependency automatically")
    print("   taskB.encoding.set(taskA.encoding)")
    print("   ```")
    print("2. **`.convention()` vs `.set()`** — both are lazy, but they differ in intent. `.convention()` provides a default that can be overridden by `.set()`; `.set()` provides an explicit value. Use `.convention()` when defining a default in a plugin, `.set()` when configuring a task:")
    print("   ```groovy")
    print("   // In a plugin — overridable default")
    print("   task.encoding.convention(\"UTF-8\")")
    print()
    print("   // In a build script — explicit configuration")
    print("   task.encoding.set(\"ISO-8859-1\")")
    print("   ```")
    print("3. **`.get()` is needed when you need the resolved value** — inside task actions, or when passing a value to any API that does not accept `Provider`:")
    print("   ```groovy")
    print("   // Inside a task action")
    print("   task.doLast {")
    print("       println(\"Encoding: ${task.encoding.get()}\")")
    print("   }")
    print()
    print("   // Feeding a lazy value into an API that expects a plain type")
    print("   someApi.configure(compileTask.encoding.get())")
    print("   ```")
    print("4. **For file properties**, prefer `layout`-based APIs over `project.file()`:")
    print("   ```groovy")
    print("   task.outputFile.set(layout.buildDirectory.file(\"report.txt\"))")
    print("   task.baseDir.set(layout.projectDirectory.dir(\"src\"))")
    print("   ```")
    print("6. **For collection properties**, use incremental APIs to add items lazily:")
    print("   ```groovy")
    print("   task.compilerArgs.add(\"-Xlint\")")
    print("   task.compilerArgs.addAll(otherTask.compilerArgs)")
    print("   task.properties.put(\"key\", provider { computeValue() })")
    print("   task.classpath.from(configurations.compileClasspath)")
    print("   ```")
    print()
    print("---")
    print()

    # Summary
    print("## Summary")
    print()
    print("| # | Class | Properties Changed |")
    print("|---|-------|--------------------|")
    total = 0
    for idx, (cls, entries) in enumerate(all_entries, 1):
        short = cls.rsplit('.', 1)[-1]
        count = len(entries)
        total += count
        print(f"| {idx} | `{short}` | {count} |")
    print(f"| | **Total** | **{total}** |")
    print()
    print("---")
    print()

    # Detailed sections
    print("## Detailed Migration Guide")
    print()

    for cls, entries in all_entries:
        print(f"### `{cls}`")
        print()
        print("| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |")
        print("|----------|----------------|----------------|-------------------|")
        for e in entries:
            removed = e['removed'] if e['removed'] else "—"
            print(f"| `{e['prop']}` | `{e["base"]}` | `{e['g10']}` | {removed} |")
        print()

        # Generate migration examples: one per property-type category, concise
        print("**Migration examples:**")
        print()

        # Separate read-only providers from mutable properties
        read_only = [e for e in entries if e['g10'].startswith('Provider<')]
        mutable = [e for e in entries if not e['g10'].startswith('Provider<')]

        # Categorize mutable properties — pick one representative per category
        categories = []  # list of (representative_entry, same_pattern_names, category_key)
        seen = set()

        def categorize(pred, key):
            matches = [e for e in mutable if pred(e) and id(e) not in seen]
            if matches:
                for e in matches:
                    seen.add(id(e))
                rep = matches[0]
                others = [e['prop'] for e in matches[1:]]
                categories.append((rep, others, key))

        categorize(lambda e: e["base"] == 'boolean', 'boolean')
        categorize(lambda e: e["base"] in ('String', 'int', 'long') and 'Property<' in e['g10'], 'scalar')
        categorize(lambda e: e['g10'] == 'DirectoryProperty', 'dir')
        categorize(lambda e: e['g10'] == 'RegularFileProperty', 'file')
        categorize(lambda e: e['g10'] == 'ConfigurableFileCollection', 'filecoll')
        categorize(lambda e: 'ListProperty' in e['g10'], 'list')
        categorize(lambda e: 'SetProperty' in e['g10'], 'set')
        categorize(lambda e: 'MapProperty' in e['g10'], 'map')
        categorize(lambda e: True, 'other')  # catch-all for enums, custom types

        print("```groovy")

        for rep, same_others, cat in categories:
            prop = rep['prop']
            also = ""
            if same_others:
                also = f"  // also: {', '.join(same_others)}"

            if cat == 'boolean':
                print(f"task.{prop}.set(true){also}")
                print(f"task.{prop}.set(otherTask.{prop})  // lazy wiring")
            elif cat == 'scalar':
                eager_val = '"value"' if rep['base'] == 'String' else '4'
                print(f'task.{prop}.set({eager_val}){also}')
                print(f'task.{prop}.set(provider {{ computeValue() }})')
                print(f'task.{prop}.set(otherTask.{prop})  // lazy wiring')
            elif cat == 'dir':
                print(f'task.{prop}.set(layout.projectDirectory.dir("src")){also}')
                print(f'task.{prop}.set(otherTask.{prop})  // lazy wiring')
            elif cat == 'file':
                print(f'task.{prop}.set(layout.buildDirectory.file("output.txt")){also}')
                print(f'task.{prop}.set(otherTask.{prop})  // lazy wiring')
            elif cat == 'filecoll':
                print(f'task.{prop}.setFrom(configurations.someConfig){also}')
                print(f'task.{prop}.setFrom(otherTask.{prop})  // lazy wiring')
            elif cat == 'list':
                print(f'task.{prop}.add("item"){also}')
                print(f'task.{prop}.addAll(otherTask.{prop})  // lazy wiring')
            elif cat == 'set':
                print(f'task.{prop}.add(item){also}')
                print(f'task.{prop}.addAll(otherTask.{prop})  // lazy wiring')
            elif cat == 'map':
                print(f'task.{prop}.put("key", "value"){also}')
                print(f'task.{prop}.putAll(otherTask.{prop})  // lazy wiring')
            else:  # other (enums, custom types)
                print(f'task.{prop}.set(someValue){also}')
                print(f'task.{prop}.set(otherTask.{prop})  // lazy wiring')

        # Read-only providers
        if read_only:
            if categories:
                print()
            ro_props = ", ".join(e['prop'] for e in read_only)
            print(f"// Read-only ({ro_props}) — no .set(); pass the Provider to consumers:")
            prop = read_only[0]['prop']
            print(f'otherTask.someInput.set(task.{prop})')

        print("```")
        print()
        print("---")
        print()

    # General patterns
    print("## General Migration Patterns")
    print()
    print("| 9.4 Pattern | 10 — Configuration (lazy) | 10 — Execution time only |")
    print("|-------------|---------------------------|--------------------------|")
    print("| `taskB.setFoo(taskA.getFoo())` | `taskB.foo.set(taskA.foo)` | — |")
    print("| `task.setFoo(value)` | `task.foo.set(value)` | — |")
    print("| `task.setFoo(computed)` | `task.foo.set(provider { computed })` | — |")
    print("| `val x = task.getFoo()` | Pass `task.foo` as a `Provider` | `task.foo.get()` in a task action |")
    print("| `task.isFoo()` | Wire `task.foo` as `Provider<Boolean>` | `task.foo.get()` in a task action |")
    print("| `task.getFoo()` → `File` | Wire `task.foo` as `Provider<Directory>` | `task.foo.get().asFile` in a task action |")
    print("| `task.getFoo()` → `List<T>` | `task.foo.add(item)` / `.addAll(provider)` | `task.foo.get()` in a task action |")
    print("| `task.getFoo()` → `Set<T>` | `task.foo.add(item)` / `.addAll(provider)` | `task.foo.get()` in a task action |")
    print("| `task.getFoo()` → `Map<K,V>` | `task.foo.put(k, v)` / `.putAll(provider)` | `task.foo.get()` in a task action |")
    print("| `task.getFoo()` → `FileCollection` | `task.foo.setFrom(source)` (use `.from(...)` only to append) | Iterate in a task action |")
    print()
    print("> **Key principle**: `Property` extends `Provider`. Anywhere a `Provider<T>` is accepted, you can pass the `Property<T>` directly — no `.get()` needed. Reserve `.get()` for task actions and `doLast {}` blocks where you need the resolved value.")


if __name__ == '__main__':
    main()
