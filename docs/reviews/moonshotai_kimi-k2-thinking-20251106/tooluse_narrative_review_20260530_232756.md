**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:56


Bedingt deploy, weil die Tool-Aufrufe valide und halluzinationsfrei bleiben, die Synthesetreue mit 70.00 kombiniert aber nicht stabil genug ist, um unbeaufsichtigt in verifizierungsnahe Pipelines zu gehen.

**Tool-Execution-Profil**

Kimi K2 Thinking arbeitet grundsätzlich MCP-konform. Der Tool-Call war valide, und im Test Web Search & Tool Selection, der prüft, ob ohne Hinweis zwischen Suche und Direktabruf unterschieden wird, traf das Modell die Werkzeugwahl sehr sicher. Das spricht gegen ein starres Muster und für echte Tool-Intelligenz im Dispatcher-Verhalten. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL plus Fetch misst, bleibt es brauchbar, aber nicht präzise genug für vollständig deterministische Abläufe. P1 von 82.50 zeigt damit eine solide Ausführungsseite, aber keine fehlerfreie Agentenpräzision. Dass ein Retry erforderlich war, wirkt hier eher wie ein Orchestrierungs- oder Formatproblem im Lauf als wie ein Verständnisfehler bei der Werkzeugwahl.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Ordentlich, aber nicht belastbar genug für sensible Entscheidungsstrecken. Stark ist es bei HTTP Fetch & Extract, wo strukturierte Inhalte sauber übernommen werden. Schwächer ist es überall dort, wo mehrere Quellen, Sprachwechsel oder regulatorische Nuancen zusammengeführt werden müssen. Das sieht man an EU License Research und Multilingual Search & Synthesis, beide mit nur 40 in P2. Das Modell kann also Material einsammeln, verliert aber bei der Endverdichtung an Präzision und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Training kommen, wurde keine Halluzination erkannt. Das ist das wichtige Vertrauenssignal. Der Content-Verification-State B2 und P2=40 zeigen aber auch: Es bleibt zwar grundsätzlich an den Quellen, formt daraus jedoch keine hinreichend belastbare Compliance-Zusammenfassung.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem gescheiterten Tool-Call gegen erfundenen Ersatzinhalt stellt, reagiert Kimi K2 Thinking produktionsgerecht. P2=80 und keine Halluzination trotz 404 bedeuten: Das Modell kommuniziert den Fehler akzeptabel, statt Seiteninhalt zu erfinden. Für Tool-Pipelines ist das ein klar positives Signal.

**Betriebsprofil**

Call 1: 4.57s. MCP-Latenz: 1.60s. Call 2: 20.05s. Total: 157.28s. Langsam. Kosten pro Run: 0.005985. Günstig. Im Verhältnis zur Leistung ist es ökonomisch attraktiv, aber für latenzkritische Orchestrierung zu träge.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Coding-Pipelines, in denen Tool-Wahl, mehrstufiges Reasoning und transparente Fehlerbehandlung wichtiger sind als knappe Antwortzeiten. Nicht die richtige Wahl für Compliance-, Policy- oder multilingual verdichtende Pipelines, wenn die Endantwort ohne menschliche Kontrolle direkt weiterverarbeitet wird. Deployen, wenn ein Verifikations- oder Review-Schritt hinter der Synthese steht. Ohne diesen Guardrail nicht.