with open("docs/USER_GUIDE.md", "r") as f:
    text = f.read()

OLD = """Um den Modus zu aktivieren:
```bash
make benchmark-audit
```"""

NEW = """Der Audit-Modus ist **standardmäßig aktiv**. Wenn du die Audit-Logs überspringen möchtest, kannst du die Protokollierung beim Benchmark-Start via `SILENT=1` Flag deaktivieren:
```bash
make benchmark MODEL=modell_name SILENT=1
```"""

if OLD in text:
    text = text.replace(OLD, NEW)
    with open("docs/USER_GUIDE.md", "w") as f:
        f.write(text)
    print("Replaced!")
else:
    print("Not found.")

