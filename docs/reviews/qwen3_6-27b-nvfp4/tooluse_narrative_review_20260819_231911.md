**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:19:11


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgängig valide waren und die Synthesetreue mit Combined 76,00 für tool-gestützte Produktionspipelines zu ungleich ausfällt.

**Tool-Execution-Profil**

Qwen 3.6 27B zeigt echtes Werkzeugverständnis. Beim Web-Search-and-Tool-Selection-Test, der prüft ob das Modell ohne Hinweis erkennt, dass Suche statt direktem Fetch nötig ist, agiert es fehlerfrei. Das spricht gegen ein starres Abrufmuster und für situative Toolwahl. Auch die multilingualen Suchaufgaben und die EU License Research wurden auf P1-Seite sehr sicher bedient.

Schwächer ist die Präzision bei der Ausführung. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, ist das Ergebnis brauchbar, aber nicht deterministisch genug für Pipelines, die korrekte Endpunkte ohne Korrekturschleife erwarten. Der globale Befund „Tool-Call valide: false“ ist hier der operative Haken. Es gibt kein Retry-Muster, also kein offensichtliches Formatproblem. Das wirkt eher wie gelegentliche Ungenauigkeit in der letzten Meile des Calls.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. P2 von 51,67 ist der klare Schwachpunkt dieses Laufs. Qwen kann gefundene Inhalte zusammenziehen, verliert aber bei Verdichtung Konsistenz und Präzision. Das sieht man besonders bei EU License Research mit P2 40 und bei mehreren sonst starken Tool-Aufgaben, die in der Synthese deutlich hinter der Ausführung zurückfallen. Für reine Recherche-Orchestrierung ist das tragbar. Für entscheidungsreife Kurzfassungen eher nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, wurde keine Halluzination erkannt. Das ist der wichtigere Vertrauensbefund. Das Modell dichtet keine erfundenen Compliance-Fakten an ein Tool-Ergebnis an, auch wenn die Zusammenfassung inhaltlich flach bleibt.

**Fehlerresilienz**

Beim 404-Test, der die Reaktion auf einen scheiternden Tool-Call misst, bleibt Qwen transparent und erfindet keinen Ersatzinhalt. P2 60 ist kein Glanzwert, aber produktionsfähig. Ein Modell, das Fehler offen meldet statt Seiteninhalt zu halluzinieren, bleibt in einer MCP-Pipeline kontrollierbar.

**Betriebsprofil**

Total 145,38s. Call 1 3,14s, Call 2 19,67s, MCP-Latenz 1,42s. Für die gezeigte Qualität langsam. Kosten/Run: local. Wirtschaftlich nur sinnvoll, wenn lokale Ausführung und offene Gewichte wichtiger sind als Durchsatz.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen das Modell Tools auswählen, Web-Recherche anstoßen und Fehler sauber offenlegen soll. Nicht geeignet als letzte Instanz für Compliance-Synthesen, entscheidungsreife Executive Summaries oder strikt deterministische Fetch-Pipelines ohne nachgelagerte Validierung. Empfohlen als Recherche- und Orchestrierungsschicht mit hartem Response-Checking nach dem Tool-Call und einer zweiten Stufe für Verdichtung.