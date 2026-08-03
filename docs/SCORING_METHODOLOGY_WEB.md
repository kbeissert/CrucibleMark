# Scoring-Methodik (Web-Variante)

**Stand: v5.1.0 · 2026-07-14**

> Diese Datei beschreibt die Scoring-Logik in konzentrierter Form für Endnutzer des Web-Frontends. Die technische Variante mit Implementierungsdetails steht in [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md).

## Grundformel

Der CrucibleMark-Score ist ein gewichteter Durchschnitt über alle bewerteten Module:

```
                 Σ (Modul-Score × Modul-Gewicht)
Total Score = ─────────────────────────────────────
                       Σ Modul-Gewichte
```

Jedes Modul liefert einen individuellen Score (0 bis 100) und hat ein fest definiertes Gewicht, das seine Bedeutung für die Gesamtbewertung bestimmt. Die Modul-Gewichte sind in der Modul-Konfiguration hinterlegt und für alle Modelle identisch.

## Aufteilung in Routine und Reasoning

Der Total Score setzt sich aus zwei Komponenten zusammen:

```
Total Score = Routine Score + Reasoning Score
```

Jedes Modul trägt zu beiden Komponenten bei, basierend auf der Art der gestellten Aufgaben. Routine-Aufgaben testen Anwendungswissen und Formatierung, Reasoning-Aufgaben testen logisches Denken und Problemlösung. Die Gewichtung zwischen Routine und Reasoning variiert pro Modul — ein Reasoning-schweres Modul wie Logical Reasoning trägt fast ausschließlich zur Reasoning-Komponente bei, während ein Modul wie UX Writing überwiegend Routine-Anteile liefert.

## Modulübersicht

| Modul | Gewicht | Fokus |
|---|---|---|
| Code Quality Audit | 1.0 | Routine + Reasoning |
| Content Transformation & Adaption | 1.0 | Routine + Reasoning |
| Cultural Intelligence | 1.0 | Routine + Reasoning |
| Documentation Quality | 1.0 | Routine + Reasoning |
| Logical Reasoning | 1.0 | Reasoning |
| UX Writing & Microcopy | 1.0 | Routine |
| Tool Use & Assistenz | 1.0 | Routine + Reasoning |
| CLI Operations | 0.5 | Routine |

**Summe aller Gewichte: 7.5**

Module mit `enable_scoring: false` (etwa Political Compass) fließen nicht in die Score-Berechnung ein.

## Behandlung unvollständiger Daten

Nicht jedes Modell durchläuft jedes Modul. Die Ursachen wirken sich unterschiedlich auf die Berechnung aus.

### Module ohne Testlauf

**Wenn ein Modell ein Modul nicht getestet hat, obwohl das Modul für es verfügbar wäre** (Status *missing*), wird das erwartete Gewicht dieses Moduls zum Nenner der Formel hinzugefügt — ohne dass ein entsprechender Score in den Zähler eingeht.

Der Total Score sinkt, weil der Nenner wächst, während der Zähler unverändert bleibt. Dieser Mechanismus heißt Coverage-Malus.

```
                 Σ (Scores getesteter Module)
Total Score = ─────────────────────────────────────────────
                 Σ (Gewichte getesteter Module) + Σ (Gewichte fehlender Module)
```

Ein Modell, das das Modul Tool Use & Assistenz nicht durchlaufen hat, erhält keinen Score-Beitrag für dieses Modul. Das Gewicht von 1.0 wird dennoch zum Nenner addiert. Bei einer Gesamtgewichtssumme von 7.5 ergibt sich ein neuer Nenner von 8.5 — der Score sinkt entsprechend.

### Module mit nicht verwertbaren Ergebnissen

**Wenn ein Modell ein Modul durchlaufen hat, aber keine verwertbaren Ergebnisse erzielen konnte** (etwa alle Aufgaben endeten mit Fehler oder Timeout), wird es wie ein nicht getestetes Modul behandelt. Es gilt der Status *missing*: kein Zählerbeitrag, Nenner wird um das erwartete Gewicht erhöht.

Getestet und durchgefallen ist kein Capability-Mangel — das Modell tritt im Ranking mit dem entsprechenden Malus an.

### Module ohne strukturelle Unterstützung

**Wenn ein Modell ein Modul grundlegend nicht unterstützen kann** (Status *incapable*), wird das Modul vollständig aus der Berechnung entfernt — weder Zähler noch Nenner werden beeinflusst.

Beispiel: Ein reines Reasoning-Modell ohne Tool-Use-Funktionalität. Das Modul Tool Use & Assistenz wird sowohl aus dem Zähler als auch aus dem Nenner herausgerechnet. Der Score basiert nur auf den verbleibenden Modulen, ohne Malus.

Die Feststellung, ob ein Modell strukturell unfähig ist, erfolgt über das Capability-Feld in der Model Card (`supports_tool_use`). Ein Modell gilt nur dann als *incapable*, wenn die Model Card dies ausdrücklich bestätigt und das Modell keine Testdaten für das jeweilige Modul aufweist.

### Module in der Einführungsphase

**Wenn ein Modul noch nicht ausreichend getestet wurde** (weniger als 10 % aller Modelle haben Daten dafür, Status *rolling_out*), wird es für alle Modelle aus der Berechnung ausgeschlossen. Das schützt Modelle davor, bestraft zu werden, bevor das Modul breit verfügbar ist.

Sobald das Modul die 10 %-Schwelle erreicht, wird es für alle Modelle aktiviert und der Coverage-Malus greift für Modelle, die es nicht getestet haben.

## Coverage Ratio

Die Coverage Ratio gibt an, wie viel der erwarteten Modul-Abdeckung ein Modell tatsächlich erreicht:

```
                  Σ (Gewichte getesteter Module)
Coverage Ratio = ─────────────────────────────────────────────
                  Σ (Gewichte getesteter + fehlender Module)
```

- **1.00** — das Modell hat alle für es relevanten Module durchlaufen.
- **< 1.00** — das Modell hat Module ausgelassen oder nicht abgeschlossen.

Incapable-Module fließen in diese Kennzahl nicht ein. Ein Modell, das ein Modul strukturell nicht unterstützt, kann dennoch eine Coverage Ratio von 1.00 erreichen.

## Invariante

Für jedes Modell gilt:

```
Routine Score + Reasoning Score = Total Score
```

Diese Invariante ist durch die gemeinsame Nenner-Basis gewährleistet. Abweichungen in der Anzeige sind ausschließlich auf Rundungseffekte zurückzuführen (±0.01).
