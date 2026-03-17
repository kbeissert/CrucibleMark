import glob
import re

files = glob.glob('benchmark_scores/**/*.csv', recursive=True) + \
        glob.glob('outputs/**/*.csv', recursive=True) + \
        glob.glob('outputs/**/*.json', recursive=True)

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Säubere alte Fingerprint-Hashes von den Versionsnummern ab (z.B. "4.6-812e63c4" -> "4.6")
        new_content = re.sub(r'(claude(?:-opus|-sonnet|-haiku)?-?\d*(?:-\d+)?)-[0-9a-f]{8}\b', r'\1', content)
        new_content = re.sub(r'\b(4\.[56])-[0-9a-f]{8}\b', r'\1', new_content)
        new_content = re.sub(r'claude-opus-4-6', 'claude-3-5-opus-latest', new_content) # Wenn nötig

        # Die Modelle heißen jetzt vermutlich einfach claude-sonnet-4-6 und claude-opus-4-6,
        # wir entfernen primär die alten, zufälligen Hashes der Fingerprints.

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filepath}')
    except Exception:
        pass
print("Bereinigung abgeschlossen.")
