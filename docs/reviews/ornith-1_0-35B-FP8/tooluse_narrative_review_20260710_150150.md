**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:01:50


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauensniveau für unbeaufsichtigte MCP-Pipelines begrenzen.

**Tool-Execution-Profil**

Ornith 1.0 35B zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr zuverlässig. Das spricht für brauchbare Planungslogik in dynamischen Agent-Flows. Beim URL-Construction-Test, der die Ableitung einer Zieladresse aus Eigenwissen und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für Pfade mit harter Protokolltreue. Der Gesamtwert in P1 ist gut, trotzdem ist der Befund „Tool-Call valide: false“ produktionsrelevant. Das heißt: Die Modellentscheidung ist oft richtig, die formale Ausführung ist nicht durchgehend MCP-sauber. Positiv ist, dass kein Retry erforderlich war. Das Problem wirkt daher eher wie ein punktueller Protokoll- oder Formatfehler als ein grundsätzliches Verständnisdefizit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. Die Synthesis Quality liegt spürbar unter der Ausführungsseite. Das sieht man besonders bei Multilingual Search & Synthesis, wo die sprachübergreifende Recherche noch gelingt, die Verdichtung auf Deutsch aber deutlich an Präzision verliert. Für einfache Extraktion aus Fetch-Inhalten arbeitet es solide. Für mehrquellige, sprachgemischte Verdichtung ist es kein belastbarer Standardbaustein.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten auf aktuelle Web-Quellen prüft, bleibt es ausreichend diszipliniert und halluziniert nicht aus dem Vorwissen. Das ist der wichtigste Vertrauensanker dieses Laufs. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko. In einer Tool-Pipeline ist das kein Qualitätsdetail, sondern ein Bruch der Beweiskette zwischen Quelle und Antwort.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Aufruf misst, erfindet Ornith keinen Seiteninhalt. Das ist die Mindestanforderung für Produktion und sie wird erfüllt. Schwach ist die eigentliche Fehlerbehandlung trotzdem: Der Output bleibt mit P2 40 zu knapp oder zu unklar, um nachgelagerte Systeme sauber zu informieren. Für operator-geführte Workflows ist das akzeptabel. Für vollautonome Fehlerpfade ist es zu dünn.

**Betriebsprofil**

Total 98.92s pro Run. Call 1 2.41s. MCP-Latenz 0.95s. Call 2 13.12s. Kosten/Run: local. Langsam für die erreichte Gesamtqualität. Günstig im Betrieb, wenn lokale GPU-Kapazität bereits vorhanden ist.

**Fazit & Empfehlung**

Geeignet für lokale, agentische Research- und Retrieval-Pipelines mit menschlicher Kontrolle, insbesondere dort, wo Werkzeugwahl wichtiger ist als sprachliche Verdichtung. Nicht geeignet als unbeaufsichtigter Synthese-Endpunkt für Compliance, mehrsprachige Zusammenführung oder strikt deterministische MCP-Orchestrierung. Wenn Sie es einsetzen, dann hinter Schema-Validierung, Tool-Call-Guards und einer zweiten Instanz zur Antwortprüfung.