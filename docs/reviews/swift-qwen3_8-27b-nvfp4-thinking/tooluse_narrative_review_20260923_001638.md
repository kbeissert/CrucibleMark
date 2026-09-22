**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:16:38


Bedingt deploy, weil die Tool-Nutzung stark ist, aber ein invalider Tool-Call und ein gesetzter Halluzinations-Flag das Vertrauen in produktive MCP-Pipelines begrenzen.

**Tool-Execution-Profil**

Swift Qwen 3.8 27B zeigt echte Werkzeugintelligenz, nicht nur starres Fetch-Verhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt das Modell den Bedarf für web_search sauber und erreicht volle Ausführungssicherheit. Das spricht für brauchbare Planung in offenen Retrieval-Szenarien. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt, bleibt es brauchbar, aber nicht deterministisch genug für sensible Pipelines. P1 80 heißt hier: funktional, aber nicht robust. Kritisch ist weniger die Auswahl als die Protokolltreue. Der globale Befund „Tool-Call valide: false“ bedeutet, dass mindestens ein Aufruf nicht sauber MCP-konform war. Da kein Retry nötig war, wirkt das nicht wie ein wiederkehrendes Formatproblem, sondern wie punktuelle Unsauberkeit in der Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung von 59.17 liegt deutlich unter der Ausführungsstärke. Das Modell extrahiert Web-Inhalte im Test HTTP Fetch & Extract sehr gut, verdichtet aber in Such- und Rechercheaufgaben zu unpräzise. Besonders sichtbar ist das bei Web Search & Tool Selection, wo die Werkzeugwahl richtig ist, die Zusammenführung der Funde aber schwach bleibt. Für Pipelines, in denen nicht nur abgerufen, sondern belastbar zusammengefasst werden muss, ist das die eigentliche Grenze.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, halluziniert es nicht, aber es bleibt auch nicht eng genug an den abgerufenen Befunden. P2 40 ohne Halluzination ist kein Entwarnungssignal, sondern ein Vertrauensdefizit. Der gesetzte Halluzinations-Flag ist deshalb als Sicherheitsrisiko zu lesen: Sobald ein Modell erfundene Fakten als Tool-Ergebnis rahmt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Abruf misst, erfindet Swift Qwen 3.8 27B keinen Seiteninhalt. Das ist produktionsrelevant positiv. P2 60 zeigt keine elegante Fehlerbehandlung, aber die Reaktion bleibt akzeptabel: lieber unvollständig als erfunden.

**Betriebsprofil**

Call 1: 7.30s. MCP-Latenz: 1.05s. Call 2: 53.41s. Total: 370.58s.  
Lokal und ohne API-Kosten. Für die gelieferte Qualität zu langsam. Für Batch- oder Backoffice-Jobs vertretbar, für interaktive Tool-Pipelines grenzwertig.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Abrufpipelines mit menschlicher Nachkontrolle, besonders wenn Souveränität und Tool-Ausführung wichtiger sind als präzise Verdichtung. Nicht geeignet für Compliance-, Policy- oder Entscheidungsstrecken, in denen die Antwort selbst als verlässliches Endprodukt dient. Wenn Sie es einsetzen, dann als Tool-Operator mit nachgelagerter Validierung, nicht als autonomes Synthese-Modell.