# ============================================================
# .clinerules — Cline Cost & Context Optimization
# Optimiert für Claude Sonnet mit direkter Anthropic API
# ============================================================

# --- KONTEXT-MANAGEMENT (wichtigster Kostenhebel) -----------

## Context Window Schwellenwert
- Überwache aktiv die Kontextauslastung
- Wenn die Kontextauslastung 40% überschreitet: Weise den Nutzer darauf hin
- Wenn die Kontextauslastung 60% überschreitet: Schließe den aktuellen Schritt ab und starte mit `new_task`, inklusive kompakter Zusammenfassung (siehe Übergabe-Format unten)
- Beginne NIEMALS eine neue, komplexe Subtask, wenn der Kontext bereits über 50% liegt

## Übergabe-Format bei Kontextwechsel
Beim Start einer `new_task` immer dieses kompakte Format verwenden:
```
KONTEXT-ÜBERGABE:
- Projekt: [Pfad und Beschreibung]
- Erledigte Schritte: [Liste der abgeschlossenen Aktionen]
- Aktueller Datei-Status: [Welche Dateien wurden verändert und wie]
- Nächste Aktion: [Konkreter nächster Schritt]
- Offene Probleme: [Nur wenn relevant]
```

# --- MODELLWAHL (Kosten reduzieren) -------------------------

## Modell-Routing nach Aufgabentyp
- Für reine Datei-Lesevorgänge (read_file, search_files): bevorzuge claude-haiku-3-5
- Für einfache Textänderungen (< 30 Zeilen): bevorzuge claude-haiku-3-5
- Für komplexes Reasoning, Architekturentscheidungen, neue Features: claude-sonnet-4-5 oder claude-sonnet-4-6
- Für Code-Reviews ganzer Dateien: claude-haiku-3-5 reicht aus

# --- AGENTIC WORKFLOW EFFIZIENZ ----------------------------

## Tool-Nutzung optimieren
- Lese nur die tatsächlich benötigten Dateibereiche (nutze `read_file` mit start/end lines)
- Kombiniere mehrere kleine Änderungen in einem einzigen `write_to_file` statt mehrerer sequenzieller Edits
- Vermeide redundante `list_files`-Aufrufe: Wenn die Struktur bereits bekannt ist, nicht erneut abfragen
- Nutze `search_files` (regex) statt manuelles Lesen vieler Dateien
- Vermeide unnötige `execute_command`-Aufrufe nur zur Verifikation

## Task-Scope klar halten
- Bearbeite genau den beschriebenen Auftrag — keine unrequested Refactorings
- Wenn ein Problem außerhalb des Scopes entdeckt wird: Erwähne es kurz, behebe es aber NICHT eigenständig
- Kein Gold-Plating: Keine zusätzlichen Features, die nicht explizit angefragt wurden

# --- ANTWORTFORMAT (Output-Tokens sparen) ------------------

## Kommunikationsstil
- Halte Erklärungen kompakt: Code > Prosa
- Kein Wiederholen von Aufgabenstellungen am Anfang
- Kein Zusammenfassen erledigter Schritte am Ende jedes Tool-Calls
- Keine redundanten Bestätigungen ("Ich werde jetzt X tun..." → einfach X tun)
- Fehler direkt benennen, ohne ausschweifende Entschuldigungen

## Code-Ausgabe
- Keine ausführlichen Inline-Kommentare in Boilerplate-Code
- Keine vollständigen Datei-Outputs, wenn nur ein kleiner Abschnitt geändert wurde (nutze targeted edits)

# --- PROJEKTSPEZIFISCHE REGELN ----------------------------

## Bei Web-Projekten (11ty, HTML/CSS/JS)
- Nutze SCSS-Variablen und vorhandene Design-Tokens, nicht hardcodierte Werte
- Bootstrap-Klassen bevorzugen vor Custom-CSS, wo es passt
- Accessibility (WCAG 2.2 AA) ist non-negotiable

## Bei Python/AI-Projekten (CrucibleMark etc.)
- Bestehende Pytest-Fixtures wiederverwenden
- Konfiguration über Config-Files, nicht hardcodiert
- Type hints in neuen Funktionen verwenden

## Bei API-Integrationen
- API Keys niemals in Code oder Logs — immer .env / Umgebungsvariablen
- Rate-Limiting und Error-Handling von Anfang an berücksichtigen

# ============================================================
