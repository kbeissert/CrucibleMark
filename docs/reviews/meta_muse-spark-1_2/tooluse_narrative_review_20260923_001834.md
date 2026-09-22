**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:18:34


Bedingt deploy, weil die Gesamtnote gut ist, aber der Tool-Call nicht valide war und damit die entscheidende Produktionsfrage nicht sauber positiv beantwortet wird.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl-Kompetenz, aber keine saubere Protokollsicherheit. Beim Test **Web Search & Tool Selection**, der prüft, ob ohne Hinweis das richtige Recherchewerkzeug gewählt wird, erkennt es klar, dass `web_search` statt `fetch` nötig ist. Das spricht gegen ein starres Muster und für situationsbezogene Tool-Selektion. Beim Test **URL Construction & Fetch**, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es brauchbar, aber nicht deterministisch genug. P1-Werte von 100 und 80 zeigen also: gute Entscheidung auf Planungsebene, geringere Präzision in der konkreten Ausführung.

Kritisch ist der Globalbefund `tool_call_valid=false`. Auch ohne Retry-Bedarf deutet das auf einen formalen oder semantischen Bruch im Call hin, nicht auf ein bloßes Robustheitsproblem. Für MCP-Pipelines heißt das: Orchestrierungsidee vorhanden, aber die Übergabe an die Infrastruktur braucht Guardrails, Schema-Validierung und enge Laufzeitkontrollen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht präzise genug für hochwertige Retrieval-Pipelines. Die Einzelwerte schwanken sichtbar: **HTTP Fetch & Extract**, also strukturierte Faktenextraktion aus realem Seiteninhalt, landet bei 60. **Multilingual Search & Synthesis**, also sprachübergreifende Recherche mit deutscher Verdichtung, ebenfalls bei 60. Das Modell kann Ergebnisse zusammenziehen, verliert dabei aber Details und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht zuverlässig genug. Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen kommen, fällt die Vertrauensseite mit P2=40 deutlich ab. Es halluziniert nicht offen, aber es bindet die Tool-Recherche nicht hart genug an die Antwort. Für Compliance-, Policy- oder Lizenz-Workflows ist das ein Warnsignal.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im Test **Tool Failure Handling (404)**, der transparenten Umgang mit fehlgeschlagenen Abrufen gegen erfundenen Ersatzinhalt prüft, kommuniziert es den Fehler, statt Seiteninhalt zu erfinden. P2=80 und kein Halluzinationsbefund sind für Produktion ein tragfähiges Minimum. Das schützt die Pipeline vor stillen Falschinformationen.

**Betriebsprofil**

Total 77.74s. Call 1 1.75s, MCP-Latenz 1.40s, Call 2 9.81s. Langsam für den gezeigten Qualitätsstand. Kosten pro Run: local angegeben, Modellprofil selbst: cloud-only. Preisniveau: $1.25/1M Input, $4.25/1M Output. Für Frontier nicht teuer, aber die Laufzeit macht es nur dann wirtschaftlich, wenn Tool-Orchestrierung wichtiger ist als Durchsatz.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit Aufsicht: Recherche-Workflows, mehrstufige Tool-Auswahl, robuste Fehlerkommunikation. Nicht geeignet für streng deterministische MCP-Strecken, in denen jeder Tool-Call formal korrekt sein muss, und nicht für Compliance-nahe Syntheseaufgaben, in denen das Modell strikt im abgerufenen Material bleiben muss. Deploy nur mit Call-Validator, strukturierter Output-Prüfung und einer nachgelagerten Verifikation der finalen Antwort gegen die Tool-Artefakte.