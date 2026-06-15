**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:14:28


Bedingt deploy, weil die Tool-Calls formal valide sind, der Gesamteindruck mit 42.33 aber klar zu schwach für vertrauensintensive Tool-Pipelines ist und ein Halluzinationssignal im Lauf als Sicherheitsrisiko stehen bleibt.

**Tool-Execution-Profil**

Das Modell kann MCP-konform aufrufen. Tool-Call valide: true, Retry war nicht nötig. Das spricht für ein Format, das in eine bestehende Infrastruktur integrierbar ist. Das eigentliche Problem liegt nicht im Protokoll, sondern in der Werkzeugwahl und in der operativen Präzision.

Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es nur P1 40. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, liegt es ebenfalls bei P1 40. Das zeigt keine belastbare Tool-Intelligenz. Das Modell folgt eher einem unsicheren Grundmuster, statt den Informationsbedarf sauber in Such- oder Abrufschritte zu zerlegen. Positiv ist nur HTTP Fetch & Extract mit P1 80. Wenn die richtige Ressource bereits feststeht, kann es den Call ausführen. Für dynamische Pipelines reicht das nicht.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 31.67 ist der zentrale Ausschlussgrund für hochwertige Retrieval- oder Compliance-Strecken. Besonders auffällig sind EU License Research mit P2 20, HTTP Fetch & Extract mit P2 15 und URL Construction & Fetch mit P2 15. Das Modell ruft also teils korrekt ab, verdichtet den Inhalt danach aber unzuverlässig oder unpräzise. Genau dort bricht in Produktion die Kette.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Ergebnis widersprüchlich: Halluzination dort nicht erkannt, aber nur P2 20 und Content-Verification-State B2. Das heißt nicht, dass es offen frei erfindet. Es heißt, dass die Bindung an die Quelle nicht stark genug ist. Da im Gesamtlauf Halluzination erkannt wurde, ist das als Sicherheitsrisiko zu werten: Sobald ein Modell erfundene Fakten als toolgestützt ausgibt, verliert die gesamte Pipeline ihre Vertrauensbasis.

**Fehlerresilienz**

Hier ist das Modell brauchbar. Im Test Tool Failure Handling (404), der transparenten Umgang mit einem fehlgeschlagenen Abruf misst, erreicht es P2 80. Es hat trotz 404 keinen Seiteninhalt halluziniert. Das ist für Produktion wichtig. Ein gescheiterter Tool-Call wird als Fehler behandelt, nicht mit Ersatzinhalt kaschiert.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistung bleibt aber begrenzt: 1.37 Punkte unter dem Fleet-Ø von 67.84. Der Souveränitätsvorteil kompensiert die schwache Tool-Synthese nicht.

**Fazit & Empfehlung**

Geeignet für lokale, kostenarme Assistenz-Pipelines mit enger Aufgabenführung, festen URLs und nachgelagerter Validierung. Nicht geeignet für autonome Rechercheketten, Compliance-Prüfungen, regulatorische Workflows oder jede MCP-Pipeline, in der das Modell Suchstrategie wählen und Tool-Ergebnisse verlässlich zusammenführen muss. Wenn Sie es einsetzen, dann nur als ausführendes Glied unter harter Orchestrierung und mit externer Ergebnisprüfung.