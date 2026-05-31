**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:53:31


Bedingt deploy, weil die Tool-Nutzung stark wirkt, aber der invalide Tool-Call und der schwache Gesamteindruck zeigen, dass man ihm keine unüberwachte MCP-Infrastruktur mit hohem Vertrauensanspruch übergeben sollte.

**Tool-Execution-Profil**

DeepSeek V3.2 zeigt grundsätzlich brauchbare Ausführungskompetenz. Der P1-Wert von 90 signalisiert, dass es Tools aktiv einsetzt und bei klaren Fetch-Aufgaben oft zum Ergebnis kommt. Im Test **HTTP Fetch & Extract**, der präzise Fakten aus echtem Seiteninhalt verlangt, arbeitet es sehr ordentlich und extrahiert verwertbare Informationen. Im Test **EU License Research**, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingt, hat es die Recherche offenbar tatsächlich angestoßen.

Kritisch bleibt aber: Der Tool-Call war nicht valide. Für produktive MCP-Pipelines ist das kein Formfehler am Rand, sondern ein Integrationsrisiko. Es bedeutet, dass gute Absicht nicht automatisch in protokollsaubere Ausführung übersetzt wird. Zu **Web Search & Tool Selection** und **URL Construction & Fetch** fehlen belastbare Daten. Damit ist offen, ob das Modell Werkzeuge intelligent nach Informationslage wählt oder vor allem dann funktioniert, wenn der Pfad praktisch vorgegeben ist. Für dynamische Tool-Router ist diese Lücke relevant.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht belastbar genug für strenge Produktionspfade. Der P2-Wert von 70 wird durch ein starkes Ergebnis in **HTTP Fetch & Extract** getragen, wo das Modell Inhalte aus einem Fetch sauber zusammenzieht. Gleichzeitig fällt **EU License Research** mit P2=40 deutlich ab. Das spricht für schwankende Verdichtungsqualität, sobald Aktualität, Compliance-Kontext oder mehrere Einzelbefunde sauber zusammengeführt werden müssen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist gemischt positiv. Im Honeypot **EU License Research**, der genau diese Trennung prüft, wurde keine Halluzination erkannt und der Verifikationszustand ist stark. Das ist wichtig: Das Modell erfindet hier keine aktuellen Regelinhalte. Aber es verdichtet die gefundenen Inhalte nicht präzise genug, um daraus ohne Kontrolle belastbare Entscheidungen abzuleiten.

**Fehlerresilienz**

Beim Test **Tool Failure Handling (404)**, der transparentes Verhalten bei fehlgeschlagenem Abruf prüft, hat DeepSeek V3.2 keinen Seiteninhalt erfunden. Das ist produktionsreif im Kern. Ein Modell darf scheitern. Es darf dabei nur nichts ersetzen, was nie geliefert wurde. Genau diese Mindestanforderung erfüllt es.

**Betriebsprofil**

Total 34.33s pro Run. Call 1: 3.19s, Call 2: 13.98s. Insgesamt langsam. Kosten pro Run: $0.000612. Sehr günstig. Preislich attraktiv, leistungseitig nur dann sinnvoll, wenn zusätzliche Validierungsschichten ohnehin vorhanden sind.

**Fazit & Empfehlung**

Geeignet für kostensensitive Pipelines mit Human-in-the-Loop, für technische Recherche mit nachgelagerter Prüfung und für Extraktionsaufgaben, bei denen Tool-Output noch einmal validiert wird. Nicht geeignet als autonomer Orchestrator für Compliance, Policy, Lizenz- oder andere entscheidungsnahe Workflows, in denen ein invalider Tool-Call oder eine ungenaue Synthese direkt in den Prozess einsickert. Für MCP-Umgebungen nur mit strikter Call-Validierung, Schema-Checks und Output-Gating einsetzen.