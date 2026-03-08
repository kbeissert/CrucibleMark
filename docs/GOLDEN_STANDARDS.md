# Golden Standard Methodology

**Zielgruppe:** Alle, die verstehen wollen, wie CrucibleMark Modelle vergleichbar macht.

**Was Sie hier finden:**

- Das "Single Source of Truth" Prinzip
- Update-Strategie (Trial & Commit)
- Interpretation der Performance Ratio
- Wann und wie Golden Standard aktualisiert wird

______________________________________________________________________

## ⚖️ Das Gesetz der Referenz

CrucibleMark unterscheidet sich von anderen Benchmarks durch eine fundamentale Entscheidung:

> **Wir messen nicht gegen theoretische Perfektion, sondern gegen die bestmögliche Realität.**

Ein **Score von 100%** bedeutet nicht "Fehlerfrei", sondern **"Auf Augenhöhe mit unserem besten kommerziellen Modell"**.

______________________________________________________________________

## 📌 Das "Single Source of Truth" Prinzip

In `benchmark_config.yaml` ist genau **ein** Golden Standard definiert. Es gibt keine multiplen Referenzen.

```yaml
golden_standard:
  provider: "anthropic"            # Fixer Provider
  model: "claude-sonnet-4-5-20250929" # Das Referenz-Modell
  description: "Die absolute Messlatte für alle lokalen Tests."
```

Alle lokalen Modelle (Llama, Gemma, Qwen) werden relativ zu diesem einen Ankerpunkt bewertet.

**Ausnahme:** Der **Political Compass** ist *kein* Teil des Golden Standards, da Bias-Messungen keine Leistung gegen ein Ideal darstellen („Neutralität“ ist kein absoluter Benchmark-Score in der gleichen Weise wie Code-Qualität). Der Golden Standard Prozess überspringt dieses Modul daher automatisch.

______________________________________________________________________

## 🛠️ Update-Strategie: "Trial & Commit"

Um wissenschaftliche Vergleichbarkeit zu gewährleisten, darf sich der Maßstab nicht schleichend verändern.

**Regel:** Der Golden Standard aktualisiert sich **NIEMALS automatisch**.

### Der Prozess

#### 1. Benchmarking (Read-Only)

Wenn Sie `make benchmark-single MODEL=mistral-large-latest` ausführen, wird Mistral Large **wie ein normales Modell behandelt**:

- Seine Leistung wird gemessen
- Sie wird gegen den *alten* Golden Standard verglichen
- **Ratio > 100%?** Das bedeutet, Mistral Large hat sich verbessert (oder Scoring-Logik wurde gefixt)
- Die Referenzdatei bleibt unangetastet

______________________________________________________________________

#### 2. Validierung (Audit)

Als Engineer prüfen Sie die Ergebnisse:

- Sind 105% plausibel?
- War das Scoring vorher fehlerhaft?
- Haben sich die Assets geändert?

______________________________________________________________________

#### 3. Update (Write Action)

Erst wenn Sie sicher sind, dass der neue Zustand der neue "Nullpunkt" sein soll:

```bash
make generate-golden
```

**Was passiert:**

- Überschreibt `benchmark_scores/golden_standard_benchmark.csv`
- Ab jetzt ist dies das neue "100%"
- **Pflicht:** Eintrag im `GOLDEN_STANDARD_CHANGELOG.md`

**Beispiel-Eintrag:**

```markdown
## v2.2.0 (2026-02-15)

- **Model:** mistral-large-latest
- **Reasoning Score:** 89.20 (vorher: 87.40)
- **Changes:**
  - Added Reasoning 5E-1 (Constraint Propagation)
  - Fixed scoring bug in 5C-001 (Scheduling Paradox)
- **Note:** +1.8% improvement reflects bugfix, not model change
```

______________________________________________________________________

## 📊 Interpretation der Metrics

### Performance Ratio

Die wichtigste Metrik im Leaderboard ist die **Ratio** zum Golden Standard.

```
Ratio = (Model Score / Golden Standard Score) × 100
```

**Bedeutung:**

| Ratio | Interpretation | Beispiel |
|-------|---------------|----------|
| **100%** | Identisch mit Referenz | Mistral Large (per Definition) |
| **< 100%** | Unter Referenz (Normalfall) | Qwen 2.5 14B @ 92% |
| **> 100%** | Besser als Referenz | **Achtung: Prüfen!** |

______________________________________________________________________

### Ratio > 100% – Was tun?

**Zwei mögliche Ursachen:**

#### Fall A: Modell-Verbesserung

Das Modell ist tatsächlich besser als der alte Standard.

**Beispiel:**

- DeepSeek R1 @ 105% (neues "Thinking Model")
- Golden Standard: Mistral Large (Gen 1 Modell)

**Action:** Erwägen Sie ein Update des Standards (oder akzeptieren Sie, dass lokale Modelle die Referenz überholen können).

______________________________________________________________________

#### Fall B: Veralteter Standard

Der Golden Standard ist zu alt (z.B. vor einem Bugfix im Scoring).

**Beispiel:**

- Alle Modelle zeigen plötzlich >100%
- Grund: Scoring-Fehler wurde behoben

**Action:** **Sofort** `make generate-golden` ausführen, um Konsistenz wiederherzustellen.

______________________________________________________________________

## 🎯 Warum Mistral Large?

Wir nutzen Mistral Large als Referenz, weil es:

1. **Exzellente Reasoning-Fähigkeiten** besitzt (vergleichbar mit GPT-4)
1. Ein **europäisches Modell** ist (GDPR/DSGVO Compliance Fokus)
1. **Offen dokumentiert** ist (Transparency)
1. **Stabil** ist (keine wöchentlichen Breaking Changes wie GPT-4)

______________________________________________________________________

## ⚠️ Häufige Fehler

### ❌ Golden Standard manuell editieren

**Falsch:**

```bash
# CSV direkt bearbeiten
nano benchmark_scores/golden_standard_benchmark.csv
```

**Warum schlecht:**

- Inkonsistenzen zwischen CSV und JSON-Referenzen
- Keine Versionierung (Changelog fehlt)
- Nicht reproduzierbar

**Richtig:**

```bash
make generate-golden
# Dann: GOLDEN_STANDARD_CHANGELOG.md aktualisieren
```

______________________________________________________________________

### ❌ Mehrere Golden Standards parallel

**Falsch:**

```yaml
golden_standard:
  models:
    - mistral-large
    - gpt-4
```

**Warum schlecht:**

- Verwässert die Vergleichbarkeit
- Welcher Standard gilt für welches Modul?
- Unterschiedliche Modelle haben unterschiedliche Bias

**Richtig:** Ein Standard für alles. Punkt.

______________________________________________________________________

## 🔄 Wann Golden Standard aktualisieren?

### Szenarien für Update:

✅ **Ja, updaten:**

- Neue Assets hinzugefügt (Module erweitert)
- Mistral Large erhält Major-Update (z.B. neue Version)
- Scoring-Logik wurde gefixt (Bug-Behebung)
- Konsistent >100% Ratios bei vielen Modellen

❌ **Nein, nicht updaten:**

- Ein einzelnes Modell zeigt >100% (könnte Ausreißer sein)
- Mistral Large zeigt minimal bessere Scores (~2-3%)
- Sie "mögen" ein anderes Modell lieber

______________________________________________________________________

## 📦 Pre-Generated Standards

Dieses Repository enthält **vorgenerierte Golden Standards** (basierend auf Mistral Large v2.1.0, Stand: Jan 2026).

Sie können **sofort loslegen**, ohne API-Key!

### Wenn Sie einen neuen Standard etablieren wollen:

1. Update `benchmark_config.yaml` → Golden Standard Modell ändern
1. Run `make generate-golden`
1. Commit die neuen JSON-Files in `golden_standards/`
1. Update `GOLDEN_STANDARD_CHANGELOG.md`

______________________________________________________________________

## 🔗 Verwandte Dokumentation

- **GOLDEN_STANDARD_CHANGELOG.md** – Historie aller Updates
- **ARCHITECTURE.md** – Wie Golden Standard Comparison technisch funktioniert
- **MODEL_CLASSIFICATION.md** – RCI & Generation-Klassifizierung

______________________________________________________________________

## 📜 Lizenz-Hinweis

Die Golden Standards (JSON-Dateien) sind Teil von CrucibleMark und unterliegen der **Apache License 2.0**.

Sie dürfen:

- ✅ Die Referenzen nutzen (kommerziell & privat)
- ✅ Eigene Standards erstellen und teilen
- ✅ Die Methodik adaptieren

Sie müssen:

- ✅ Attribution beibehalten (siehe LICENSE)
- ✅ Änderungen dokumentieren (NOTICE-Datei)

**Siehe:** `LICENSE` und `TRADEMARK.md` für Details.

______________________________________________________________________

**Dokumenten-Version:** 1.0.0 (Rewrite Feb 2026)\
**Kompatibel mit:** CrucibleMark v0.9.5+\
**Letzte Golden Standard Version:** v2.1.0 (30. Jan 2026)
