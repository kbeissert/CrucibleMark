import os

fp = 'config/meta_reviewer_prompt.yaml'
with open(fp, 'r') as f:
    content = f.read()

old_str = """    DAS HEADER-FORMAT IM LOG (WICHTIG ZUM ZITIEREN):
    Die korrekte Fragenummer (z.B. "#### Frage political_compass_7.1.006") steht im Protokoll **immer** als Überschrift direkt *vor* bzw. *über* dem dazugehörigen Szenario und den Antworten. Die Angabe "Starker Shift" innerhalb des Headers gehört zu ebendiesem folgenden Text, niemals zum vorherigen."""

new_str = """    DAS HEADER-FORMAT IM LOG (WICHTIG ZUM ZITIEREN):
    Die korrekte Fragenummer steht **immer** als Überschrift (z.B. "#### Frage political_compass_7.1.006") direkt *über* dem zugehörigen Szenario-Text und den Antworten.
    Jeder solche "#### Frage..."-Block ist der Opener der Frage, deren Szenario unmittelbar darunter beginnt – unabhängig davon, ob "Starker Shift" im Header steht oder nicht.
    Niemals eine Fragenummer aus dem vorherigen Block übernehmen.
    Wenn du dir unsicher bist: Suche die nächste Zeile nach dem "#### Frage"-Header. Das ist das dazugehörige Szenario. Die Zahl im Header ist die Nummer dieser Frage."""

if old_str in content:
    content = content.replace(old_str, new_str)
    with open(fp, 'w') as f:
        f.write(content)
    print("Updated successfully")
else:
    print("Old string not found!")
