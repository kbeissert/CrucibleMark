**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:49


Bedingt deploy, weil die Tool-Aufrufe überwiegend valide sind, das Modell aber mit erkannter Halluzination und nur moderater Gesamtsicherheit kein uneingeschränkt vertrauenswürdiger Tool-Operator ist.

**Tool-Execution-Profil**

Grok 4 (Non-Reasoning) arbeitet auf der Ausführungsebene solide. Die Tool-Calls sind valide, und P1 von 82.50 zeigt, dass das Modell MCP-konforme Aufrufe in der Regel korrekt produziert. Besonders stark ist es dort, wo Werkzeugwahl aktiv gefordert ist: Beim Web-Search-&-Tool-Selection-Test erkennt es ohne expliziten Hinweis, dass statt fetch ein Such-Tool nötig ist, was für echte Orchestrierung spricht und nicht nur für starres Musterverhalten. Auch beim URL-Construction-Test leitet es Ziel-URLs meist brauchbar ab und führt fetch anschließend korrekt aus, wenn auch nicht deterministisch genug für fragile Pipelines.

Das erforderliche Retry wirkt hier eher wie ein Robustheitsproblem im Ablauf als wie ein grundsätzliches Verständnisproblem. Die hohe Tool-Selection-Leistung bei gleichzeitig notwendigem Retry deutet darauf hin, dass die Planungsentscheidung meist stimmt, die Erstantwort aber nicht immer im erwarteten Format oder mit ausreichender Präzision landet.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 54.17 ist der eigentliche Bremsklotz dieses Modells. Es kann extrahierte Fakten sauber weiterreichen, wie der HTTP-Fetch-&-Extract-Test und der URL-Construction-&-Fetch-Test zeigen. Sobald die Aufgabe aber aus mehreren Quellen oder Sprachräumen zu einer belastbaren Endaussage verdichtet werden muss, bricht die Qualität sichtbar ein. Das ist für MCP-Pipelines relevant, weil viele Produktionspfade nicht an der Tool-Nutzung scheitern, sondern an der letzten Meile der Zusammenführung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im EU-License-Research-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen gezogen werden, fällt das Modell mit P2=15 und erkannter Halluzination durch. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell recherchierte Compliance-Inhalte durch Trainingswissen ersetzt, verliert die gesamte Tool-Infrastruktur ihren Nachweiswert.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell produktionstauglich. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt misst, kommuniziert es den Fehlschlag sauber und halluziniert keinen Seiteninhalt. Das ist ein starkes Signal. Fehler werden offengelegt statt verdeckt.

**Betriebsprofil**

Call 1: 5.44s. MCP-Latenz: 1.18s. Call 2: 3.69s. Total: 61.88s.  
Kosten pro Run: 0.029169.  
Direkte Einordnung: nicht schnell, aber auch nicht extrem teuer. Für die gezeigte Leistung ist die Laufzeit eher lang und die Kosten nur dann vertretbar, wenn man die Synthese extern absichert.

**Fazit & Empfehlung**

Geeignet für Pipelines, in denen das Modell Tools auswählen, Inhalte abrufen und Fehler transparent melden soll, während ein nachgelagerter Verifier oder regelbasierter Aggregator die Schlussfassung kontrolliert. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere High-Trust-Pipelines, in denen die Endantwort strikt an Tool-Belege gebunden bleiben muss. Wer Grok 4 (Non-Reasoning) einsetzt, sollte es als Tool-Bediener mit Aufsicht verwenden, nicht als letzte Instanz für belastbare Synthese.