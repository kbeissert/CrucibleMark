**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:02:33


Bedingt deploy, weil die Tool-Ausführung brauchbar ist, aber die Synthesetreue zu instabil bleibt und der Tool-Call im Lauf nicht durchgängig valide war. Der Combined-Score von 63.67 bestätigt genau dieses Bild: ein arbeitsfähiges Modell mit klaren Grenzen für produktive Tool-Pipelines.

**Tool-Execution-Profil**

Qwen3.6 27B Instruct zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der ohne Hinweis die Wahl zwischen Suche und direktem Abruf prüft, traf es die richtige Entscheidung konsequent. Das spricht für agentische Grundkompetenz in offenen Pipelines. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es gut, aber nicht deterministisch genug. P1 80 ist produktionsfähig, aber nicht robust genug für Flows, in denen schon kleine URL-Fehler den Lauf kippen. Kritisch ist, dass der Tool-Call insgesamt nicht valide war. Das ist kein Totalausfall, aber ein Protokollrisiko. Positiv: Es brauchte keinen Retry, also eher kein reines Formatproblem, sondern punktuelle Unsicherheit in der Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung von 56.67 zeigt, dass es gefundene Inhalte oft brauchbar zusammenzieht, aber Details nicht stabil genug konserviert. Das sieht man auch an EU License Research mit P2 20 und an mehreren Aufgaben, die bei der Ausführung stark, in der Verdichtung aber nur durchschnittlich enden. Für Pipelines, die aus Tool-Output belastbare Entscheidungstexte erzeugen sollen, ist das zu wenig Reserve.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten gegen aktuelle Web-Quellen prüft, wurde keine Halluzination erkannt. Das ist der wichtigste Entlastungspunkt dieses Modells. Trotzdem ist das Vertrauensurteil nicht stark, weil die Antwortqualität dort sehr schwach war. Es erfindet hier nicht, aber es verwertet die recherchierte Evidenz auch nicht sicher genug.

**Fehlerresilienz**

Beim 404-Test, der prüft, ob ein Modell Tool-Fehler offen meldet statt Seiteninhalt zu erfinden, reagierte Qwen3.6 27B Instruct akzeptabel. Es halluzinierte trotz Fehler keinen Ersatzinhalt. P2 60 ist keine starke Fehlerdiagnostik, aber transparente Fehlerkommunikation reicht für Produktion aus. Für MCP-Pipelines ist das ein klarer Pluspunkt.

**Betriebsprofil**

Total 137.84s. Call 1 3.84s. MCP-Latenz 0.82s. Call 2 18.31s. Lokal betrieben, daher direkte Run-Kosten ohne API-Gebühr. Gemessen an der Leistung ist das langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Orchestrierungs-Pipelines, in denen Tool-Auswahl wichtiger ist als perfekte Verdichtung und ein nachgelagerter Prüfschritt die Antwort absichert. Nicht geeignet für Compliance-, Policy- oder Executive-Summary-Flows, in denen Tool-Ergebnisse präzise und vollständig verdichtet werden müssen. Wenn Sie es einsetzen, dann als Tool-using worker mit enger Ausgabevalidierung, nicht als letzte Instanz der Synthese.