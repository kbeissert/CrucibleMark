# Konfiguration & Setup-Anleitung

**Zielgruppe:** Alle, die CrucibleMark erstmalig einrichten oder die zentrale Konfiguration anpassen wollen.
**Inhalt:** Hardware-Profil, Provider & API-Keys, LLM-Judge-Konfiguration, Modul-Auswahl

> **Voraussetzung:** Installation abgeschlossen (`make install` ausgeführt).

Diese Anleitung beschreibt, wie CrucibleMark nach der Installation exakt auf die eigene Hardware und spezifische Anforderungen (Provider, Module, Modelle) zugeschnitten wird.

Nach `make install` kopiert das System die Vorlage `benchmark_config.example.yaml` automatisch zu `benchmark_config.yaml` – vorausgesetzt, sie existierte noch nicht. **Diese Datei ist der zentrale Steuerungshebel. Sie steht in `.gitignore` und landet nicht im Repository, damit API-Keys lokal sicher bleiben.**

Wenn eine Einstellung fehlt oder das System mit „Runtime Errors" abstürzt, liegt das meist an fehlenden API-Credits, zu kleinen Kontext-Fenstern oder falschen Provider-Aktivierungen. Gehe die folgenden vier Schritte durch.

---

## Schritt 1: Das Hardware-Profil aktivieren

Nicht jede Maschine kann jeden lokalen Benchmark flüssig verarbeiten. In der Sektion `runner_environment` wird das primäre Hardware-Profil (`active_profile`) festgelegt.

```yaml
runner_environment:
  active_profile: "apple_silicon_m4"  # Ändere dies z. B. zu "nvidia_rtx4090"
```

Mit einer dedizierten Nvidia-Grafikkarte (`nvidia_rtx4090`) trägt man den Namen exakt so ein, wie er unter `profiles:` in der YAML-Liste steht.

---

## Schritt 2: Provider & API-Keys hinterlegen

Alle Provider und ihre Kategorien (Commercial, Open-Weights Cloud, Local) sind dynamisch als Single Source of Truth in der `benchmark_config.yaml` hinterlegt (unter der Sektion `providers`). Wer einen neuen Anbieter nutzen möchte (z. B. `together_ai`), fügt diesen nur dort zur entsprechenden Kategorie hinzu. So werden die Provider auch fehlerfrei im Leaderboard klassifiziert (Details unter [MODEL_CLASSIFICATION.md](MODEL_CLASSIFICATION.md)).

Die Benchmarks nutzen API-Schnittstellen für kommerzielle Modelle oder Cloud-gehostete Open-Weights-Modelle. Nicht jeder Provider muss aktiviert werden.

1. **Provider einrichten:** Die aktuellen Listen finden sich in `benchmark_config.yaml` unter `providers.commercial`, `providers.open_weights_cloud` und `providers.local`. Die Listen werden nach Bedarf angepasst.
2. **API-Schlüssel:** API-Keys werden **nicht** in der YAML-Datei hinterlegt. Sie werden direkt in eine `.env`-Datei im Hauptverzeichnis eingetragen:

```env
# .env Datei im CrucibleMark-Hauptverzeichnis
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIzaSy...
MISTRAL_API_KEY=...
```

---

## Schritt 3: LLM Judge & Meta-Reviewer konfigurieren

Weil CrucibleMark textbasierte Soft-Skill-Vergleiche vornimmt, nutzt das System einen „Meta-Judge" – ein starkes externes Modell, das die Antworten der Kandidaten auswertet und Punkte vergibt.

In der Sektion `llm_judge:` wird festgelegt, welcher Richter verwendet wird. **Anthropic** (mit `claude-haiku`-Modell) oder **Google** (mit `gemini-pro`) sind sehr empfehlenswert. Wer keinerlei API-Kosten generieren will, kann auch ein lokales Ollama-Modell als Judge angeben (z. B. `ministral-3:14b`). Das beansprucht jedoch erheblich mehr Zeit und Kontextfenster.

```yaml
llm_judge:
  enabled: true
  provider:
    name: anthropic
    model: claude-haiku-4-5-20251001
    max_tokens: 8192
```

---

## Schritt 4: Benchmarking-Module auswählen

Nicht alle Test-Module sind für jeden Anwendungsfall relevant. Im Feld `modules` am Ende der `benchmark_config.yaml` wird exakt festgelegt, welche Eigenschaften evaluiert werden sollen.

Für einen schnellen ersten Test empfiehlt sich, nur Code Quality (`coding`), CLI Benchmark (`cli_benchmark`) oder logisches Verständnis (`reasoning`) auf `enabled: true` zu lassen. Soft-Skills (UX-Writing, Cultural Intelligence u. a.) lassen sich zunächst ausklammern.

| Disziplin | Typ | Ziel des Moduls |
| :--- | :--- | :--- |
| **`code_quality`** | Hard Skill | Testet sauberes, deterministisches Programmieren und Code-Erklärung. |
| **`cli_benchmark`** | Hard Skill | Prüft den Umgang mit der Kommandozeile und Terminal-Skripten. |
| **`reasoning`** | Metrik | Kognitiver Stresstest (Logikrätsel, Chain-of-Thought, Systemfehler). |
| **`ux_writing`** | Soft Skill | Testet die Erstellung von UI-Texten, Warnungen und nutzerzentrierter Führung. |
| **`documentation_quality`** | Soft Skill | Analysiert, wie gut APIs, README-Dokumente oder Code dokumentiert werden. |
| **`content_transformation`** | Soft Skill | Ermittelt die Adaptionsfähigkeit von Sprache (Tone of Voice und Zielgruppenwechsel). |
| **`cultural_intelligence`** | Metrik | Bewertet interkulturelle Nuancen, Empathie und Übersetzungspräzision im Kontext. |
| **`political_compass`** | Spezial | Ermittelt die ideologische Ausrichtung (Bias) des Modells anhand politischer Thesen. |

```yaml
  content_transformation:
    path: "benchmark_modules/content_transformation"
    enabled: false
```

Einzelne Module lassen sich auch dann via CLI aufrufen, wenn sie global deaktiviert sind: `make benchmark MODULE=code_quality`.

Nach diesen vier Schritten ist die Konfiguration abgeschlossen und der erste Testlauf kann starten.
