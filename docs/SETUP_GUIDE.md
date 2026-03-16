# Benchmark Configuration & Setup Guide

Diese Anleitung hilft dir dabei, das System nach der Installation von CrucibleMark exakt auf deine Hardware und deine Bedürfnisse (Provider, Module, Modelle) zuzuschneiden.

Sobald du `make install` ausgeführt hast, wird automatisch die Vorlage `benchmark_config.example.yaml` zu `benchmark_config.yaml` kopiert (vorausgesetzt, sie existierte nicht bereits). **Diese Datei (`benchmark_config.yaml`) ist der zentrale Steuerungshebel – sie ist in `.gitignore` eingetragen und wird nicht ins GitHub-Repo hochgeladen, damit deine API-Keys (und individuellen Setups) lokal sicher bleiben.**

Wenn eine Einstellung fehlt oder das System mit "Runtime Errors" crasht, liegt das in der Regel an fehlenden API-Credits, zu kleinen Kontext-Fenstern oder falschen Provider-Aktivierungen. Gehe die folgenden vier Schritte durch.

---

## Schritt 1: Das Hardware-Profil aktivieren

Nicht jede Maschine kann jeden lokalen Benchmark flüssig verarbeiten. In der Sektion `runner_environment` musst du dein primäres Hardware-Profil ("active_profile") festlegen, damit ggf. Warnungen aktiv werden können.

```yaml
runner_environment:
  active_profile: "apple_silicon_m4"  # Ändere dies z. B. zu "nvidia_rtx4090"
```
Nutzt du eine dedizierte Nvidia-Grafikkarte (`nvidia_rtx4090`), stelle den Namen exakt so ein, wie er unter `profiles:` in der YAML-Liste benannt ist.

---

## Schritt 2: Provider & API-Keys hinterlegen

Die Benchmarks nutzen API-Schnittstellen (falls du kommerzielle Modelle wie ChatGPT, Claude oder Gemini benchmarken möchtest). Du musst nicht jeden Provider aktivieren! Schalte einfach die ab, für die du keinen Schlüssel hast.

1. **Provider aktivieren:** Suche in `benchmark_config.yaml` nach der Sektion `providers.commercial`. Setze `enabled: false`, um Provider auszuschalten.
2. **API-Schlüssel:** Hinterlege deine API-Keys **nicht** in dieser YAML-Datei! Trage sie in deine lokale `.bashrc`, `.zshrc` oder besser in eine `.env`-Datei direkt im Hauptverzeichnis des Projekts ein:

```env
# .env Datei im CrucibleMark-Hauptverzeichnis
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIzaSy...
MISTRAL_API_KEY=...
```

---

## Schritt 3: LLM Judge & Meta-Reviewer konfigurieren

Weil CrucibleMark textbasierte Soft-Skill-Vergleiche vornimmt, nutzt das System einen "Meta-Judge" (ein starkes externes Modell, das die Antworten der getesteten Kandidaten auswertet, um Punkte zu vergeben).

In der Sektion `llm_judge:` legst du fest, welcher "Richter" verwendet wird.
Standardmäßig ist hier **Anthropic** (mit `claude-haiku`-Modell) oder **Google** (mit `gemini-pro`) sehr empfehlenswert. Wenn du absolut keine API-Kosten generieren willst, kannst du als Judge auch ein lokales Ollama-Modell angeben (z. B. `ministral-3:14b`), beachte hierbei aber, dass dies enorm viel Zeit und Kontextfenster in Anspruch nimmt.

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

Nicht alle Test-Module sind für jeden Anwendungsfall relevant. Im Feld `modules` am Ende der `benchmark_config.yaml` kannst du exakt festlegen, welche Eigenschaften du evaluieren möchtest.

Für einen schnellen ersten Test empfehle ich, nur Code Quality (`coding`), CLI Benchmark (`cli_benchmark`) oder das logische Verständnis (`reasoning`) auf `enabled: true` zu lassen und Soft-Skills (UX-Writing, Cultural Intelligence etc.) zunächst auszuklammern.

| Disziplin | Typ | Ziel des Moduls |
| :--- | :--- | :--- |
| **`code_quality`** | Hard Skill | Testet sauberes, deterministisches Programmieren und Code-Erklärung. |
| **`cli_benchmark`** | Hard Skill | Prüft den Umgang mit der Kommandozeile und Terminal-Skripten. |
| **`reasoning`** | Metrik | Kognitiver Stresstest (Logikrätsel, Chain-of-Thought, System Error). |
| **`ux_writing`** | Soft Skill | Testet die Erstellung von UI-Texten, Warnungen und benutzerzentrierter Führung. |
| **`documentation_quality`** | Soft Skill | Analysiert, wie gut APIs, README-Dokumente oder Code dokumentiert werden. |
| **`content_transformation`** | Soft Skill | Ermittelt die Adaptionsfähigkeit von Sprache (Tone of Voice und Zielgruppenwechsel). |
| **`cultural_intelligence`** | Metrik | Bewertet interkulturelle Nuancen, Empathie und Übersetzungspräzision im Kontext. |
| **`political_compass`** | Spezial | Ermittelt die ideologische Ausrichtung (bias) des Modells anhand politischer Thesen. |

Ändere einfach je nach Bedarf das Flag:
```yaml
  content_transformation:
    path: "benchmark_modules/content_transformation"
    enabled: false
```

Du kannst jederzeit einzelne Module via CLI-Befehl explizit aufrufen, selbst wenn sie global nicht aktiv sind: `make benchmark MODULE=code_quality`.

Sobald du die Punkte 1 bis 4 nach der Installation justiert hast, bist du bereit, den ersten Testlauf auf deiner Maschine zu evaluieren!
