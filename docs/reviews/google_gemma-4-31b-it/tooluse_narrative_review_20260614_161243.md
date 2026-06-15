**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:12:43


Bedingt deploy, weil Gemma 4 31B valide Tool-Calls produziert und keine Halluzination im Lauf zeigte, aber die Synthesetreue mit Combined 74.17 und P2 60 für verlässliche Ergebnisverdichtung nicht stabil genug ist.

**Tool-Execution-Profil**

Das Modell ist bei der Tool-Ausführung klar produktionsnah. Es wählt Werkzeuge nicht nur mechanisch, sondern erkennt im Test Web Search & Tool Selection, der die Unterscheidung zwischen Suche und direktem Abruf prüft, zuverlässig, dass zuerst web_search nötig ist. Das spricht für brauchbare Werkzeugwahl in offenen Aufgaben. Beim URL-Construction-Test, der die eigenständige Herleitung einer Ziel-URL und anschließendes fetch misst, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 heißt hier: Der Call ist valide, doch die Präzision bei abgeleiteten URLs ist nicht durchgehend belastbar. MCP-seitig gab es keine Auffälligkeiten. Tool-Call war valide, Retry war nicht erforderlich. Für orchestrierte Pipelines ist das ein gutes Signal.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die stärksten Ausschläge liegen nicht in der Tool-Nutzung, sondern in der Nachverarbeitung. HTTP Fetch & Extract und Tool Failure Handling (404) liegen bei P2 80 und sind damit solide. Kritisch sind aber EU License Research mit P2 40 und Multilingual Search & Synthesis mit P2 20. Das Modell holt also Informationen sauber herein, komprimiert und priorisiert sie aber ungleichmäßig. Für Compliance, Policy oder mehrsprachige Research-Flows ist das zu unsicher.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, bleibt das Modell formal im sicheren Bereich. Content-Verification-State A, keine Halluzination erkannt. Das Vertrauen in die Tool-Grenze ist damit vorhanden, auch wenn die inhaltliche Verdichtung schwach ausfällt.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt misst, meldet es den Fehlschlag, statt Seiteninhalt zu erfinden. P2 80 ohne Halluzination trotz 404 reicht für Produktion aus. Das ist kein Komfortmerkmal, sondern eine Basiseigenschaft für sichere Tool-Pipelines.

**Souveränitätsprofil**

Nicht lokal betreibbar. Cloud-only unter Google Gemma Terms of Use. Leistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.84. Damit kein Souveränitätsgewinn durch lokale Kontrolle, sondern ein proprietärer Cloud-Kompromiss ohne klaren Leistungsaufschlag.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen korrekte Tool-Wahl, valides Calling und sauberes Fehlerverhalten wichtiger sind als hochwertige Endverdichtung. Das passt zu Retrieval-, Fetch-, Kontroll- und Vorstufen-Workflows mit nachgelagerter Verifikation. Nicht geeignet für Pipelines, die aus Tool-Output sofort belastbare Entscheidungstexte, Compliance-Summaries oder mehrsprachige Synthesen erzeugen sollen. Dafür braucht es ein Modell mit deutlich höherer Synthesetreue.