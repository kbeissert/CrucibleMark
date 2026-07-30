**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:03:09


Nicht deploy. Die Kombination aus schwacher Gesamtleistung, invaliden Tool-Calls und erkannter Halluzination disqualifiziert das Modell für eine MCP-gestützte Produktionspipeline.

**Tool-Execution-Profil**

Qwen3.6 27B Instruct zeigt kein verlässliches Werkzeugverhalten. Der P1-Wert von 19.17 ist nicht nur niedrig, er fällt in den entscheidenden Orchestrierungsaufgaben auf null. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erkennt das Modell den passenden Zugriffspfad nicht. Beim URL-Construction-&-Fetch-Test, der die korrekte Ableitung einer Ziel-URL aus Wissen und anschließenden Fetch misst, scheitert es ebenfalls vollständig.

Das Muster spricht nicht für adaptive Tool-Intelligenz, sondern für brüchige oder starre Ausführungslogik. Positiv ist nur HTTP Fetch & Extract: Wenn der richtige Inhalt bereits sauber erreichbar ist, extrahiert das Modell brauchbar. Für produktive MCP-Pipelines reicht das nicht. Das Problem liegt vor der Extraktion, bei Auswahl und Form des Calls. Retry war nicht erforderlich, daher ist das kein reines Formatproblem. Es ist ein Verständnis- und Entscheidungsproblem im Tool-Einsatz.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt. Der P2-Wert von 22.50 zeigt, dass das Modell Ergebnisse oberflächlich zusammenfassen kann, aber kaum robuste, entscheidungsfeste Verdichtung liefert. Die Asset-Werte sind auffällig flach: meist 20 Punkte, selbst dort, wo die Tool-Ausführung scheitert. Das deutet auf generische Zusammenfassungen statt belastbarer, quellennaher Synthese.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingt, hat es nicht halluziniert. Das ist der wichtigste Entlastungspunkt. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko. In einer Tool-Pipeline genügt ein einzelner erfundener Fakt, um die Vertrauenskette zwischen Tool-Ausgabe und Modellantwort zu brechen.

**Fehlerresilienz**

Beim 404-Test, der Transparenz bei fehlgeschlagenem Tool-Call statt erfundenem Ersatzinhalt prüft, blieb das Modell sauber. Es hat keinen Seiteninhalt halluziniert. Das ist für Produktion die Mindestanforderung und hier erfüllt. Daraus folgt aber keine generelle Robustheit, weil die eigentliche Schwäche früher einsetzt: Das Modell kommt oft gar nicht zu einem validen, passenden Tool-Call.

**Betriebsprofil**

Sehr langsam. Call 1: 31.11s, Call 2: 109.65s, Total: 281.79s.  
MCP-Latenz: 0.14s, also liegt das Problem klar im Modell, nicht in der Tool-Schicht.  
Kosten/Run: local. Günstig im direkten Betrieb, aber schwache Leistung bei hoher Laufzeit.

**Fazit & Empfehlung**

Geeignet ist dieses Modell höchstens für lokal betriebene Assistenz-Workflows mit eng geführten, vorvalidierten Tool-Pfaden und menschlicher Kontrolle. Nicht geeignet ist es für autonome MCP-Pipelines, dynamische Tool-Auswahl, Rechercheketten, URL-Ableitung oder Compliance-nahe Prozesse. Wenn Sie einem Modell Infrastruktur übergeben wollen, muss es Werkzeuge korrekt wählen und Ergebnisse verlässlich daran binden. Genau das zeigt Qwen3.6 27B Instruct hier nicht.