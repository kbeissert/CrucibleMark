**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:08:58


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination erkannt wurde, die Synthesequalität mit 63.33 aber zu oft unter Produktionsniveau für präzise Wissensverdichtung bleibt.

**Tool-Execution-Profil**

Das Modell ist als MCP-Arbeiter brauchbar. P1 mit 90 zeigt, dass es valide Tool-Calls erzeugt und protokollkonform arbeitet. Wichtig ist die Differenz zwischen Werkzeugwahl und Ausführung: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erkennt es korrekt, dass erst gesucht werden muss. Das spricht gegen ein starres Fetch-first-Muster. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus eigenem Wissen misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Pipelines mit strikten URL-Annahmen. Retry war nicht erforderlich. Das ist ein gutes Signal, weil weder Formatfehler noch MCP-Verständnisprobleme sichtbar wurden.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt gut. Die schwächeren P2-Werte bei EU License Research und Multilingual Search & Synthesis zeigen, dass das Modell Fakten aus den Tools zwar einsammelt, aber nicht konsistent in eine präzise, knappe und belastbare Antwort überführt. Für Architekturen, in denen das Modell vor allem Tools orchestriert und Rohdaten an nachgelagerte Systeme weitergibt, ist das akzeptabel. Für Compliance-, Policy- oder Executive-Summaries ist es zu ungenau.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja, und das ist der wichtigere Vertrauenspunkt. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, liegt P2 zwar nur bei 40, aber ohne erkannte Halluzination und mit Content-Verification-State A. Das Modell verdichtet schwach, es erfindet aber nicht.

**Fehlerresilienz**

Die Fehlerbehandlung ist produktionstauglich. Beim Test Tool Failure Handling (404), der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt misst, kommuniziert das Modell den Fehlschlag sauber und halluziniert keinen Ersatzinhalt. Genau dieses Verhalten braucht eine Tool-Pipeline: sichtbarer Fehler statt stiller Fiktion.

**Souveränitätsprofil**

Lokal betreibbar und fleet-kompetent genug für souveräne Setups. Der Combined-Score liegt 1.37 Punkte unter dem Fleet-Ø von 67.84 und damit praktisch im Wettbewerbsbereich, ohne externen Datentransfer. Die lokale GGUF-Ausführung ist hier ein realer Betriebswert. Die chinesische Provenienz der Gewichte bleibt dennoch ein Compliance-Thema, auch bei rein lokaler Inferenz.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, die robuste Tool-Nutzung, saubere Fehlerkommunikation und lokale Souveränität priorisieren. Gut passend für Recherche-Orchestrierung, Such-Fetch-Workflows und menschlich nachgelagerte Auswertung. Nicht die erste Wahl für Pipelines, in denen die Modellantwort selbst den verbindlichen Endbefund darstellt, besonders bei mehrsprachiger Verdichtung, Lizenz- oder Policy-Synthesen. Deploy als Tool-Operator, nicht als letzte fachliche Instanz.