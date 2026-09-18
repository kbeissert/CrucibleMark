**Deployment-Urteil**

> **Erstellt am:** 18.09.2026, 09:33:31


Bedingt deploy, weil die Ausführung von Tools meist tragfähig ist, aber die Tool-Call-Validität nicht durchgängig sitzt und die Gesamtsynthese für autonome MCP-Pipelines nicht stabil genug verdichtet.

**Tool-Execution-Profil**

Occamy 1.0 35B-A3B zeigt brauchbare operative Tool-Nutzung, aber keine verlässliche Werkzeugintelligenz. Das starke Signal kommt aus klar geführten Abrufpfaden: Beim Test zu HTTP Fetch & Extract extrahiert es strukturierte Fakten sauber, und beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen prüft, arbeitet es mit solider Präzision. Auch die mehrsprachige Recherche startet operativ stark.

Der Schwachpunkt liegt bei der Auswahl des richtigen Werkzeugs ohne Hint. Beim Test Web Search & Tool Selection, der prüft, ob statt fetch zuerst web_search nötig ist, fällt es deutlich ab. Das spricht gegen flexible Tool-Planung und eher für ein Muster: Wenn eine URL oder ein direkter Abrufpfad plausibel erscheint, folgt das Modell diesem Pfad, statt den Informationsbedarf erst korrekt zu klassifizieren. Für MCP-Orchestrierung heißt das: in eng gerahmten Flows brauchbar, in offenen Recherchepfaden mit mehreren möglichen Tools riskant. Dass der Tool-Call nicht durchgängig valide war, verschärft genau diesen Punkt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung zeigt ein konsistentes Muster: Solide bei direkten Extraktionsaufgaben, aber schwach, sobald mehrere Quellen, Sprachwechsel oder implizite Schlussfolgerungen zusammengeführt werden müssen. Besonders auffällig ist die Diskrepanz zwischen perfekter operativer Ausführung bei Multilingual Search & Synthesis und deutlich schwächerer Verdichtung auf Deutsch. Das Modell findet Material, komprimiert es aber nicht präzise genug für belastbare Entscheidungsoutputs.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja, und das ist der wichtigste positive Befund. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, halluziniert Occamy nicht. Das Vertrauensfundament ist damit vorhanden: Es erfindet keine Compliance-Fakten, auch wenn die Zusammenfassung nur mittelstark ausfällt.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell produktionsfähig. Im 404-Test, der transparentes Fehlermanagement statt erfundenem Seiteninhalt misst, kommuniziert es den Fehlschlag sauber und halluziniert keinen Ersatzinhalt. Das ist für produktive Pipelines akzeptabel. Ein System kann mit klaren Fehlern umgehen; es kann nicht mit erfundenen Ergebnissen umgehen.

**Souveränitätsprofil**

Lokal betreibbar und trotz local_sovereign-Setup knapp fleet-kompetitiv. Mit 68.71 Combined liegt es 0.68 Punkte über dem Fleet-Ø von 68.03.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Pipelines mit vorstrukturierten Tool-Pfaden, klaren Fetch-Schritten und menschlicher Nachkontrolle auf der Ergebnisebene. Nicht geeignet als autonomer Recherche-Orchestrator, der selbst entscheiden muss, ob gesucht, abgerufen oder umgeplant werden soll. Wenn Sie Tool-Auswahl und Call-Schema hart vorgeben, kann Occamy ein nützlicher lokaler Worker sein. Wenn das Modell die Infrastruktur eigenständig navigieren soll, bleibt das Risiko zu hoch.