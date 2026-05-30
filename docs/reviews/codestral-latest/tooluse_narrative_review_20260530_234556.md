**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:45:56


Bedingt deploy, weil Codestral valide Tool-Calls erzeugt und im MCP-Ablauf stabil bleibt, aber die nachgelagerte Synthese mit Combined 64.96 und erkannten Halluzinationsbefunden nicht verlässlich genug für faktenkritische Pipelines ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klar stärkere Seite. Codestral wählt Werkzeuge nicht rein schematisch, sondern zeigt brauchbare Tool-Intelligenz: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es P1 100 und erkennt den Bedarf für web_search sauber. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Modellwissen und anschließendes fetch misst, ist es mit P1 80 noch solide, aber nicht deterministisch genug für fragile Pipelines mit starren URL-Erwartungen. Wichtig für den Produktionseinsatz: Die Tool-Calls waren valide, MCP-protokollkonform und ohne Retry lauffähig. Das spricht für eine robuste Einbindung als ausführendes Modell in klar geführten Tool-Flows.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 47.50 ist der eigentliche Risikowert dieses Laufs. Codestral kann abgerufene Inhalte in einfachen Fällen verwerten, wie URL Construction & Fetch mit P2 100 oder Tool Failure Handling (404) mit P2 80 zeigt. Sobald mehrere Quellen, Sprachwechsel oder präzise Extraktion gefragt sind, fällt die Verdichtungsqualität deutlich ab. Besonders kritisch sind EU License Research mit P2 20 und Multilingual Search & Synthesis mit P2 15.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht zuverlässig genug. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, liegt der Content-Verification-State nur bei B1 und P2 bei 20. Zwar wurde dort keine Halluzination markiert, aber die Antwort blieb nicht eng genug an den verifizierbaren Tool-Inhalten. Zusätzlich ist global ein Halluzinationsbefund gesetzt. In einer Tool-Pipeline ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Das Modell kann den Anschein von tool-gestützter Faktizität erzeugen, ohne die Quelle sauber zu tragen.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich Codestral produktionsnah. Im 404-Test, der transparenten Umgang mit fehlschlagenden Aufrufen gegen erfundenen Ersatzinhalt abgrenzt, erreicht es P2 80 und halluziniert keinen Seiteninhalt. Das ist akzeptabel für Produktion. Ein fehlerhaftes Tool wird als Fehler behandelt, nicht als Einladung zum Auffüllen.

**Souveränitätsprofil**

Lokal betreibbar und grundsätzlich fleet-kompetent, aber nicht führend: Codestral liegt 5.32 Punkte unter dem Fleet-Ø von 66.76. Für souveräne Entwicklungs- und Inhouse-Setups ist das ein brauchbares Profil, sofern die Pipeline die Antwortseite strikt kontrolliert.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Codestral primär Tools auswählt, Aufrufe sauber ausführt und Rohresultate an strengere Downstream-Prüfung übergibt. Nicht geeignet als letzte Instanz für Compliance, Lizenzbewertung, mehrsprachige Recherche oder jede Strecke, in der die Antwort selbst als belastbare Faktensynthese dient. Wenn Sie es einsetzen, dann als lokales Coder-Modell für Tool-Orchestrierung mit harter Quellenbindung, Schema-Outputs und externer Verifikation vor der Nutzerantwort.