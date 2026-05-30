**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:02


Bedingt deploy, weil das Modell valide Tool-Calls erzeugt und in der Ausführung stark ist, aber mit erkannter Halluzination im Gesamturteil kein durchgehend vertrauenswürdiger Tool-Synthesizer ist.

**Tool-Execution-Profil**

Das Ausführungsprofil ist klar besser als die Endantworten. Mit P1 90 zeigt Ministral 14B, dass es MCP-konform arbeitet, gültige Calls baut und keine Retry-Schleife braucht. Das ist für produktive Tool-Pipelines ein echter Pluspunkt. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erkennt das Modell den richtigen Werkzeugtyp sicher. Das spricht gegen reines Schema-Folgen und für brauchbare Werkzeugwahl im Kontext. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann per Fetch abrufen lässt, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für Pipelines, die exakte Adressbildung erwarten. Das Muster ist damit konsistent: gute Tool-Intelligenz bei der Auswahl, etwas weniger Präzision bei der letzten Meile der Adresskonstruktion.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 50.83 ist der eigentliche Flaschenhals. Besonders schwach fällt die Verdichtung bei EU License Research und Web Search & Tool Selection aus, wo es zwar die richtigen Quellen ansteuert, aber die gewonnenen Informationen nicht belastbar zusammenführt. Besser arbeitet es bei URL Construction & Fetch sowie bei Multilingual Search & Synthesis. Das Modell kann also aus Tool-Ergebnissen brauchbare Antworten formen, aber nicht konstant.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das Produktionsrisiko. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen stammen, fiel das Modell mit P2 15 und erkannter Halluzination auf. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsproblem. Ein Modell, das erfundene oder vortrainierte Inhalte als Werkzeugergebnis ausgibt, beschädigt die Vertrauenskette der gesamten MCP-Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Seiteninhalt misst, halluziniert es nicht und erreicht P2 80. Das ist produktionsfähig. Wenn ein Aufruf scheitert, bleibt die Antwort nachvollziehbar statt kompensatorisch erfunden.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Setups operativ attraktiv. Die Leistung liegt 5.32 Punkte unter dem Fleet-Ø von 66.76. Damit ist es lokal konkurrenzfähig, aber nicht stark genug, um Vertrauensprobleme in der Synthese durch Souveränität allein zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische Tool-Pipelines mit klarer Nachkontrolle, etwa Retrieval, Vorstrukturierung, Routing und robuste Fehlerbehandlung. Nicht geeignet für Compliance-, Policy-, Research- oder Freigabe-Workflows, in denen die Endantwort strikt an Tool-Belege gebunden bleiben muss. Wenn Sie es einsetzen, dann als ausführendes Zwischenmodell unter harter Ergebnisvalidierung, nicht als letzte Instanz für faktenkritische Synthese.