**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:23:09


Bedingt deploy, weil das Modell Tools oft zweckrichtig einsetzt, aber die Synthese nach dem Abruf zu wenig belastbar ist und zudem kein durchgängig valides Tool-Call-Verhalten zeigt. Der kombinierte Befund ist gut genug für assistierte Pipelines, nicht für hochvertrauenswürdige Automationsstrecken.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Beim Test **Web Search & Tool Selection**, der prüft, ob ohne expliziten Hinweis Suche statt Direktabruf nötig ist, wählt es das passende Tool zuverlässig. Das spricht für brauchbare Orchestrierungsintuition in offenen MCP-Setups.

Schwächer ist die Präzision beim Test **URL Construction & Fetch**, der die korrekte Ableitung einer Ziel-URL und den anschließenden Abruf misst. Dort ist die Ausführung brauchbar, aber nicht deterministisch genug für Pipelines, in denen URL-Bildung fehlerfrei sitzen muss. Dazu passt der globale Befund, dass der Tool-Call nicht durchgehend valide war. Das ist kein Planungsproblem, sondern ein Protokoll- und Ausführungsrisiko an der Schnittstelle zum Tooling. Positiv ist, dass kein Retry erforderlich war. Das Modell scheitert also nicht an grundlegendem MCP-Verständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung zeigt, dass das Modell gefundene Inhalte oft nur teilweise in belastbare, präzise Zusammenfassungen überführt. Das sieht man besonders bei **EU License Research**, wo aktuelle Lizenzrestriktionen aus Web-Quellen zusammengeführt werden müssen, und bei **Multilingual Search & Synthesis**, wo Recherche sprachübergreifend sauber verdichtet werden soll. Für produktive Pipelines heißt das: Der Abruf ist häufiger stärker als die eigentliche Nutzantwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der genau dieses Ausweichen prüft, wurde keine Halluzination erkannt. Das ist das wichtigste Vertrauenssignal des Laufs. Trotz schwacher Verdichtung erfindet das Modell hier keine aktuellen Compliance-Fakten aus dem Parametergedächtnis.

**Fehlerresilienz**

Beim Test **Tool Failure Handling (404)**, der transparentes Verhalten bei fehlschlagendem Abruf prüft, bleibt das Modell akzeptabel. Es halluziniert trotz 404 keinen Seiteninhalt. Die Antwortqualität ist dabei nicht stark, aber für Produktion ist der entscheidende Punkt erfüllt: Es markiert den Fehlerpfad, statt Ersatzinhalt als Tool-Ergebnis auszugeben.

**Souveränitätsprofil**

Lokal gut betreibbar, aber nicht klar fleet-kompetitiv. Das Modell liegt 1.22 Punkte unter dem Fleet-Ø von 66.87. Für lokale, souveräne Deployments ist das noch im brauchbaren Bereich, aber kein Leistungsargument an sich.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Assistenzpipelines mit Mensch-im-Loop, in denen Tool-Auswahl zählt und Ausgaben nachgeprüft werden. Nicht geeignet für Compliance-, Policy- oder Fully-Automated-Workflows, in denen die Antwort nach dem Tool-Call ohne Nachkontrolle direkt weiterverarbeitet wird. Wer es einsetzt, sollte strikte Output-Validierung, Quellzitat-Pflicht und Downstream-Checks auf Zusammenfassungsfehler vorsehen.