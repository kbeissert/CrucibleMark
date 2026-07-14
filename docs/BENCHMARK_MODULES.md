# Benchmark-Module im Überblick

**Stand: v5.1.0 · 2026-07-14**

CrucibleMark bewertet KI-Modelle nicht auf theoretisches Faktenwissen, sondern auf ihre praktische Einsetzbarkeit im Produktionsalltag. Jedes Benchmark-Modul simuliert ein spezifisches Real-World-Szenario, mit dem Produktteams, Entwickler und Redakteure täglich konfrontiert sind.

## Total Score (Gesamtwertung)

Der Total Score ist das aggregierte Gesamtergebnis über alle bewerteten Module. Er ist besonders aussagekräftig, wenn ein einziges Generalist-Modell als universeller Assistent eingesetzt wird — typischerweise bei kommerziellen Abonnement-Modellen, die in diversen Szenarien verlässlich funktionieren müssen. Wer spezialisierte Modelle für konkrete Aufgaben oder Agenten-Pipelines einsetzt, findet in den Einzel-Modul-Scores die präzisere Entscheidungsgrundlage.

### Designprinzip: Module als gleichwertige, geschlossene Tests

Jedes Benchmark-Modul ist eine in sich geschlossene, vollständige Messung einer Alltagsdimension. Die interne Asset-Anzahl eines Moduls hat keinen Einfluss auf seinen Gesamtbeitrag — ein Modul mit fünf Assets und eines mit elf Assets tragen gleichwertig bei.

Die Module lassen sich unabhängig voneinander auswerten. Wer ein Modell nur unter dem Aspekt Code-Qualität oder Reasoning bewerten will, erhält direkt den Einzel-Modul-Score. Der Total Score beantwortet die Frage nach dem stärksten Generalisten, nicht nach dem besten Spezialisten.

### Konfigurierbare Gewichtung

Die Modulgewichtung steht in `integration.leaderboard.module_weight` der jeweiligen Modul-`config.yaml`. Für ein reines Developer-Setup lassen sich Code Quality und CLI Benchmark höher gewichten oder irrelevante Module deaktivieren (`enabled: false` in `benchmark_config.yaml`). Der Score normalisiert sich automatisch auf die aktiven Module und bleibt im Bereich 0 bis 100.

> **CLI Benchmark als Sonderfall:** Das CLI-Modul ist als leichtgewichtiges Supplement konzipiert (kurze Syntax-Tests, kein tiefes Reasoning). Es trägt mit `module_weight: 0.5` nur halb so viel zum Total Score bei wie ein Vollmodul. Für Developer-Profile kann dieser Wert auf `1.0` erhöht werden.

---

## Code Quality (Code-Qualität)

**Typ:** Hard Skill
**Gewicht:** 1.0 (Standard-Vollmodul)

Dieses Modul prüft, ob die KI als verlässlicher Code-Reviewer agieren kann. Im Mittelpunkt steht bestehender Quelltext: systematische Analyse auf Sicherheitslücken (OWASP), Accessibility-Verstöße (WCAG) und Architekturprobleme. In vier Schwierigkeitsstufen — von offensichtlichen Bugs bis zu subtilen Race Conditions — wird geprüft, ob das Modell den Unterschied zwischen "funktioniert" und "ist production-ready" erkennt.

---

## CLI Benchmark (Kommandozeilen-Fähigkeiten)

**Typ:** Hard Skill (leichtgewichtig)
**Gewicht:** 0.5 (Supplement)

Systemadministratoren und DevOps-Engineers verlassen sich auf pixelgenaue Befehle — ein fehlendes Flag oder ein falsches Argument kann Systeme gefährden. Das Modul simuliert Terminal-Aufgaben von Disk-Cleanup bis Docker-Deployment und bewertet drei Dimensionen gleichzeitig: Korrektheit der Flags (Exact Match), Sicherheit (gebannte Destruktivbefehle) und Effizienz. Ausschweifige Modelle werden für unnötige Ausgabezeilen bestraft.

---

## Reasoning (Logik und Schlussfolgern)

**Typ:** Metrik
**Gewicht:** 1.0

Im Berufsalltag erfordern Probleme oft mehrstufige Gedankengänge — und manchmal lautet die richtige Antwort: "Das ist nicht lösbar." Das Modul testet neben klassischer Deduktion auch Feasibility-Detection (Erkennen unmöglicher Aufgaben) und Metakognition (Selbstkorrektur falscher Annahmen). Ein eigener Reasoning Complexity Index (RCI) zeigt, ob ein Modell nur antwortet oder tatsächlich denkt.

---

## UX Writing (Nutzerführung und Textgestaltung)

**Typ:** Soft Skill
**Gewicht:** 1.0

Gute Software kommuniziert unmissverständlich, empathisch und lösungsorientiert. Das Modul evaluiert die KI als professionellen UX-Writer für Fehlermeldungen, Button Labels, Onboarding-Flows und ARIA-Accessibility-Labels. Strenge Bewertung, ob Texte tatsächlich nutzerzentriert und prägnant sind, Jargon vermieden wird und der geforderte Tonfall exakt eingehalten wird — bis hin zu gesundheitskritischen Microcopy-Szenarien.

---

## Documentation Quality (Dokumentationsqualität)

**Typ:** Soft Skill
**Gewicht:** 1.0

Technische Systeme sind nur so gut wie ihre Dokumentation — eine KI, die halluzinierte Parameter oder falsche Code-Beispiele produziert, ist gefährlicher als keine Dokumentation. Das Modul prüft READMEs, API-Referenzen, Setup-Guides und Changelogs auf strukturelle Vollständigkeit, Genauigkeit und Lesbarkeit (Flesch-Kincaid). Es deckt auf, ob das Modell lückenlose und korrekte Dokumentation für andere Entwickler liefern kann.

---

## Content Transformation (Inhaltsanpassung)

**Typ:** Soft Skill
**Gewicht:** 1.0

Inhalte müssen in der Praxis ständig für andere Zielgruppen oder Ausgabeformate aufbereitet werden — vom Landing-Page-Teaser über einen Twitter-Thread mit striktem 280-Zeichen-Limit bis zur Vereinfachung juristischer Fachtexte. Das Modul bewertet, ob Kerninformationen erhalten bleiben, Formatvorgaben präzise eingehalten werden, der Ton korrekt angepasst wird und das Modell selbst unter Provokation (aggressiver Kundenton) professionell bleibt.

---

## Cultural Intelligence (Kulturelle Intelligenz)

**Typ:** Metrik
**Gewicht:** 1.0

Sprachliche Kompetenz endet nicht bei grammatikalischer Korrektheit. Das Modul testet, ob eine KI echte interkulturelle Sensibilität beherrscht: idiomatische Übersetzungen (kein wörtliches "Es regnet Katzen und Hunde"), korrekte Formalitätsstufe (Sie/Du), konsistente Verwendung regionaler Varianten (DE/AT/CH). Geprüft wird gezielt, ob das Modell kulturelle Fauxpas, Stereotypen und regionale Inkonsistenzen vermeidet.

---

## Political Compass (Politischer Kompass und Bias-Analyse)

**Typ:** Spezial (Diagnosemodul)
**Gewicht:** kein Einfluss auf den Total Score

Jedes KI-Modell trägt ein unsichtbares Weltbild, das durch Training und Alignment entsteht. Dieses Modul bewertet nicht — es diagnostiziert: Es positioniert ein Modell in einem zweidimensionalen Koordinatensystem (Wirtschaft × Gesellschaft) und zwingt es via "Anti-Diplomat"-Prompting, seine neutralen Schutzfloskeln aufzugeben. Der Vergleich zwischen Vanilla- und Forced-Modus deckt auf, ob ein Modell stabil ist ("Der Stoiker"), unter Druck eine Maske verliert ("Der Wolf im Schafspelz"), die Seite wechselt ("Die Chimäre") oder gar kein erkennbares Gravitationszentrum besitzt ("Der Narr"). Das Modul fließt nicht in den Total Score ein; es ist ein reines Diagnosewerkzeug. Konzept-Details: [POLITICAL_COMPASS_KONZEPT.md](POLITICAL_COMPASS_KONZEPT.md).

---

## Tool Use (Werkzeugnutzung)

**Typ:** Spezial (Diagnosemodul)
**Gewicht:** 1.0 im Total Score (v5.0+)

Ein Modell, das überzeugend antwortet, ohne je ein Tool aufgerufen zu haben, ist gefährlicher als eines, das offen zugibt, nicht zu wissen. Das Modul ist ein Diagnose-Benchmark für die Toolfähigkeit von LLMs — kein Test für Multi-Agenten-Orchestrierung oder komplexe Agentenplanung. Geprüft werden drei Kernfähigkeiten: ob ein Modell externe Tools (Web-Suche, HTTP-Fetch) tatsächlich aufruft, das passende Tool für die Aufgabe selbst auswählt und aus dem Ergebnis eine nachvollziehbare, quellennahe Antwort synthetisiert. Sechs Assets testen jeweils eine klar abgrenzbare Fähigkeit: Tool-Aufruf, Tool-Auswahl, URL-Inferenz, Fehlertoleranz (404-Szenario) und deutschsprachige Synthese aus mehrsprachigen Quellen.

Ein kleineres, schnelles Open-Weight-Modell kann hier sehr gut abschneiden — nicht weil es allgemein "intelligenter" ist, sondern weil es die konkreten Aufgaben zuverlässig mit Tool-Nutzung erfüllt. Damit beantwortet das Modul eine praktische Frage: Ist dieses Modell toolfähig genug, um mit MCP-Erweiterung (etwa in VS Code) produktiv in einem realen Arbeitskontext eingesetzt zu werden? Details: [TOOLUSE_MODULE.md](TOOLUSE_MODULE.md).