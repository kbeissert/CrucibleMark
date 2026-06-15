**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:09:34


Bedingt deployen: Das Modell ist für MCP-gestützte Tool-Pipelines grundsätzlich vertrauenswürdig, weil es valide Tool-Calls erzeugt, keine Halluzination im Lauf zeigte und mit 73,0 kombiniert klar im brauchbaren Bereich liegt, aber seine Synthese bleibt zu oft zu grob für präzise Ausgabestrecken.

**Tool-Execution-Profil**

Die operative Seite ist die klare Stärke. Mit P1 90 wählt das Modell Werkzeuge meist richtig und bleibt MCP-protokollkonform. Besonders wichtig: Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden soll, traf es die richtige Wahl durchgehend. Das spricht für echte Werkzeugwahl statt starrem Fetch-Muster.

Weniger sicher ist es beim URL-Construction-and-Fetch-Test, der die korrekte Ziel-URL aus vorhandenem Wissen ableitet. Dort ist die Ausführung brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen direkt auf eine kanonische URL schließen müssen. Es arbeitet also intelligent bei der Tool-Auswahl, aber nicht präzise genug bei der letzten Meile der Adresskonstruktion. Positiv bleibt: Kein Retry war nötig. Das ist ein Verständnis- und kein Formatproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 56,67 zeigt, dass das Modell extrahierte Inhalte oft korrekt aufnimmt, sie aber nicht stabil in eine dichte, entscheidungsreife Antwort überführt. Das sieht man auch im Asset-Bild: EU License Research und Multilingual Search and Synthesis erreichen trotz starker Tool-Nutzung nur 40 bei der Verdichtung. Für Recherche- oder Routing-Schritte reicht das. Für Compliance- oder Executive-Summaries nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen stammen, blieb es auf der sicheren Seite. Content-Verification-State A bei gleichzeitig keiner erkannten Halluzination ist das wichtigere Signal als die schwache Verdichtung. Das Modell erfindet hier nichts, aber es komprimiert die Befunde nicht scharf genug.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlschlagenden Tool-Calls prüft, reagierte das Modell akzeptabel. Es halluzinierte keinen Ersatzinhalt, sondern blieb bei einer nachvollziehbaren Fehlerlage. P2 60 ist kein Qualitätsausreißer nach oben, aber für Produktion ausreichend, weil die zentrale Sicherheitsanforderung erfüllt ist: kein erfundener Seiteninhalt trotz Fehler.

**Souveränitätsprofil**

Lokal betreibbar und damit für sensible Umgebungen attraktiv. Zugleich bleibt es fleet-kompetitiv, aber nicht führend: 1,37 Punkte unter dem Fleet-Ø von 67,84. Das ist ein kleiner Abschlag für deutlich bessere Datenhoheit. Die restriktive Gemma-Lizenz bleibt jedoch ein Governance-Thema.

**Fazit & Empfehlung**

Geeignet für lokale Recherche-, Tool-Routing- und Retrieval-Pipelines, in denen der eigentliche Wahrheitsanker im Tool liegt und ein nachgelagerter Schritt die Endverdichtung übernehmen kann. Nicht erste Wahl für Pipelines, die vom Modell selbst belastbare, knappe Entscheidungssynthesen oder URL-genaue Aktionsschritte erwarten. Als souveräne Tool-Ausführungsschicht ist es solide. Als letzter redaktioneller Knoten ist es zu unpräzise.