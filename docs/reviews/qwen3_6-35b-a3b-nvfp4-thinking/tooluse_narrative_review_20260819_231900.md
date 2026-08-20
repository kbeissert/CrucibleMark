**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:19:00


Bedingt deploy: Das Modell ist für Tool-Ausführung grundsätzlich brauchbar, aber die Kombination aus nur mittlerer Synthesetreue, ungültigem Tool-Call und einem Combined-Score von 76.62 reicht nicht für unbewachte Produktionspipelines.

**Tool-Execution-Profil**

Qwen 3.6 35B-A3B zeigt echte Werkzeugintelligenz, aber keine durchgängig saubere Protokolldisziplin. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis erst gesucht statt direkt gefetcht werden muss, erkennt es die richtige Werkzeugklasse sehr zuverlässig. Das spricht gegen starres Musterverhalten. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL mit anschließendem Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Der Kernbefund ist daher klar: Es wählt Tools meist sinnvoll, produziert aber nicht immer valide MCP-konforme Aufrufe. Dass kein Retry nötig war, deutet eher auf inkonsistente Call-Form als auf ein Verständnisproblem im Aufgabenablauf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung von 56.67 zeigt, dass Qwen gefundene Inhalte oft korrekt zusammenführt, aber Präzision, Priorisierung und Verdichtung nicht stabil genug hält. Das sieht man auch an EU License Research: korrekte Tool-Nutzung, aber schwache Endverdichtung. Dagegen sind HTTP Fetch & Extract sowie Tool Failure Handling (404) in der Zusammenfassung deutlich sauberer.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch prüft, halluziniert es nicht. Das ist der wichtige Sicherheitsbefund. Der schwache P2-Wert von 40 ist deshalb eher ein Verdichtungs- als ein Vertrauensproblem. Für Compliance-nahe Abläufe ist das besser als erfundene Aktualität, aber noch kein Freifahrtschein.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit gescheiterten Tool-Calls statt erfundenem Ersatzinhalt misst, reagiert das Modell produktionsgerecht. Es halluziniert trotz Fehler keinen Seiteninhalt und kommuniziert den Ausfall ausreichend offen. Das ist für reale MCP-Pipelines ein starkes Signal, weil ein Tool-Fehler die Antwortqualität senken darf, aber nicht die Tatsachengrundlage zerstören darf.

**Betriebsprofil**

Total 226.16s pro Run. Call 1: 9.00s. MCP-Latenz: 1.19s. Call 2: 27.50s. Lokal betrieben, daher keine API-Kosten. Für die gezeigte Leistung klar langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche-, Retrieval- und Assistenzpipelines mit menschlicher Abnahme oder nachgelagerter Validierung. Besonders brauchbar dort, wo Tool-Ausfälle sauber behandelt werden müssen und lokale Gewichte wichtiger sind als maximale Antwortschärfe. Nicht die richtige Wahl für vollautomatische Compliance-, Policy- oder Entscheidungsstrecken, in denen jeder Tool-Call formal valide sein und jede Synthese eng am Tool-Output bleiben muss.