**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:17:20


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgängig valide waren und die Synthesequalität für vertrauenssensitive Pipelines nur knapp ausreichend ausfällt.

**Tool-Execution-Profil**

Qwen3.8-Flash zeigt echte Werkzeugwahl-Kompetenz statt eines starren Fetch-Musters. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sicher. Das spricht für brauchbare Orchestrierungslogik in offenen MCP-Flows. Beim URL-Construction-Test, der die Ziel-URL aus internem Wissen ableiten und dann korrekt abrufen lässt, bleibt es dagegen nur ordentlich. Die Konstruktion funktioniert, aber nicht präzise genug für deterministische Pipelines mit harter Erfolgsquote. P1 insgesamt ist mit 90 stark, doch das Signal „Tool-Call valide: false“ verhindert ein uneingeschränktes Freigabevertrauen. Das ist kein Verständnisproblem, sondern ein Protokoll- und Ausführungsrisiko an der Schnittstelle.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. Die P2-Leistung von 62.5 zeigt, dass Qwen3.8-Flash Rechercheergebnisse meist in eine brauchbare Antwort überführt, aber nicht konsistent präzise genug verdichtet. Das sieht man auch in EU License Research und Tool Failure Handling (404), wo die Schlussfassung hinter der eigentlichen Tool-Nutzung zurückbleibt. Für Architekturen, in denen das Modell primär sammelt und ein nachgelagerter Validator die Endfassung prüft, ist das akzeptabel. Für direkt nutzbare Berichts- oder Compliance-Ausgaben ist es zu knapp.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Modell auf der sicheren Seite. Keine Halluzination, kein Ausweichen auf vortrainiertes Wissen. Das ist das wichtigste Vertrauenssignal in diesem Lauf.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Abruf gegen erfundenen Ersatzinhalt prüft, reagiert Qwen3.8-Flash akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler. Die Kommunikation ist nicht besonders stark verdichtet, aber produktionsfähig. Für MCP-Pipelines zählt hier vor allem: Es erfindet keinen erfolgreichen Fetch, wenn keiner stattgefunden hat.

**Betriebsprofil**

Total 109.26s. Erste Tool-Phase schnell: 2.40s bei 1.27s MCP-Latenz. Zweiter Call 14.54s. Insgesamt langsam für die erzielte Synthesequalität. Kosten pro Run: local. Preisblatt: $0.16/1M Input, $0.47/1M Output. Gemessen an der Tool-Leistung günstig, gemessen an der Endverdichtung nur solide.

**Fazit & Empfehlung**

Geeignet für agentische MCP-Pipelines, in denen das Modell Werkzeuge auswählen, Recherche anstoßen und Fehler sauber offenlegen soll. Nicht die erste Wahl für Pipelines, die aus Tool-Ergebnissen ohne weitere Kontrolle belastbare Endfassungen erzeugen müssen, etwa Compliance-Summaries, Entscheidungsvermerke oder kundenseitige Reports. Deploy als Orchestrator mit nachgelagerter Validierung und striktem Tool-Call-Monitoring. Nicht als unbeaufsichtigter Synthese-Endpunkt.