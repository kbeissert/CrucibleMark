**Deployment-Urteil**

> **Erstellt am:** 19.07.2026, 23:27:40


Nicht deploy, weil weder ein valider Tool-Call vorliegt noch irgendein belastbares Ergebnis aus der Tool-Pipeline entstanden ist. Der Combined-Score von 0.00 ist hier nur Bestätigung, nicht die Hauptaussage.

**Tool-Execution-Profil**

Für eine MCP-gestützte Infrastruktur ist das Kernproblem eindeutig: Das Modell hat keinen validen Tool-Call produziert. Damit ist nicht nur die Ausführung gescheitert, sondern schon die grundlegende Protokollfähigkeit nicht nachgewiesen. Ob es das richtige Werkzeug wählen kann, bleibt deshalb offen, aber genau diese Unklarheit ist im Produktionseinsatz bereits ein Ausschlusskriterium.

Bei Web Search & Tool Selection, dem Test auf eigenständige Wahl zwischen Suche und direktem Abruf, liegen keine verwertbaren Resultate vor. Dasselbe gilt für URL Construction & Fetch, also den Test, ob das Modell eine Ziel-URL korrekt herleitet und anschließend sauber abruft. Es zeigt damit keine nachweisbare Werkzeugintelligenz, sondern hinterlässt eine Ausführungslücke. Retry war nicht erforderlich. Das spricht eher gegen einen bloßen Formatfehler und eher für fehlende oder nicht stabil abrufbare Tool-Use-Fähigkeit in diesem Setup.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es keine Grundlage. P2 ist durchgängig n/a, weil keine tragfähigen Tool-Ergebnisse zur Weiterverarbeitung entstanden sind. Für Architekten ist das ein harter Befund: Ohne belastbare Verdichtung kann das Modell keine letzte Meile zwischen Tool-Ausgabe und nutzbarer Antwort übernehmen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist ein positives Vertrauenssignal, aber nur ein enges. Es beweist Zurückhaltung, nicht operative Tauglichkeit.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Aufruf prüft, hat das Modell keinen Seiteninhalt halluziniert. Das ist für Produktion die richtige Fehlerrichtung. Ein Modell darf Unsicherheit offenlegen. Es darf bei einem Fehler nichts erfinden. Dieser Punkt entlastet das Modell sicherheitlich, kompensiert aber nicht die fehlende Tool-Ausführung.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments grundsätzlich attraktiv. In der vorliegenden Bewertung liegt es jedoch 0.83 Punkte unter dem Fleet-Ø von 66.54. Der Souveränitätsvorteil ist real, aber ohne nachgewiesene MCP-Ausführung nicht ausreichend.

**Fazit & Empfehlung**

Nicht für autonome oder halbautonome Tool-Pipelines freigeben. Wenn überhaupt, dann nur für offline-nahe, rein textuelle Assistenzrollen ohne Tool-Verantwortung und mit harter externer Orchestrierung, die jede Aktion vorgibt. Für Recherche, Fetch, URL-Ableitung, dynamische Tool-Wahl oder Compliance-nahe Workflows fehlt der produktionsreife Nachweis.