**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:22:48


Bedingt deploy: GPT-5.5 zeigt starke Tool-Orientierung und keine Halluzinationsbefunde, aber der invalide Tool-Call und die nur mittlere Synthesetreue machen es für unüberwachte MCP-Pipelines noch nicht robust genug.

**Tool-Execution-Profil**

Bei der Tool-Ausführung wirkt das Modell nicht wie ein reiner Pattern-Follower, sondern wie ein System mit brauchbarer Werkzeugwahl. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Fetch unterscheiden soll, wählt es das passende Werkzeug sicher. Das spricht für situative Tool-Intelligenz. Auch bei EU License Research und Multilingual Search & Synthesis ruft es aktuelle Quellen ab, statt nur aus dem Vorwissen zu antworten.

Die Schwäche liegt nicht in der grundsätzlichen Entscheidung für Tools, sondern in der operativen Präzision. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen ableiten und anschließend abrufen soll, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Dass der Tool-Call insgesamt als nicht valide markiert ist, ist der zentrale Produktionsvorbehalt. Ohne Retry-Bedarf sieht das nicht nach einem bloßen Formatversagen aus, sondern nach einem einzelnen, aber realen Ausführungsfehler im Ablauf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung zeigt, dass GPT-5.5 gefundene Inhalte meist korrekt zusammenzieht, aber Details nicht konstant präzise hält. Das sieht man an HTTP Fetch & Extract, URL Construction & Fetch und Multilingual Search & Synthesis, wo die Recherche selbst funktioniert, die Verdichtung aber an Schärfe verliert. Für Assistenz-Workflows ist das tragbar. Für Compliance-, Vertrags- oder Policy-Pipelines ist es zu locker.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten auf aktuelle Lizenzrestriktionen prüft, bleibt das Modell auf der sicheren Seite. Kein Halluzinationssignal, kein erkennbares Ausweichen auf Trainingswissen. Das ist ein belastbares Vertrauenssignal, auch wenn die Antwortqualität dort in der Verdichtung nur mittel ausfällt.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit scheiternden Tool-Aufrufen prüft, reagiert GPT-5.5 produktionsfähig. Es erfindet keinen Seiteninhalt und kommuniziert den Fehlerzustand sauber. Genau dieses Verhalten braucht eine Tool-Pipeline: Fehler offenlegen, nicht kaschieren.

**Betriebsprofil**

Total 104.61s. Einzelaufrufe 2.28s und 13.66s. MCP-Latenz 1.50s. Langsam für den erzielten Qualitätskorridor. Preis $5.0 pro 1M Input und $30.0 pro 1M Output. Klar teuer.

**Fazit & Empfehlung**

Geeignet für recherchierende, mehrstufige MCP-Pipelines mit Human-in-the-Loop, wo gute Tool-Wahl wichtiger ist als perfekte Verdichtung. Ebenfalls sinnvoll für breit angelegte Produktiv- und Analyseflüsse mit Web-Zugriff. Nicht die richtige Wahl für vollautomatisierte Pipelines mit strikten Anforderungen an URL-Präzision, formale Tool-Validität und wortgetreue Ergebnisverdichtung. Für regulierte oder rechtsnahe Workflows nur mit nachgelagerter Validierung und strukturellen Guardrails einsetzen.