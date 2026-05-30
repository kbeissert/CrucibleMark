**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:43


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination erkannt wurde, die Synthesetreue aber zu ungleichmäßig bleibt, um unbeaufsichtigte Wissens-Pipelines ohne Guardrails zu tragen.

**Tool-Execution-Profil**

Claude Opus 4.7 zeigt ein belastbares Tool-Profil. Die Calls waren valide, MCP-konform und ohne Retry ausführbar. Das spricht gegen ein Protokoll- oder Formatproblem und für tatsächliches Verständnis der Tool-Schnittstelle. Besonders stark ist es beim Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis search statt fetch nötig ist: Hier wählt das Modell das richtige Werkzeug sicher. Das ist ein klares Signal für echte Werkzeugwahl statt starrem Muster.

Weniger deterministisch ist es beim URL-Construction-and-Fetch-Test, der prüft, ob das Modell die Ziel-URL aus eigenem Wissen korrekt ableitet und dann sauber fetcht. Die Ausführung ist brauchbar, aber nicht präzise genug, um aus freier URL-Konstruktion einen harten Produktionspfad zu machen. Für Orchestrierung mit vorhandenen Discovery- oder Search-Schritten ist das akzeptabel. Für direkte URL-Ableitung ohne Vorvalidierung ist es zu fehleranfällig.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht konstant präzise genug. Der P2-Wert von 76.67 wird von sehr guten Ergebnissen bei HTTP Fetch & Extract und Tool Failure Handling getragen, fällt aber bei EU License Research und besonders bei Multilingual Search & Synthesis sichtbar ab. Das Modell schreibt strukturiert und vollständig, verdichtet aber nicht immer hart entlang der belegten Tool-Ausgabe. Für produktive Pipelines heißt das: gute Lesbarkeit, aber nicht automatisch maximal enge Faktendisziplin.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Training kommen, bleibt das Vertrauenssignal positiv. Keine Halluzination wurde erkannt, Content-Verification-State A. Der P2-Wert von 60 zeigt jedoch, dass das Modell zwar nicht erfindet, die belegte Evidenz aber nicht scharf genug in die Endantwort überführt.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit Tool-Fehlern statt erfundenem Seiteninhalt prüft, reagiert Claude Opus 4.7 produktionsgerecht. P2 100 und keine Halluzination trotz Fehler. Das ist ein starkes Signal: Wenn ein Tool scheitert, kommuniziert das Modell den Ausfall, statt die Lücke mit plausibel klingendem Inhalt zu füllen.

**Betriebsprofil**

Total 112.66s. Frühe Calls schnell bei 2.45s und 15.04s, MCP-Latenz 1.29s. Gesamtlaufzeit für agentische Mehrschritt-Pipelines klar lang. Kosten pro Run $0.191580. Für die gezeigte Leistung tragbar, aber klar teuer.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell Tools auswählt, Schritte koordiniert und Fehler transparent behandelt. Gut passend für Recherche-Orchestrierung, Web-gestützte Analysten-Workflows und menschennahe Review-Stufen. Nicht die erste Wahl für vollautomatische Compliance-, Policy- oder mehrsprachige Wissens-Synthese ohne nachgelagerte Verifikation. Wenn du enge Quellendisziplin und belastbare Tool-Steuerung wichtiger findest als Latenz und Kosten, ist es ein brauchbarer Orchestrator mit Pflicht zu Output-Guardrails.