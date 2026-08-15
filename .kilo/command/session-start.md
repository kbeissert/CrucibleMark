---
description: >-
  CrucibleMark Session-Kontext laden und Projektstand zusammenfassen.
  Liest README, Memory Bank und Config — nur Lesen, keine Änderungen.
  Mit Argument "compact": verdichtete 15-Punkte-Übersicht statt Session-Bootstrap.
---

Du bist Senior Developer für das CrucibleMark-Projekt.

## Modus-Auswahl

- **Default (Session-Bootstrap):** Vollständiger Session-Start wie unten beschrieben.
- **Argument `compact`** (`$ARGUMENTS` enthält "compact"): Verdichtete Übersicht —
  zusätzlich `PROJECT_STATUS.md` lesen, dann max. 15 Bulletpoints in drei
  Abschnitten (Architektur / Bugs / Todos). Verwerfe Versionsnummern-Rauschen,
  Testzähler, Zeilen-Diffs und Changelog-Zitate. Nur architektonische
  Entscheidungen (SSoT-Prinzipien, Card-First, Tiers), kritische Bugs mit
  Ursache + Fix sowie offene Todos / Roadmap-Punkte.

## Ablauf (Default-Modus)

Lies zunächst **ausschließlich** die folgenden Dateien — in dieser Reihenfolge —
und bestätige den aktuellen Projektstand:

1. [README.md](../README.md)
2. [memory-bank/progress.md](../memory-bank/progress.md)
3. [memory-bank/activeContext.md](../memory-bank/activeContext.md)
4. [benchmark_config.yaml](../benchmark_config.yaml)

Falls eine der Dateien nicht existiert oder nicht lesbar ist, brich den Vorgang ab, melde welche Datei fehlt und frage nach dem korrekten Pfad, bevor du eine Zusammenfassung erstellst.

Führe **keine Änderungen** durch.

Fasse danach präzise zusammen: maximal 3–5 Bullet-Points pro Abschnitt, jeweils 1–2 Sätze. Falls die gelesenen Dateien sich widersprechen (z.B. unterschiedliche "nächste Tasks" in progress.md vs. activeContext.md), kennzeichne den Widerspruch explizit unter "Bekannte Baustellen" und nenne beide Quellen (Dateiname + kurzer Auszug).

- **Zuletzt implementiert:** Was wurde in der letzten Session abgeschlossen?
- **Nächster offener Task:** Was ist der konkret nächste Schritt?
- **Bekannte Baustellen:** Offene Risiken oder blockierende Issues? Bei Widersprüchen: Quellen angeben.

Warte auf meine ausdrückliche Bestätigung, bevor du irgendetwas änderst.
