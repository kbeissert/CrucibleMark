**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:19:33


Bedingt deploy: Die Tool-Ausführung ist stark, aber die erkannte Halluzination bei ungültigem Tool-Call und der nicht valide Tool-Call selbst disqualifizieren das Modell für unbeaufsichtigte MCP-Pipelines.

**Tool-Execution-Profil**

Qwen 3.8 27B zeigt echte Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es zuverlässig, dass erst web_search statt fetch nötig ist. Das spricht gegen ein starres Abrufmuster. Auch beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Eigenwissen misst, arbeitet es grundsätzlich brauchbar, aber nicht präzise genug für deterministische Abläufe. Das Profil ist damit stark in der Planungsphase und etwas schwächer in der exakten Protokollausführung. Der P1-Wert stützt das, aber produktionsrelevant ist vor allem: Der Tool-Call war im Lauf nicht valide. Das ist kein kosmetischer Formatfehler, sondern ein Integrationsrisiko an der MCP-Grenze. Positiv ist, dass kein Retry nötig war. Das Modell versteht also den Aufgabenfluss, scheitert aber nicht sauber genug an den formalen Schnittstellen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die Synthesequalität ist insgesamt der klare Schwachpunkt. Bei HTTP Fetch & Extract und URL Construction & Fetch verdichtet es sauber, aber bei EU License Research und Multilingual Search & Synthesis bricht die Präzision deutlich ein. Das Muster ist konsistent: Fakten werden gefunden, aber nicht stabil genug in belastbare Ergebnistexte überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es formal auf dem sicheren Pfad. Es halluziniert dort nicht aus dem Training, obwohl die Verdichtung schwach bleibt. Das ist wichtig. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko, nicht nur ein Qualitätsmangel. Sobald ein Modell erfundene Inhalte als Werkzeugergebnis ausgeben kann, verliert die gesamte Tool-Infrastruktur ihren Vertrauensanker.

**Fehlerresilienz**

Hier liegt der produktionskritische Defekt. Beim 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Aufruf prüfen soll, kommuniziert Qwen 3.8 27B den Fehler nicht sauber, sondern halluziniert trotz Fehlers Seiteninhalt. Das ist für Produktion ohne Ausnahme inakzeptabel. Eine Pipeline kann mit einem offen gemeldeten Fetch-Fehler umgehen. Sie kann nicht sicher mit erfundenem Ersatzinhalt umgehen.

**Betriebsprofil**

Total 326.55s. Call 1 5.75s. Call 2 47.12s. MCP-Latenz 1.56s. Langsam für die erzielte Gesamtqualität. Kosten pro Run: local, damit infrastrukturseitig günstig.

**Fazit & Empfehlung**

Geeignet für assistierte Recherche-, Such- und Orchestrierungs-Pipelines mit menschlicher Abnahme oder harten nachgelagerten Validierern. Nicht geeignet für Compliance-, Dokumentations-, Incident- oder Retrieval-Workflows, in denen Tool-Fehler strikt transparent bleiben müssen und Synthesen direkt weiterverarbeitet werden. Wer es einsetzt, sollte Tool-Outputs schema-validieren, Fehlerpfade hart abfangen und jede inhaltliche Zusammenfassung gegen die Rohquellen prüfen.