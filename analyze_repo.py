import os
import re

print("=" * 60)
print("MEX-WarSystem Repository Analysis")
print("=" * 60)

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)

            print(f"\nFILE: {path}")
            print("-" * 50)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                imports = re.findall(
                    r'^(?:from\s+([^\s]+)\s+import|import\s+([^\s]+))',
                    content,
                    re.MULTILINE
                )

                funcs = re.findall(
                    r'^def\s+([a-zA-Z0-9_]+)|^async\s+def\s+([a-zA-Z0-9_]+)',
                    content,
                    re.MULTILINE
                )

                classes = re.findall(
                    r'^class\s+([a-zA-Z0-9_]+)',
                    content,
                    re.MULTILINE
                )

                envs = re.findall(
                    r'os\.getenv\(["\']([^"\']+)["\']',
                    content
                )

                print("Imports:")
                for imp in imports[:20]:
                    print(" ", imp[0] or imp[1])

                print("\nClasses:")
                for c in classes:
                    print(" ", c)

                print("\nFunctions:")
                for f in funcs[:30]:
                    print(" ", f[0] or f[1])

                print("\nEnvironment Variables:")
                for e in sorted(set(envs)):
                    print(" ", e)

            except Exception as e:
                print("Error:", e)

print("\nAnalysis Complete")
