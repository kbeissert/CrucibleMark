# Cultural Intelligence Module (v0.9.5)

## 🎯 Über dieses Modul
Das **Cultural Intelligence Modul** testet die Fähigkeit von LLMs, sich an spezifische kulturelle und sprachliche Nuancen im DACH-Raum (Deutschland, Österreich, Schweiz) anzupassen. Anders als reine Übersetzungsbenchmarks, prüft dieses Modul "Cultural Fit", "Register-Wechsel" und "Soziolekte".

Es geht nicht nur darum, *korrektes* Deutsch zu schreiben, sondern das *passende* Deutsch für den Kontext (z.B. IT-Fachsprache, inklusive HR-Sprache, Berliner Agentur-Slang).

---

## 🏗 Architektur
Dieses Modul weicht von der Standard-Logik von CrucibleMark ab. Anstatt rein LLM-basierte Evaluation (LLM-as-a-judge) zu nutzen, verwendet es **deterministische Python-Logik (`test.py`)**, um präzise und reproduzierbare Scores zu garantieren.

- **Assets (`assets/*.yaml`)**: Definieren die Prompts und Metadaten.
- **Logik (`test.py`)**: Enthält pro Asset eine eigene `_evaluate_...` Methode mit Hardcoded-Regeln (Regex, Keyword-Listen).

---

## 🔎 Wie funktioniert der Benchmark-Vergleich?

Anders als bei anderen Modulen, wo oft ein "Golden Standard" (eine Referenzantwort) semantisch oder durch eine Jury-KI mit der Modell-Antwort verglichen wird, nutzt dieses Modul **harte, programmatische Regeln**.

Der Prozess läuft so ab:

1.  **Generierung**: Das Modell erhält den Prompt aus dem Asset (z.B. *"Übersetze 'Project went south' als deutsches Idiom"*).
2.  **Analyse**: Der Antwort-Text des Modells wird vom Skript (`test.py`) analysiert.
3.  **Mustererkennung (Pattern Matching)**: Das Skript sucht im Text nach **vordefinierten Schlüsselwörtern** und **Mustern**:
    *   ✅ **Positive Matches**: Sind gewünschte Begriffe enthalten? (z.B. *"ging schief"*, *"in die Hose"*)
    *   🚫 **Negative Matches**: Sind verbotene Begriffe enthalten? (z.B. *"ging nach Süden"*, *"Craftsman"*, *"Sie"*)
4.  **Score-Berechnung**: Der Score ergibt sich rein mathematisch aus der Anzahl der Treffer (z.B: 8 von 10 Begriffen korrekt = 80%).

**Vorteil:** Das Ergebnis ist zu 100% objektiv und reproduzierbar. Es gibt keinen Interpretationsspielraum einer "Jury-KI".

---

## 🧪 Benchmark Assets & Scoring Logik

### 1. Asset 6A: German Tech Localization (Tech-Speak)
**Ziel:** "Denglisch" korrekt anwenden. Fachbegriffe wie "Push", "Commit", "Repo" sollen im Deutschen *nicht* übersetzt werden (Code-Switching).
- **Methode:** `_evaluate_tech_localization`
- **Max Score:** 10 Punkte (10 Begriffe)
- **Logik:**
  - Positive Liste: "Push", "Commit", "Repo", "Branch", etc. müssen enthalten sein.
  - Negative Liste: Übersetzungen wie "Drücken", "Verpflichten", "Zweig" geben Punktabzug.

### 2. Asset 6B: Inclusive Job Ad (Diversity & Bias)
**Ziel:** Schreiben einer inklusiven Stellenanzeige. Entfernen von "Bro-Speak" und toxischer Maskulinität.
- **Methode:** `_evaluate_inclusive_job_ad`
- **Max Score:** 10 Punkte (10 Checks)
- **Logik:**
  - **Toxic Filter**: Entfernt Begriffe wie "Ninja", "Rockstar", "Dominate", "Manpower".
  - **Gender Awareness**: Prüft auf Gendering (*in, :in, m/w/d) und vermeidet generisches Maskulinum ("Der Handwerker").

### 3. Asset 6C: Berlin Agency Vibe (Buzzword Cleaner)
**Ziel:** Reduktion von Corporate-Bullshit hin zu authentischer, direkter Sprache ("Berliner Schnauze").
- **Methode:** `_evaluate_agency_vibe`
- **Max Score:** 9 Punkte (11.1% pro bereinigtem Buzzword)
- **Logik:**
  - Prüft, ob 9 spezifische Buzzword-Kategorien (Synergy, Ecosystem, Paradigm, Deep-Dive, etc.) aus dem Text entfernt wurden.
  - **v8 Update**: "Lösung" (Solution) und "Ganzheitlich" (Holistic) wurden aus der Blacklist entfernt, da sie valides Deutsch sind.

### 4. Asset 6D: Formal vs. Informal (Register Switch)
**Ziel:** Umschreiben einer formellen Bank-E-Mail ("Sie") in eine casual Start-up Ansprache ("Du").
- **Methode:** `_evaluate_formal_informal`
- **Max Score:** 10 Punkte (Hardened v8.1)
- **Logik:**
  - **Strict 'Du' Check**: Zählt absolute Vorkommen von "du", "dir", "dein". Muss mind. 2x vorkommen.
  - **Absence of 'Sie'**: Bestraft jedes verbliebene förmliche "Sie" oder "Ihnen".
  - **Vocab Swap**: Prüft spezifische Ersetzungen (z.B. "herunterladen" -> "runterladen", "bezüglich" -> "wegen").

### 5. Asset 6E: German Idioms (Idiomatische Übersetzung)
**Ziel:** Korrekte Übertragung englischer Redewendungen ins Deutsche (keine wörtliche Übersetzung).
- **Methode:** `_evaluate_german_idioms`
- **Max Score:** 5 Idiome x 2 Punkte = 10 Punkte (v8.1 Expanded)
- **Logik:**
  - Prüft 5 Idiome: "went south", "outside the box", "game plan", "touch base", "ball rolling".
  - **Varianz**: Akzeptiert eine breite Liste an gültigen deutschen Entsprechungen (z.B. für "went south": "ging schief", "in die Hose", "missglückte").
  - Bestraft wörtliche Falschübersetzungen (z.B. "ging nach Süden").

---

## 🔧 Erweiterung des Moduls (Developer Guide)
Wenn du dieses Modul in Zukunft erweitern möchtest (z.B. "Schwäbischer Dialekt" oder "Behördendeutsch"):

1.  **Asset erstellen**: Lege `asset_6f_neues_thema.yaml` an.
2.  **Test-Klasse erweitern**: Öffne `test.py`.
    - Füge eine Methode `_evaluate_neues_thema(text)` hinzu.
    - Definiere eine `score`-Variable und eine `feedback`-Liste.
    - Implementiere Regex- oder Keyword-Checks.
3.  **Dispatcher Update**: Füge in der `score_response`-Methode (ca. Zeile 60) eine neue `elif asset_id == "cultural_intel_006":`-Weiche hinzu.

---

## 📊 Benchmark-Interpretation
- **0-30%**: Modell hat kein Verständnis für kulturellen Kontext / übersetzt stur wörtlich.
- **40-70%**: Modell versteht die Aufgabe, macht aber Inkonsistenz-Fehler (z.B. mischt "Du" und "Sie").
- **80-100%**: Modell besitzt hohe kulturelle Fluency ("Native Level") und versteht Nuancen.
