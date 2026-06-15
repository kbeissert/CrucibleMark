**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:19:09


Bedingt deploy, weil die Tool-Ausführung produktionsreif wirkt, die Synthese aber zu oft an Präzision verliert. Mit validen Tool-Calls, keiner Halluzination und einem Combined Score von 74.17 ist die Infrastrukturverträglichkeit gegeben, nicht jedoch durchgehend die Verdichtungstreue.

**Tool-Execution-Profil**

Gemini 3.1 Pro Preview zeigt ein starkes Tool-Profil. Es wählt Werkzeuge nicht mechanisch, sondern erkennt im Web Search & Tool Selection-Test ohne expliziten Hinweis korrekt, dass erst gesucht und nicht direkt gefetcht werden muss. Das spricht für echte Werkzeugwahl statt eines starren Fetch-zuerst-Musters. Auch die MCP-Seite ist sauber: Tool-Call valide, kein Retry erforderlich, also kein Format- oder Protokollproblem.

Schwächer ist die zweite Hälfte der Kette. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableiten und dann abrufen lässt, arbeitet es brauchbar, aber nicht deterministisch genug für Pipelines, die aus einer Modellantwort direkt auf exakte Endpunkte bauen. Das Muster ist klar: gute Orchestrierung, etwas weniger Präzision beim letzten operativen Schritt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Der P2-Wert von 60 zeigt, dass das Modell vorhandene Tool-Inhalte nicht zuverlässig in präzise, belastbare Endantworten überführt. Besonders sichtbar wird das bei EU License Research und Multilingual Search & Synthesis, wo die Recherche gelingt, die Verdichtung aber zu grob bleibt. Für Architekturen mit Human Review ist das akzeptabel. Für automatische Downstream-Entscheidungen ist es zu knapp.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal deutlich besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Training kommen, halluziniert es nicht. Content-Verification-State A bei P2 40 heißt: Das Problem liegt eher in der Aufbereitung als in erfundenen Fakten. Für Compliance-nahe Tool-Pipelines ist das ein wichtiger Unterschied.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call prüft, bleibt das Modell sauber. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler nachvollziehbar. Das ist für Produktion akzeptabel. Ein Modell, das bei Ausfällen Ersatzfakten erzeugt, wäre sofort disqualifiziert. Dieser Befund liegt hier nicht vor.

**Betriebsprofil**

Call 1: 4.09s. Call 2: 13.26s. MCP-Latenz: 0.71s. Total pro Run: 108.34s.  
Kosten pro Run: $0.034276.  
Urteil: Tool-seitig reaktionsfähig, aber als Gesamtlauf langsam; kostenmäßig moderat, gemessen an der nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und multimodale Assistenzpipelines, in denen Tool-Wahl wichtiger ist als perfekte Endverdichtung und in denen eine Validierungs- oder Review-Stufe existiert. Nicht die erste Wahl für Compliance-, Policy- oder Decisioning-Pipelines, die aus Tool-Ergebnissen unmittelbar präzise Abschlussantworten generieren müssen. Wenn Sie es einsetzen, dann als starkes Orchestrierungsmodell mit nachgelagerter Kontrolle, nicht als letzte autoritative Syntheseschicht.