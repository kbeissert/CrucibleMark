**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:26


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination erkannt wurde, die Synthesetreue mit Combined 73.17 aber klar hinter der Ausführungsqualität zurückbleibt.

**Tool-Execution-Profil**

Grok 4 Reasoning zeigt ein belastbares Tool-Profil. Der Tool-Call war valide, das spricht für saubere MCP-Konformität im produktiven Pfad. Besonders stark ist Web Search & Tool Selection: Im Test, der prüft, ob ohne Hinweis web_search statt fetch nötig ist, wählt das Modell das richtige Werkzeug sicher. Das ist kein stures Musterverhalten, sondern spricht für situative Werkzeugwahl. Beim URL-Construction-Test, der die korrekte Ziel-URL aus eigenem Wissen plus anschließenden Fetch misst, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines. P1 80 ist dafür solide, aber kein Freifahrtschein.

Dass ein Retry erforderlich war, wirkt hier eher wie ein Format- oder Ablaufproblem als ein Verständnisfehler. Dafür sprechen die insgesamt hohe P1-Leistung von 89.17 und die durchgehend validen Calls. Für produktive Nutzung heißt das: Wrapper mit Retries und Schema-Validierung einplanen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. P2 56.67 ist der eigentliche Engpass dieses Modells. Es findet Quellen und führt Werkzeuge aus, komprimiert Ergebnisse dann aber oft zu grob oder zu wenig trennscharf. Das sieht man besonders bei EU License Research und Tool Failure Handling (404), beide mit P2 40. Für Compliance, Audit und präzise Entscheidungsdokumente ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gut. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Content-Verification-State A stützt den Befund: Das Modell bleibt grundsätzlich an der beschafften Evidenz.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt misst, halluziniert Grok 4 Reasoning nicht. Das ist produktionsreif. Die schwache P2 zeigt aber, dass die Fehlerkommunikation zwar ehrlich, aber nicht immer ausreichend präzise oder hilfreich verdichtet wird. Für Operations-Pipelines ist das akzeptabel. Für Endnutzer-Ausgaben sollte die Fehlerbehandlung stärker gerahmt werden.

**Betriebsprofil**

Total 90.93s pro Run. Einzelcalls 7.15s und 7.11s, MCP-Latenz 0.89s. Langsam für den Durchsatzbetrieb. Kosten 0.014590 pro Run. Preislich moderat, gemessen an der Leistung eher fair als günstig.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Wahl und saubere Ausführung wichtiger sind als hochwertige Ergebnisverdichtung: Recherche-Orchestrierung, mehrstufige Abrufketten, kontrollierte Agentenpfade mit nachgelagerter Validierung. Nicht erste Wahl für Compliance-Summaries, Executive Briefings oder jede Pipeline, in der die Modellausgabe selbst das Endprodukt ist. Deployen, wenn ein zweites System die Synthesis prüft oder ersetzt. Nicht deployen als alleinige Instanz für tool-basierte Schlussfassungen.