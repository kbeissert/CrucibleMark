# Golden Standard Methodik

## ⚖️ Das Gesetz der Referenz

CrucibleMark unterscheidet sich von anderen Benchmarks durch eine fundamentale Entscheidung:
**Wir messen nicht gegen die theoretische Perfektion, sondern gegen die bestmögliche Realität.**

Ein "Score von 100%" bedeutet nicht "Fehlerfrei", sondern "Auf Augenhöhe mit unserem besten kommerziellen Modell".

### 1. Das "Single Source of Truth" Prinzip
In [`benchmark_config.yaml`](../benchmark_config.yaml) ist genau **ein** Golden Standard definiert. Es gibt keine multiplen Referenzen.

```yaml
golden_standard:
  provider: "mistral"              # Fixer Provider
  model: "mistral-large-latest"   # Das Referenz-Modell (123B)
  description: "Die absolute Messlatte für alle lokalen Tests."
```

Alle lokalen Modelle (Llama, Gemma, Ministral) werden relativ zu diesem einen Ankerpunkt bewertet.

---

## 🛠️ Update-Strategie: "Trial & Commit"

Um wissenschaftliche Vergleichbarkeit zu gewährleisten, darf sich der Maßstab nicht schleichend verändern.
Deshalb gilt: **Der Golden Standard aktualisiert sich NIEMALS automatisch.**

### Der Prozess

1.  **Benchmarking (Read-Only):**
    Wenn du `make benchmark-single MODEL=mistral-large-latest` ausführst, wird Mistral Large **wie ein normales Modell behandelt**.
    *   Seine Leistung wird gemessen.
    *   Sie wird gegen den *alten* Golden Standard in der CSV verglichen.
    *   **Ratio > 100%?** Das bedeutet, Mistral Large hat sich verbessert (oder wir haben die Scoring-Logik gefixt).
    *   Die Referenzdatei bleibt unangetastet.

2.  **Validierung (Audit):**
    Als Engineer prüfst du die Ergebnisse. Sind 105% plausibel? War das Scoring bugged?

3.  **Update (Write Action):**
    Erst wenn du sicher bist, dass der neue Zustand der neue "Nullpunkt" sein soll, führst du aus:
    ```bash
    make generate-golden
    make generate-golden-new # Erzwingt Neuberechnung aller Assets
    ```
    *   Dies überschreibt `benchmark_scores/golden_standard_benchmark.csv`.
    *   Ab jetzt ist dies das neue "100%".
    *   Ein Eintrag im `GOLDEN_STANDARD_CHANGELOG.md` ist obligatorisch.

---

## 📊 Interpretation der Metrics

### Performance Ratio
Die wichtigste Metrik im Leaderboard ist die **Ratio** zum Golden Standard.

*   **100%**: Das Modell ist exakt so gut wie die Referenz (Mistral Large) zum Zeitpunkt des letzten Snapshots.
*   **< 100%**: Der Normalfall für lokale Modelle (Quantized, weniger Parameter).
*   **> 100%**:
    *   **Fall A (Modell-Update):** Das Modell ist tatsächlich besser als der alte Standard.
    *   **Fall B (Veralteter Standard):** Der Golden Standard ist zu alt (z.B. vor einem Bugfix im Scoring). -> **Handlungsempfehlung:** `make generate-golden`.

### Warum Mistral Large?
Wir nutzen Mistral Large als Referenz, weil es:
1.  Exzellente Reasoning-Fähigkeiten besitzt (vergleichbar mit GPT-4).
2.  Ein europäisches Modell ist (GDPR/DSGVO Compliance Fokus).
3.  Eine offene Gewichtung hat (Transparency).

---

## ⚠️ Architektur-Hinweis für Entwickler

Der Code in `scripts/run_commercial_benchmark.py` respektiert dieses Gesetz strikt:

```python
# Pseudo-Code Logik
if mode == "test":
    calc_score()
    print("Score: 87%")
    # KEIN Save in golden_standard_benchmark.csv!

if mode == "golden_standard":
    calc_score()
    save_to_csv("golden_standard_benchmark.csv")
    print("Neuer Standard gesetzt.")
```

Dies verhindert "Drift". Ein Benchmark ist nur nützlich, wenn das Lineal, mit dem man misst, nicht während der Messung seine Länge ändert.


