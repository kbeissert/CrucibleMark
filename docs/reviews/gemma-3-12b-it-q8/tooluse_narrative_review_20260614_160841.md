**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:08:41


Bedingt deploy, weil es Tools zuverlässig und protokollkonform nutzt, aber die Synthesetreue mit Combined 68.08 und erkannter Halluzination nicht hoch genug für vertrauenskritische Pipelines ist.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsseite klar belastbar. Tool-Calls sind valide, Retry war nicht erforderlich, und P1 liegt mit 90 auf einem produktionsfähigen Niveau. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis prüft, ob statt fetch ein Such-Tool nötig ist, erkennt es den richtigen Werkzeugtyp sicher und erreicht P1 100. Das spricht gegen bloßes Schema-Folgen und für echte Werkzeugwahl im Kontext.

Schwächer ist die Präzision beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetch ausführt. Mit P1 80 kommt es meist ans Ziel, aber nicht deterministisch genug für Pipelines, in denen URL-Bildung Teil der fachlichen Logik ist. Für MCP-Orchestrierung ist das insgesamt positiv: Das Modell versteht, wann es suchen muss, produziert formale Calls sauber und scheitert nicht am Protokoll.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 45.83 ist der klare Engpass. Besonders HTTP Fetch & Extract zeigt mit P2 15, dass strukturierte Fakten aus abgerufenen Inhalten nicht stabil genug in eine präzise Antwort überführt werden. Auch EU License Research und URL Construction & Fetch bleiben in der Verdichtung zu grob. Besser fällt Multilingual Search & Synthesis aus, aber nicht so stark, dass es den Gesamtbefund dreht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch prüft, bleibt es im beschafften Material. Content-Verification-State A und keine Halluzination sind ein gutes Signal. Gleichzeitig ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgibt, verliert die Infrastruktur ihre Prüfbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call prüft, reagiert das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler. P2 40 zeigt, dass die Formulierung der Fehlermeldung nicht besonders stark ist, aber das entscheidende Produktionskriterium erfüllt es: Es bleibt ehrlich über den Fehlschlag.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Umgebungen attraktiv. Leistung liegt nur 1.37 Punkte unter dem Fleet-Ø von 67.84. Für ein lokal laufendes Desktop-Modell ist das wettbewerbsfähig.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit klarer Tool-Führung, Suchschritten, Fehlertransparenz und menschlicher oder regelbasierter Endkontrolle. Nicht geeignet für Compliance-, Extraktions- oder Entscheidungsstrecken, in denen die Antwort selbst als verlässliche Verdichtung des Tool-Outputs gelten muss. Wer dieses Modell einsetzt, sollte es als sauberen Tool-Bediener behandeln, nicht als vertrauenswürdigen End-Synthesizer.