# New Session: CrucibleMark Context Load

Du bist Senior Developer für CrucibleMark.
Lies zunächst NUR die folgenden Dateien und bestätige den Projektstand:

1. README.md
2. memory-bank/progress.md
3. memory-bank/activeContext.md
4. benchmark_config.yaml

Führe KEINE Änderungen durch. Fasse zusammen:
- Was wurde zuletzt implementiert?
- Was ist der nächste offene Task?
- Welche bekannten Baustellen existieren?

Warte auf meine Bestätigung bevor du irgendwas änderst.

---
## SESSION COMMIT

Aktualisiere das Projekt-Wissen. Qualität vor Vollständigkeit –
lieber nichts schreiben als etwas Falsches oder Triviales.

### Filter (vor dem Schreiben prüfen)
Nur dokumentieren wenn:
- Es ein nicht-offensichtliches Problem war, das Zeit gekostet hat
- Es eine Entscheidung ist, die man in 3 Monaten nicht mehr rekonstruieren kann
- Es den nächsten Schritt direkt beeinflusst

Nicht dokumentieren:
- Standard-Python/Framework-Verhalten
- Dinge, die bereits im Code selbst klar ersichtlich sind
- Einzel-Fixes ohne Wiederholungsrisiko

---

### 1. AGENTS.md — Fallstricke & Verbote
Nur ergänzen wenn ein neuer, nicht-offensichtlicher Fallstrick aufgetreten ist,
der noch nicht dokumentiert ist. Max. 1–2 Sätze. Ein Satz pro Eintrag.
Kein Eintrag? Nichts schreiben.

### 2. memory-bank/systemPatterns.md — Architekturentscheidungen
Nur ergänzen wenn heute eine neue Architekturentscheidung getroffen wurde
oder ein bestehendes Pattern sich als falsch erwiesen hat.
Kein struktureller Wandel? Nichts schreiben.

### 3. memory-bank/activeContext.md — Aktueller Stand
Vollständig überschreiben mit:
- Abgeschlossen: [was – max. 2 Zeilen]
- Nächster Schritt: [konkret, ein Satz]
- Offen/Risiko: [was – oder "keine"]

### 4. memory-bank/progress.md — Nur aktueller Zustand
Laufende Tasks: Status aktualisieren ([ ] → [DONE] oder Fortschritt ergänzen).
Abgeschlossene Meilensteine: Nicht neu anlegen – nur bestehende als [DONE] markieren.
Neue Tasks nur ergänzen wenn sie den nächsten logischen Schritt darstellen.
Kein Changelog, keine Erklärungen – nur Status.

### 5. memory-bank/techContext.md — Stack & Tools
Nur anfassen bei neuer Dependency, geändertem Build-Befehl oder neuem Tool.
Sonst: nicht ändern.

Bestätige mit: "Memory updated ✓"

---

