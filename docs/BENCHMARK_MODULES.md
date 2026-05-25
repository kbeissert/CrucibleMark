# CrucibleMark: Die Benchmark-Module im Überblick

CrucibleMark wurde entwickelt, um KI-Modelle nicht auf theoretisches Faktenwissen, sondern auf ihre praktische Einsetzbarkeit im Produktionsalltag zu testen. Jedes Benchmark-Modul simuliert ein spezifisches Real-World-Szenario, mit dem Produktteams, Entwickler und Redakteure täglich konfrontiert sind. Die folgende Übersicht erklärt, welchen fachlichen Zweck die einzelnen Testbereiche erfüllen.

## Total Score (Gesamtwertung)
Der Total Score ist das aggregierte Gesamtergebnis über alle bewerteten Module. Er ist besonders aussagekräftig, wenn ein einziges Generalist-Modell als universeller Assistent eingesetzt wird – typischerweise bei kommerziellen Abonnement-Modellen, die in diversen Szenarien verlässlich funktionieren müssen. Wer dagegen spezialisierte Modelle für konkrete Aufgaben oder Agenten-Pipelines einsetzt, findet in den Einzel-Modul-Scores die präzisere Entscheidungsgrundlage.

### Designprinzip: Module als gleichwertige, geschlossene Tests

Jedes Benchmark-Modul ist als **in sich geschlossene, vollständige Messung** einer Alltagsdimension konzipiert. Das bedeutet:

- **Gleiche Gewichtung by default:** Jedes Vollmodul fließt mit dem gleichen Gewicht in den Total Score ein. Die interne Asset-Anzahl eines Moduls hat keinen Einfluss auf seinen Gesamtbeitrag — ein Modul mit 5 Assets und eines mit 11 Assets tragen gleichwertig bei.
- **Jedes Modul ist für sich aussagekräftig:** Die Module können unabhängig voneinander ausgewertet werden. Wer ein Modell nur unter dem Aspekt _Code-Qualität_ oder _Reasoning_ bewerten will, erhält direkt den Einzel-Modul-Score — ohne den Total Score zu betrachten.
- **Der Total Score ist ein Generalist-Filter:** Er beantwortet die Frage: *„Welches Modell ist im Durchschnitt aller Alltagsbereiche am stärksten?"* — nicht: *„Welches Modell ist in Bereich X das beste?"*

### Konfigurierbare Gewichtung

Die Modulgewichtung ist über `integration.leaderboard.module_weight` in der jeweiligen Modul-`config.yaml` einstellbar. Wer CrucibleMark z. B. für ein reines Developer-Setup betreibt, kann Code Quality und CLI Benchmark höher gewichten oder nicht relevante Module deaktivieren (`enabled: false` in `benchmark_config.yaml`). Der Score normalisiert sich automatisch auf die aktiven Module — das Ergebnis bleibt immer im Bereich 0–100.

> **CLI Benchmark als Sonderfall:** Das CLI-Modul wurde bewusst als leichtgewichtiges Supplement konzipiert (kurze Syntax-Tests, kein tiefes Reasoning). Es trägt daher mit `module_weight: 0.5` nur halb so viel zum Total Score bei wie ein Vollmodul. Wer für Developer-Profile testet, kann diesen Wert auf `1.0` erhöhen.

## Code Quality (Code-Qualität)
Dieses Modul prüft, ob eine KI als verlässlicher Code-Reviewer agieren kann. Es geht nicht darum, funktionierenden Code zu schreiben, sondern bestehenden Quelltext systematisch auf Sicherheitslücken (OWASP), Accessibility-Verstöße (WCAG) und Architekturprobleme zu analysieren. In vier Schwierigkeitsstufen – von offensichtlichen Bugs bis zu subtilen Race Conditions – testet das Modul, ob das Modell den Unterschied zwischen „funktioniert" und „ist production-ready" erkennt.

## CLI Benchmark (Kommandozeilen-Fähigkeiten)
Systemadministratoren und DevOps-Engineers verlassen sich auf pixelgenaue Befehle – ein fehlendes Flag oder ein falsches Argument kann Systeme gefährden. Dieses Modul simuliert Terminal-Aufgaben von Disk-Cleanup bis Docker-Deployment und bewertet drei Dimensionen gleichzeitig: Korrektheit der Flags (Exact Match), Sicherheit (gebannte Destruktivbefehle) und Effizienz – ausschweifende Modelle werden für unnötige Ausgabezeilen hart bestraft.

## Reasoning (Logik und Schlussfolgern)
Im Berufsalltag erfordern Probleme oft mehrstufige Gedankengänge – und manchmal lautet die richtige Antwort: „Das ist nicht lösbar." Dieses Modul testet neben klassischer Deduktion auch Feasibility-Detection (Erkennen unmöglicher Aufgaben) und Metakognition (Selbstkorrektur falscher Annahmen). Ein eigener Reasoning Complexity Index (RCI) zeigt, ob ein Modell nur antwortet oder tatsächlich denkt.

## UX Writing (Nutzerführung und Textgestaltung)
Gute Software kommuniziert unmissverständlich, empathisch und lösungsorientiert. Dieses Modul evaluiert die KI als professionellen UX-Writer für Fehlermeldungen, Button Labels, Onboarding-Flows und ARIA-Accessibility-Labels. Es wird streng bewertet, ob Texte tatsächlich nutzerzentriert und prägnant sind, Jargon vermieden wird und der geforderte Tonfall exakt eingehalten wird – bis hin zu gesundheitskritischen Microcopy-Szenarien.

## Documentation Quality (Dokumentationsqualität)
Technische Systeme sind nur so gut wie ihre Dokumentation – und eine KI, die halluzinierte Parameter oder falsche Code-Beispiele produziert, ist gefährlicher als keine Dokumentation. Dieses Modul prüft READMEs, API-Referenzen, Setup-Guides und Changelogs auf strukturelle Vollständigkeit, Genauigkeit und Lesbarkeit (Flesch-Kincaid). Es deckt auf, ob das Modell lückenlose und korrekte Dokumentation für andere Entwickler liefern kann.

## Content Transformation (Inhaltsanpassung)
Inhalte müssen in der Praxis ständig für andere Zielgruppen oder Ausgabeformate aufbereitet werden – vom Landing-Page-Teaser über einen Twitter-Thread mit striktem 280-Zeichen-Limit bis hin zur Vereinfachung juristischer Fachtexte. Dieses Modul bewertet nicht nur, ob Kerninformationen erhalten bleiben, sondern auch ob das Modell Formatvorgaben präzise einhält, den Ton korrekt anpasst und selbst unter Provokation (aggressiver Kundenton) professionell bleibt.

## Cultural Intelligence (Kulturelle Intelligenz)
Sprachliche Kompetenz endet nicht bei grammatikalischer Korrektheit. Dieses Modul testet, ob eine KI echte interkulturelle Sensibilität beherrscht: von idiomatischen Übersetzungen (kein wörtliches „Es regnet Katzen und Hunde") über die korrekte Formalitätsstufe (Sie/Du) bis zur konsistenten Verwendung regionaler Varianten (DE/AT/CH). Es prüft gezielt, ob ein Modell kulturelle Fauxpas, Stereotypen und regionale Inkonsistenzen vermeidet.

## Political Compass (Politischer Kompass & Bias-Analyse)
Jedes KI-Modell trägt ein unsichtbares Weltbild, das durch Training und Alignment entsteht. Dieses Modul dient nicht der Bewertung, sondern der Diagnose: Es positioniert ein Modell in einem zweidimensionalen Koordinatensystem (Wirtschaft × Gesellschaft) und zwingt es via „Anti-Diplomat"-Prompting, seine neutralen Schutzfloskeln aufzugeben. Der Vergleich zwischen Vanilla- und Forced-Modus deckt auf, ob ein Modell ein Narr, ein Wolf im Schafspelz, eine Chimäre oder ein Stoiker ist – und wo seine blinden Flecken beim Vorsortieren von Informationen liegen. Einziges Modul ohne Score-Einfluss: reines Diagnosewerkzeug.

## Tool Use & Function Calling (Werkzeugnutzung)
Ein Modell, das überzeugend antwortet, ohne je ein Tool aufgerufen zu haben, ist gefährlicher als eines, das offen zugibt, nicht zu wissen. Dieses Modul ist ein Diagnose-Benchmark für die Toolfähigkeit von LLMs — kein Test für Multi-Agenten-Orchestrierung oder komplexe Agentenplanung. Es prüft drei Kernfähigkeiten: ob ein Modell externe Tools (Web-Suche, HTTP-Fetch) tatsächlich aufruft, das passende Tool für die Aufgabe selbst auswählt und aus dem Ergebnis eine nachvollziehbare, quellennahe Antwort synthetisiert. Sechs Assets testen dabei jeweils eine klar abgrenzbare Fähigkeit: Tool-Aufruf, Tool-Auswahl, URL-Inferenz, Fehlertoleranz (404-Szenario) und deutschsprachige Synthese aus mehrsprachigen Quellen. Ein kleineres, schnelles Open-Weight-Modell kann hier sehr gut abschneiden — nicht weil es allgemein „intelligenter" ist, sondern weil es die konkreten Aufgaben zuverlässig mit Tool-Nutzung erfüllt. Damit beantwortet das Modul eine praktische Frage: Ist dieses Modell toolfähig genug, um mit MCP-Erweiterung (z.B. in VS Code) produktiv in einem realen Arbeitskontext eingesetzt zu werden? Das Modul fließt nicht in den Total Score ein — es ist ein Infrastruktur-Diagnosetest, der vor dem Einsatz von Tool-Calling-Pipelines absolviert werden sollte.
