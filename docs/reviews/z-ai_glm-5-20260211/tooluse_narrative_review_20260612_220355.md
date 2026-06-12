**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:03:55


Bedingt deploy, weil GLM-5 die Tool-Infrastruktur zuverlässig ansteuert und valide MCP-Calls erzeugt, aber die Synthesequalität mit Halluzinationssignal für produktive High-Trust-Pipelines nicht stabil genug ist.

**Tool-Execution-Profil**

GLM-5 ist auf der Ausführungsebene klar produktionsnah. Der Tool-Call war valide, ein Retry war nicht nötig, und P1 von 90 zeigt, dass das Modell MCP-konform arbeitet. Besonders wichtig: Beim Web-Search-&-Tool-Selection-Test erkennt es ohne expliziten Hinweis, dass erst gesucht und nicht direkt gefetcht werden muss. Das spricht für echte Werkzeugwahl statt starrem Fetch-Muster. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt, bleibt es brauchbar, aber weniger präzise. Genau dort sieht man die Grenze: Es plant den richtigen Zugriffspfad, ist aber nicht in jeder Ableitung deterministisch genug für fragile Pipelines.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. P2 von 59.17 ist der klare Schwachpunkt dieses Laufs. In HTTP Fetch & Extract und Tool Failure Handling (404), also bei klaren Einzeldokumenten mit strukturierter Extraktion, arbeitet es noch sauber. Schwächer wird es, sobald mehrere Quellen oder Sprachgrenzen zusammengeführt werden müssen. Beim Multilingual-Search-&-Synthesis-Test sinkt die Verdichtung deutlich. Dasselbe gilt für Web Search & Tool Selection auf der Antwortseite: Das richtige Tool wird gewählt, aber die nachgelagerte Zusammenfassung verliert Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellgedächtnis beantwortet werden, bleibt GLM-5 im Ergebnisraum der Tools. Das ist ein starkes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: In einer Tool-Pipeline genügt schon ein einzelner erfundener Fakt, um den Vertrauenskern der gesamten Infrastruktur zu beschädigen.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem gescheiterten Tool-Aufruf statt erfundenem Seiteninhalt prüft, reagiert GLM-5 akzeptabel. Es halluziniert trotz Fehler keinen Ersatzinhalt. Das ist für Produktion wichtig, weil es Fehler sichtbar macht, statt sie mit plausibel klingendem Text zu verdecken.

**Betriebsprofil**

Total 211.44s. Call 1 6.52s. Call 2 27.51s. MCP-Latenz 1.21s. Für die erreichte Qualität langsam. Kosten/Run: local.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit Tool-First-Architektur, in denen Tool-Wahl, Ausführung und Fehleroffenheit wichtiger sind als perfekte Verdichtung. Nicht die erste Wahl für Compliance, mehrsprachige Recherche-Synthese oder Executive Summaries ohne nachgelagerte Verifikation. Deploybar ist es dort, wo ein zweiter Prüfschritt die finale Antwort absichert und die Tools die eigentliche Wahrheitsquelle bleiben.