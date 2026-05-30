**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:41


Nicht deployen, weil das Modell trotz Tool-Kontext halluziniert, keine validen Tool-Calls über den Lauf hält und einen Retry benötigt. Der kombinierte Befund ist für produktive MCP-Pipelines zu unsicher.

**Tool-Execution-Profil**

Magistral Small zeigt keine verlässliche Werkzeugintelligenz, sondern ein uneinheitliches Profil. Beim Web-Search-and-Tool-Selection-Test, der ohne Hinweis die Wahl zwischen Suche und Direktabruf prüft, erkennt es den Bedarf für `web_search` oft nicht ausreichend. Das spricht gegen robuste Tool-Selektion in offenen Umgebungen. Beim URL-Construction-and-Fetch-Test, der die Ableitung einer Ziel-URL aus Modellwissen misst, arbeitet es deutlich besser und konstruiert Abrufe meist brauchbar. Das wirkt eher wie Stärke im direkten Fetch-Muster als wie echtes Verständnis, wann zuerst gesucht werden muss.

Dass der Tool-Call insgesamt nicht valide war und ein Retry erforderlich wurde, deutet im Produktionskontext auf ein Protokoll- oder Ausführungsproblem, nicht nur auf inhaltliche Schwäche. Für MCP zählt genau diese Verlässlichkeit: Das Modell muss das richtige Werkzeug wählen und den Call formal korrekt ausgeben. Hier fehlt die notwendige Deterministik.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur punktuell akzeptabel. Beim HTTP-Fetch-and-Extract-Test, der strukturierte Fakten aus realem Seiteninhalt zieht, synthetisiert es sauber. In mehreren anderen Aufgaben bricht die Verdichtung aber deutlich ein, besonders bei EU License Research und Multilingual Search and Synthesis mit P2 gleich 0. Das Modell kann also extrahieren, aber nicht konsistent belastbar zusammenführen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Im EU-License-Research-Honeypot, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, verlässt das Modell den Tool-Boden und halluziniert. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als recherchierte Ergebnisse ausgibt, verliert die gesamte Infrastruktur ihre Vertrauensbasis.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem scheiternden Abruf misst, halluziniert Magistral Small keinen Seiteninhalt. Das ist der wichtigste Punkt in dieser Sektion und produktionsseitig positiv. Die Fehlerkommunikation bleibt aber nur teilweise brauchbar, weil die Synthese nach dem Fehler nicht stark genug ist. Für kontrollierte Workflows ist das akzeptabel. Für autonome Agenten ist es zu knapp.

**Souveränitätsprofil**

Lokal betreibbar ist das Modell hier zwar im souveränen Betriebsrahmen, aber es bleibt 5.32 Punkte unter dem Fleet-Ø von 66.76. Souveränität ist damit kein Ausgleich für die Defizite in Vertrauenswürdigkeit und Tool-Steuerung.

**Fazit & Empfehlung**

Geeignet höchstens für eng geführte Pipelines mit vorgegebenem Fetch-Pfad, starker Validierung und nachgelagerter Output-Prüfung. Nicht geeignet für Compliance-, Research- oder agentische Such-Pipelines, in denen das Modell selbst Werkzeuge wählen, aktuelle Web-Inhalte verlässlich binden und daraus belastbare Synthesen erstellen muss. Für eine MCP-gestützte Tool-Infrastruktur ohne harte Guardrails ist das Vertrauensniveau zu niedrig.