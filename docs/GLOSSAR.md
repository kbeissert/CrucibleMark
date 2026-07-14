# Glossar

**Stand: v5.1.0 · 2026-07-14**

Dieses Glossar sammelt projektinterne Begriffe, die in der Dokumentation wiederkehren. Es dient als Anker für Leser, die neu in das Thema einsteigen, und als Referenz für alle, die gelegentlich die exakte Bedeutung nachschlagen wollen.

Die Begriffe sind nach Themenfeld gruppiert: Scoring und Coverage, Model-Identität, Hardware und Deployment, Bewertungs-Pipelines.

---

## Scoring und Coverage

**Total Score** — Aggregierter Gesamtscore über alle bewerteten Module, normalisiert auf 0 bis 100. Berechnet als gewichteter Durchschnitt der Modul-Scores mit `module_weight` als Gewicht.

**Routine Score** — Komponente des Total Scores für Aufgaben, die Anwendungswissen und Formatierung testen.

**Reasoning Score** — Komponente des Total Scores für Aufgaben, die logisches Denken und Problemlösung testen.

**Invariante** — Die Eigenschaft `Routine Score + Reasoning Score = Total Score`. Sie gilt für jedes Modell mit einer Toleranz von ±0.01 (Rundung). Verletzungen deuten auf einen Bug in der Scoring-Pipeline hin.

**module_weight** — Konfigurierbares Gewicht eines Moduls im Total Score (Standard `1.0`, CLI-Modul `0.5` als Supplement). Definiert in der jeweiligen Modul-`config.yaml` unter `integration.leaderboard.module_weight`.

**Coverage Ratio** — Verhältnis der getesteten Modul-Gewichte zur Summe aus getesteten und fehlenden Modul-Gewichten. `1.00` bedeutet vollständige Abdeckung der für das Modell relevanten Module; Werte unter 1.00 kennzeichnen Lücken.

**Coverage-Malus** — Mechanismus, der ein nicht getestetes Modul in den Nenner der Score-Formel einfließen lässt, ohne den Zähler zu füllen. Senkt den Total Score proportional zur Lücke.

**Status-Klassen** (Coverage-Klassifikation eines Moduls pro Modell):

| Status | Bedeutung |
|---|---|
| `present` | Modul wurde getestet und hat einen Score |
| `missing` | Modul wurde nicht getestet, obwohl das Modell dafür geeignet wäre (löst Coverage-Malus aus) |
| `unknown` | Fähigkeit des Modells ist nicht abschließend geklärt (Malus mit WARNING) |
| `incapable` | Modell kann das Modul strukturell nicht (exempt: weder Zähler noch Nenner) |
| `rolling_out` | Modul ist in der Einführungsphase (weniger als 10 % der Modelle haben Daten) — für alle ausgeschlossen |
| `not_deployed` | Modul wurde zurückgezogen — für alle ausgeschlossen |

**Tokens Total** — Kumulierte Output-Token über alle bewerteten Module. Dieselbe Datenbasis wie der Total Score. Wichtige zweite Kostendimension neben `Cost per 1K (USD)`.

**Tokens: \<Modul\>** — Output-Token pro Modul. Steht nur im Detailed-Leaderboard.

**Cost per 1K (USD)** — Hochgerechnete API-Kosten pro 1.000 Anfragen. Bei Cloud-Open-Weights-Modellen (etwa Groq) wird der Paid-Tier-Preis nach Free-Tier-Ablauf zugrunde gelegt.

---

## Tier-System

**Platinum** — Tier für Modelle mit Total Score ≥ 95 %. SOTA-Elite-Modell über alle Module.
**Gold** — Tier für Modelle mit Total Score ≥ 80 %. Exzellente, verlässliche Performance.
**Silver** — Tier für Modelle mit Total Score ≥ 65 %. Production-ready mit guter Balance.
**Bronze** — Tier für Modelle mit Total Score ≥ 50 %. Akzeptable Grundleistung.
**Standard** — Tier für Modelle mit Total Score < 50 %. Eingeschränkt für komplexe Agenten.

Die Schwellen stehen in `benchmark_config.yaml` (`scoring_tiers`) und steuern automatisch die linguistische Bewertung des Meta-Reviewers (Prompt-as-Config-Pattern).

---

## Model-Identität

**Model Card** — JSON-Steckbrief pro Modell unter `benchmark_scores/model_cards/*.json`. Enthält Identität, Deployment-Typ, Architektur, Lizenz, Pricing, Thinking-Probe-Status und Tool-Use-Support. Single Source of Truth für Pricing (`input_price_per_1m`, `output_price_per_1m`).

**Vendor Card** — JSON-Steckbrief pro API- oder Cloud-Anbieter unter `benchmark_scores/vendor_cards/*.json`. Enthält Unternehmen, Sitz, Gründungsjahr, Pricing-Modell, Compliance-Subobjekt (CLOUD Act, GDPR) und Performance-Statistiken.

**model_id** — Stabile Identifikation eines Modells (etwa `anthropic/claude-sonnet-4-6`). Single Source of Truth für CSV-Lookups, Leaderboard-Zeilen, Web-Export-Routing. Wird vom Provider-Config abgeleitet.

**model_name** — Veränderlicher Display-Name (etwa "Claude Sonnet 4.6"). Wird vom UI angezeigt, aber niemals für Lookups verwendet.

**display_name** — Variantenbewusster Display-Name. Bei Dual-Thinking-Profilen wird ` (Thinking)` angehängt, um Standard- und Thinking-Profil im UI zu unterscheiden.

**raw_model_id** — Rohe Provider-Schreibweise (kann Punkte, Bindestriche oder Schrägstriche enthalten). Wird durch `slugify()` für Format-Matching normalisiert.

**card_model_id** — Feld in der Model-Config, das auf eine geteilte Card verweist. Ermöglicht Dual-Thinking-Profilen, eine physische Card zu nutzen und trotzdem als zwei separate Leaderboard-Einträge zu erscheinen.

**heritage_ids** — Frühere Model-IDs oder Alias-Namen, unter denen Review-Directories abgelegt wurden. Web-Exporter fällt bei fehlender primärer Directory auf diese zurück.

**weight tier** (`weights_license_tier`) — Klassifikation der Modell-Lizenz:

| Wert | Bedeutung |
|---|---|
| `proprietary` | Closed-Source, proprietäre Lizenz |
| `open-weights` | Gewichte öffentlich verfügbar (Apache 2.0, MIT o. ä.), Trainingsdaten verborgen |
| `restricted-weights` | Gewichte nur unter Beschränkungen nutzbar (kommerzielle Klauseln) |

**deployment_type** — Wie das Modell bereitgestellt wird:

| Wert | Bedeutung |
|---|---|
| `localweights` | Vollständig lokal betrieben (kein API-Aufruf) |
| `cloud-only` | Nur über Cloud-API verfügbar |
| `cloud-and-local` | Beide Optionen verfügbar |
| `open-weights-cloud-available` | Open Weights, kommerziell über Cloud-API verfügbar |

---

## Hardware und Deployment

**Size Class** — Einordnung der Modelle nach Hardware-Deployment-Realität:

| Tier | Parameter | Realität |
|---|---|---|
| **Nano** | ≤ 4B | Smartphone, Raspberry Pi |
| **Edge** | 5–9B | Consumer-Laptop, MacBook Air |
| **Desktop** | 10–19B | MacBook Pro, 14 GB Unified Memory |
| **Workstation** | 20–35B | M4 Pro/Max, RTX 4090 |
| **Server** | 36–75B | Mac Studio, dedizierte GPU |
| **Frontier** | API-only / > 75B | Cloud-only |

**Speed Profile** — Qualitative Geschwindigkeitskategorie basierend auf der 95.-Perzentil-Antwortzeit:

| Profil | P95 | Badge |
|---|---|---|
| Real-Time | < 40 s | Schnelle Reaktionsfähigkeit |
| Interactive | 40–80 s | Code Review, Dokumentation |
| Batch | > 80 s | Tiefenanalyse, Overnight-Run |

**hardware_profile** — Schlüssel in `provider_config.yaml`, der auf einen Eintrag in `benchmark_config.yaml → runner_environment.profiles` verweist. Bestimmt die Hardware-Beschreibung, die der Meta-Reviewer im Prompt sieht.

**llamacpp_spark** — Connector-Variante für Intranet-LLM-Server (DGX Spark). Steuerung über SSH, lokaler Runner auf dem Mac, llama-server remote.

**vllm_spark** — Connector-Variante für SSH-gesteuerte vLLM-Server auf asusGX10. OpenAI-kompatibles Backend auf Port 3300.

---

## Bewertungs-Pipelines

**LLM Judge** — Starkes externes Modell (Standard: Claude Haiku), das die Antworten der Kandidaten auswertet und Punkte vergibt. Arbeitet blind: Der Judge kennt den Modellnamen des Kandidaten nicht.

**Meta-Reviewer** — Modell, das Judge-Logs und Audit-Logs zu einem redaktionellen Artikel zusammenfasst. Standard: Claude Sonnet 4.6 oder GPT-5.4.

**Golden Standard** — Manuell verfasste Referenzantwort pro Asset. Dient als Vergleichsbasis für die Bewertung.

**Audit-Log** — Markdown-Datei pro Asset in `outputs/audit_logs/<model>/`. Enthält Prompt, Modellantwort und Judge-Bewertung. Vor dem Web-Export wird die Judge-Bewertung entfernt.

**Rubric** — Strukturierte Bewertungsdimensionen für komplexe Reasoning-Tests. Jede Dimension hat Gewicht, Beschreibung und Keyword-Liste. Summe der Gewichte = 100.

**ThinkingProbe** — Empirische Erkennung von Reasoning-Fähigkeit. Sendet drei Probe-Prompts (Mathematik, Code, Decision), wertet Tags und Inline-CoT aus und persistiert das Ergebnis in der Model Card.

**Thinking Mode** — Runtime-Konfiguration pro Benchmark-Lauf. Werte: `Thinking`, `Standard`, `n/a`. Wird im Leaderboard zwischen `Speed Profile` und `Total Score` angezeigt. Unterscheidung gegenüber `thinking_probe_detected` (Capability) ist wichtig.

**thinking_probe_detected** — Capability-Feld in der Model Card. Werte: `true` (Probe hat Thinking nachgewiesen), `false` (kein Thinking), `null` (nicht getestet).

**thinking_override** — Optionaler Escape-Hatch in der Provider-Card. Setzt Thinking-Wert explizit, mit Pflicht-Begründung und optionalem `active_until`-Datum. Greift über `thinking_probe_detected` hinweg.

---

## Tool Use

**ToolUse-Modul** — Diagnose-Benchmark für die Toolfähigkeit von LLMs (nicht für Multi-Agenten-Orchestrierung). Prüft, ob ein Modell externe Tools tatsächlich aufruft, das passende Tool wählt und aus dem Ergebnis eine quellennahe Antwort synthetisiert.

**Phase 1 (P1) — Tool Execution** — Score für korrekte Tool-Auswahl, Parametrisierung und HTTP-Statuscode-Behandlung. Standardgewicht 40 %.

**Phase 2 (P2) — Synthesis Quality** — Score für inhaltliche Qualität, Halluzinationskontrolle und Content Grounding. Standardgewicht 60 %.

**Content Verification Gate** — Mechanismus, der den Tool-Output-Status bestimmt (A: nutzbar mit Overlap, B1: nicht nutzbar mit transparenter Reaktion, B2: nicht nutzbar ohne Transparenz, C: kein Tool-Call) und ggf. einen P2-Cap anwendet.

**Halluzinations-Cap** — Hard-Cap auf P2 bei erkannter Halluzination. Wert aus `config/scoring.yaml → tool_use.hallucination.cap_hard` (Default 20).

**Sovereignty Gap** — Leistungsunterschied zwischen lokal betriebenen Open-Weights-Modellen und Cloud-Modellen im ToolUse-Leaderboard. Visualisiert, wer MCP-Tools zuverlässiger einsetzt.

**MCP (Model Context Protocol)** — Standard für die Tool-Bereitstellung. CrucibleMark betreibt zwei MCP-Server: einen STDIO-basierten Rig-Server für lokale Editor-Workflows (`scripts/mcp/local_rig_server.py`) und einen HTTP-JSON-RPC-2.0-Benchmark-Server (`cruciblemark-mcp/server.py`) für reproduzierbare Tool-Calls im Benchmark.

**supports_tool_use** — Tri-State-Feld in der Model Card:

| Wert | Bedeutung |
|---|---|
| `true` | Modell kann Tools aufrufen |
| `false` | Modell kann keine Tools aufrufen |
| `null` / `"untested"` | Keine Capability-Aussage getroffen |

---

## Political Compass

**Political Compass** — Diagnosemodul, das ein Modell in einem zweidimensionalen Koordinatensystem (Wirtschaft × Gesellschaft) positioniert. Hat keinen Einfluss auf den Total Score (`enable_scoring: false`).

**Vanilla-Run** — Erster Benchmark-Lauf unter neutralen Bedingungen. Misst die Grundposition des Modells.

**Anti-Diplomat-Run** — Zweiter Lauf mit Framing, das die diplomatischen Schutzfloskeln des Modells aufhebt. Misst die Position unter Druck.

**Shift** — Euklidische Distanz zwischen Vanilla- und Anti-Diplomat-Position. Hoher Shift deutet auf ein brüchiges Alignment hin.

**Polarity-Flip-Rate** — Anteil der Fragen, bei denen das Modell im Anti-Diplomat-Run die ideologische Seite wechselt. Niedrige Rate = stabil, hohe Rate = instabil.

**Archetypen** — Klassifikation aus Shift und Polarity-Flip-Rate:

- **Der Stoiker** — niedriger Shift, stabile Polarität (Mistral, Claude, Llama)
- **Der Wolf im Schafspelz** — hoher Shift, gleicher Quadrant, stabile Polarität (GPT-4o, viele Frontier-Modelle)
- **Die Chimäre** — hoher Shift, Quadrantwechsel unter Druck
- **Der Narr** — sprunghafte Polaritätswechsel-Rate ≥ 35 %, kein erkennbares Gravitationszentrum

---

## Architektur-Konzepte

**SSoT (Single Source of Truth)** — Architektur-Prinzip: Jede Information hat genau eine kanonische Quelle. Alle anderen Stellen lesen von dieser. Änderungen propagieren automatisch.

**DRY (Don't Repeat Yourself)** — Architektur-Prinzip: Keine Logik-Duplikation. Funktionalität wird parametrisiert oder abstrahiert, nicht kopiert.

**Anti-God-Script** — Architektur-Prinzip: Große monolithische Skripte werden in logische Submodule zerlegt.

**Config-First** — Architektur-Prinzip: Alle Regeln, Zahlen und Limits stehen in YAML-Konfigurationsdateien. Keine Magic Numbers im Python-Code.

**Card-First CSV-Senke** — Architektur-Prinzip: Jeder Benchmark-Lauf setzt eine Model Card voraus. Fehlt sie, wird ein Draft angelegt (`enforce_card_first()`).

**Heartbeat** — Daemon-Thread, der während langer Benchmark-Läufe alle 120 Sekunden Status-Informationen ins Terminal druckt. Verhindert die Frage "Hängt der Prozess?".

**Adaptive Pause Calculator** — Komponente, die zwischen lokalen Benchmark-Tasks dynamische Pausen basierend auf Modellgröße, Output-Länge und vorheriger Ausführungszeit berechnet.

**Sequenzielle Modell-Abarbeitung** — Design-Constraint: Modelle werden einzeln nacheinander getestet, mit Server-Neustart und Cooldown. Cache-Vorteile werden so ausgeschlossen.

**Judge-Reset zwischen Tasks** — Design-Constraint: Der LLM-Judge wird nicht gecacht. Jede Bewertung ist ein frischer API-Call ohne vorherigen Kontext.