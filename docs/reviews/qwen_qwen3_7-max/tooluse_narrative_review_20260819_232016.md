**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:20:16


Bedingt deploy, weil das Modell keine Halluzination im Benchmark zeigt, aber invalide Tool-Calls produziert und mit 60.38 Combined nur moderate Produktionssicherheit für MCP-Pipelines erreicht.

**Tool-Execution-Profil**

Qwen 3.7 Max kann Tools ausführen, aber nicht durchgehend mit der nötigen Verlässlichkeit für autonome Orchestrierung. Der P1-Wert von 76.67 zeigt brauchbare Grundfähigkeit, wird aber durch `tool_call_valid=false` klar relativiert. Das entscheidende Muster liegt in der Werkzeugwahl: Beim Web-Search-&-Tool-Selection-Test, der prüft ob ohne Hinweis `web_search` statt `fetch` gewählt wird, fällt das Modell mit P1=35 deutlich ab. Beim URL-Construction-Test, der die Ableitung einer bekannten Ziel-URL und den anschließenden Fetch misst, erreicht es dagegen P1=75. Das spricht nicht für flexible Tool-Intelligenz, sondern eher für ein festes Ausführungsmuster: Wenn die Zielstruktur schon nahe liegt, arbeitet es solide. Wenn es erst den richtigen Werkzeugtyp erkennen muss, bricht die Steuerung ein. Retry war nicht erforderlich. Das Problem liegt hier daher nicht primär im Format, sondern in der Tool-Policy des Modells.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 liegt bei 63.33. Starke Einzelresultate wie HTTP Fetch & Extract mit P2=80 und Tool Failure Handling (404) mit P2=100 zeigen, dass es explizit vorliegende Inhalte sauber zusammenfassen kann. Schwach wird es dort, wo Recherche, Auswahl und Verdichtung zusammenfallen, etwa bei Web Search & Tool Selection und Multilingual Search & Synthesis mit jeweils P2=20.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, gab es keine erkannte Halluzination. Das ist das wichtigste Entwarnungssignal. Der P2-Wert von 40 bleibt aber zu niedrig, um dem Modell bei compliance-naher Recherche ohne enge Führung zu vertrauen.

**Fehlerresilienz**

Hier ist das Modell produktionsfähig. Im 404-Test, der transparenten Umgang mit fehlschlagenden Tool-Calls gegen erfundenen Ersatzinhalt misst, erreicht es P2=100. Es kommuniziert den Fehler offen und halluziniert keinen Seiteninhalt. Das ist für MCP-Betrieb akzeptabel und wichtig, weil Fehlpfade in realen Pipelines häufiger sind als Idealfälle.

**Betriebsprofil**

Call 1: 14.21s. Call 2: 31.34s. MCP-Latenz: 0.45s. Total: 275.98s. Langsam für die gezeigte Leistung. Kosten/Run: local.

**Fazit & Empfehlung**

Geeignet für beaufsichtigte MCP-Pipelines mit klar vorgegebenem Tool-Pfad, robuster Fehlerbehandlung und nachgelagerter Validierung der Ergebnisverdichtung. Nicht geeignet für offene Rechercheketten, dynamische Tool-Auswahl oder mehrsprachige Discovery-Workflows, in denen das Modell selbst entscheiden muss, ob gesucht, konstruiert oder direkt gefetcht werden soll. Wenn Sie Qwen 3.7 Max einsetzen, dann als ausführendes Modell in einem stark gerahmten Orchestrator, nicht als eigenständig entscheidende Tool-Instanz.