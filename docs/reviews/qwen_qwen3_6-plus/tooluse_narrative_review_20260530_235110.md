**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:51:10


Nicht deploy, weil für Tool-Ausführung und Synthese keine verwertbaren Nachweise vorliegen, der Combined-Score bei 0.00 steht und der Tool-Call nicht als valide bestätigt ist.

**Tool-Execution-Profil**

Für den Kernpunkt dieser Bewertung fehlt die belastbare Basis. Weder für EU License Research, HTTP Fetch & Extract noch für die beiden Auswahltests liegen P1-Daten vor. Das ist im Produktionseinsatz selbst schon ein negatives Signal, weil sich damit nicht belegen lässt, ob das Modell MCP-konform arbeitet, das richtige Tool wählt oder valide Aufrufe erzeugt.

Besonders kritisch ist die Lücke bei Web Search & Tool Selection, also dem Test, ob das Modell ohne expliziten Hinweis erkennt, dass statt fetch eine Websuche nötig ist, sowie bei URL Construction & Fetch, also der Fähigkeit, eine Ziel-URL korrekt abzuleiten und dann sauber abzurufen. Ohne diese Daten lässt sich keine Werkzeugintelligenz attestieren. Der Befund spricht eher für fehlende Verifikation als für belastbare Agententauglichkeit. Ein Retry war nicht erforderlich, daher gibt es keinen Hinweis auf ein bloßes Formatproblem. Das Grundproblem ist fehlende nachgewiesene Ausführungssicherheit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es keine belastbare Bewertung. P2 ist durchgängig n/a. Damit bleibt offen, ob das Modell extrahierte Inhalte präzise zusammenführt oder ob es bei mehrschrittigen Tool-Ergebnissen Details verliert. Für Architekten ist das ein Blocker, weil gerade diese Verdichtung über die Nutzbarkeit in produktiven Tool-Pipelines entscheidet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen bezogen werden, zeigt zumindest keinen Halluzinationsbefund. Das ist ein positives Vertrauenssignal. Es ersetzt aber keine echte Verifikation, weil auch hier weder Inhaltsprüfung noch Synthesequalität ausgewiesen sind.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Call prüft, wurde kein halluzinierter Ersatzinhalt erkannt. Das ist für Produktion wichtig und grundsätzlich akzeptabel. Allerdings bleibt auch hier offen, wie gut die tatsächliche Fehlerkommunikation formuliert und in den Arbeitsfluss eingebettet war. Positiv ist nur der Mindestbefund: kein erfundener Seiteninhalt trotz Fehler.

**Betriebsprofil**

Keine verwertbaren Latenzdaten. Kosten pro Run: local. Leistungsrelation daher nicht seriös bewertbar.

**Fazit & Empfehlung**

Dieses Modell ist derzeit nicht für MCP-gestützte Produktionspipelines freizugeben, in denen Tool-Wahl, korrekte Calls und belastbare Verdichtung nachweisbar funktionieren müssen. Der fehlende Halluzinationsbefund im Honeypot und im 404-Fall ist hilfreich, reicht aber nicht aus. Wenn überhaupt, dann nur für isolierte, nicht-kritische Assistenzpfade ohne Tool-Autonomie und mit harter externer Validierung vor jeder Weiterverarbeitung. Für Compliance, Web-Recherche, Fetch-basierte Extraktion oder dynamische Tool-Orchestrierung nicht geeignet, bis echte P1- und P2-Nachweise vorliegen.