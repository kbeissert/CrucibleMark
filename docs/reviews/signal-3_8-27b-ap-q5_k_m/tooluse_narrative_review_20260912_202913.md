**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:29:13


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Vertrauensbasis an einem zentralen Punkt bricht: valide Tool-Calls wurden nicht durchgängig erreicht und die Synthese bleibt bei wissenskritischen Web-Aufgaben zu unsauber für unbeaufsichtigte Pipelines.

**Tool-Execution-Profil**

Signal 3.8 27B zeigt echte Werkzeugintelligenz, nicht nur starres Abarbeiten. Beim Web-Search-&-Tool-Selection-Test, der prüft ob ohne Hinweis search statt fetch gewählt wird, erreicht es volle Ausführungssicherheit. Das spricht dafür, dass es den Informationsbedarf vor dem Tool-Call erkennt. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableiten soll, ist es brauchbar, aber nicht deterministisch genug. Genau dort liegt die operative Grenze: Das Modell weiß oft, welches Werkzeug nötig ist, produziert aber nicht immer einen sauber validen Call. Für MCP-Pipelines heißt das: gute Planungsfähigkeit, aber ein Wrapper sollte URL-Normalisierung, Argument-Schema-Prüfung und Call-Validation erzwingen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich, nicht belastbar. Die P2-Leistung von 66.67 zeigt ein Muster: HTTP Fetch & Extract, Tool Failure Handling (404) und Multilingual Search & Synthesis sind brauchbar, aber die Verdichtung ist nicht konstant präzise. Für reine Retrieval-Zusammenfassungen reicht das oft. Für Compliance-, Policy- oder Vertragsoberflächen reicht es nicht ohne nachgelagerte Prüfung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Genau hier ist das Misstrauenssignal. Beim EU-License-Research-Honeypot, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training kommen, fällt die Synthese mit P2=20 deutlich ab. Formal wurde keine Halluzination markiert. Praktisch zeigt der Test aber, dass das Modell die Quelle nicht streng genug bindet. Für produktive Tool-Infrastruktur ist das ein Vertrauensproblem, auch ohne harte Halluzinationsflagge.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, reagiert Signal 3.8 27B akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler hinreichend offen. Das ist produktionsfähig. Scheiternde Aufrufe gefährden hier nicht automatisch die Faktentreue.

**Souveränitätsprofil**

Voll lokal betreibbar, Apache-2.0-lizenziert und damit für souveräne Deployments attraktiv. Ein Souveränitätsabzug ist nicht ausgewiesen; der Referenzrahmen bleibt n/a-Punkte unter dem Fleet-Ø von 67.75. Die lokale Betriebsform ist also kein erkennbarer Leistungsnachteil in diesem Testbild.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und Assistenzpipelines, in denen Tool-Wahl wichtig ist und ein nachgeschalteter Validator die Calls sowie die Ergebnisbindung absichert. Nicht geeignet als unbeaufsichtigter Synthese-Endpunkt für Compliance, Lizenzprüfung oder andere aktuelle Web-Fakten mit hohem Haftungsdruck. Wer lokal und offen deployen will, bekommt ein starkes Tool-Use-Grundmodell. Wer strikte Quellentreue im letzten Antwortschritt braucht, sollte es nur mit Guardrails und Verifikation einsetzen.