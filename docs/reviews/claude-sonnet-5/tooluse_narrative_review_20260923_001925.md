**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:19:25


Bedingt deploy, weil die Tool-Nutzung stark ist und keine Halluzination erkannt wurde, aber die Tool-Calls nicht durchgängig valide waren und die Synthesequalität für produktive Wissenspipelines zu ungleich ausfällt.

**Tool-Execution-Profil**

Claude Sonnet 5 zeigt echte Werkzeugintelligenz, nicht nur starres Call-Muster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und Direktabruf unterscheiden lässt, wählt es das passende Tool sicher. Das spricht für brauchbare Orchestrierung in offenen Pipelines. Beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und dann abrufen lässt, bleibt es brauchbar, aber nicht deterministisch genug für Flows, die exakte Endpunkte erwarten. Das Hauptsignal ist daher klar: gute Wahl des Werkzeugtyps, schwächere Präzision bei der konkreten Ausführung. Kritisch bleibt, dass der Tool-Call insgesamt nicht durchgängig valide war. Das ist kein Totalausfall, aber ein Integrationsrisiko für MCP-Strecken, die strikte Protokolltreue verlangen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht verlässlich präzise genug. Die P2-Leistung von 66.67 zeigt, dass Sonnet 5 Ergebnisse meist sinnvoll zusammenführt, dabei jedoch merklich an Genauigkeit verliert, sobald mehrsprachige oder quellennahe Verdichtung gefragt ist. Das sieht man besonders bei Multilingual Search & Synthesis, wo die Recherche funktioniert, die Verdichtung auf Deutsch aber zu stark abstrahiert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, mit leichter Reserve. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen beantwortet werden, halluziniert es nicht. Das ist das wichtige Vertrauenssignal. P2=60 zeigt aber, dass es den beschafften Inhalt nicht maximal sauber in eine belastbare Antwort überführt.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Abruf prüft, erfindet Sonnet 5 keinen Ersatzinhalt. Es kommuniziert den Fehler statt fiktive Seitendaten zu liefern. Genau dieses Verhalten schützt Tool-Pipelines vor stillem Datenkorruptionsrisiko.

**Betriebsprofil**

Call 1: 1.74s. MCP-Latenz: 1.48s. Call 2: 11.44s. Total: 88.01s.  
Preis: $2.0/1M Input, $10.0/1M Output.  
Urteil: bei Einzelschritten schnell, im Gesamtrun lang. Preislich für Frontier moderat, gemessen an der ungleichmäßigen Synthese nicht günstig.

**Fazit & Empfehlung**

Geeignet für agentische MCP-Pipelines, in denen das Modell Werkzeuge auswählen, Web-Recherche anstoßen und Fehler sauber offenlegen soll. Nicht die erste Wahl für Compliance-nahe, mehrsprachige oder stark verdichtende Pipelines, in denen jede abgeleitete Formulierung quellentreu und reproduzierbar sein muss. Deploybar als Orchestrator mit enger Output-Kontrolle, Schema-Validierung und nachgelagerter Antwortprüfung. Ohne diese Leitplanken nicht als vertrauenswürdige Endinstanz.