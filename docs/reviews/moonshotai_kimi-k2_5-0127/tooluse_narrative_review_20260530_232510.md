**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:25:10


Bedingt deploy, weil Kimi K2.5 valide Tool-Calls ohne Halluzinationssignal liefert, die Synthesequalität mit 73.50 Combined aber nicht stark genug für ungeprüfte High-Trust-Ausgaben ist.

**Tool-Execution-Profil**

Das stärkste Produktionssignal ist P1 86.67: Das Modell arbeitet tool-seitig sauber, erzeugt valide Aufrufe und blieb ohne Retry protokollkonform. Das spricht für stabile MCP-Einbindung und gegen Formatfragilität. Als Agentic-Orchestrator wirkt Kimi K2.5 nicht wie ein Modell, das starr immer denselben Pfad fährt. Die vorliegenden Tool-Selection-Daten zu Web Search & Tool Selection sowie URL Construction & Fetch sind zwar nicht einzeln ausdifferenziert, aber das Gesamtbild spricht dafür, dass es Werkzeugnutzung grundsätzlich versteht und nicht nur Fetch-Calls nach Schema F ausführt. Für dynamische Pipelines ist das brauchbar. Für deterministische Retrieval-Wege fehlt hier aber der feinere Nachweis, ob die Werkzeugwahl immer präzise genug ist.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 60.00 ist für Produktionspipelines der schwächere Teil des Profils. Das Modell kann Ergebnisse zusammenführen, aber nicht mit der Präzision und Verdichtungsstabilität, die man für regulatorische, kundenwirksame oder stark verdichtete Entscheidungsausgaben erwarten sollte. Der Engpass liegt also nicht im Tool-Zugriff, sondern in der nachgelagerten Verarbeitung der Tool-Ergebnisse.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist positiv. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist für Compliance-nahe und zeitkritische Recherchen das wichtigere Signal als reine Formulierungsgüte.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagenden Tool-Calls gegen erfundenen Ersatzinhalt prüft, blieb Kimi K2.5 sauber. Es halluzinierte trotz Fehler keinen Seiteninhalt. Das ist akzeptables Produktionsverhalten. Ein Tool-Ausfall beschädigt damit nicht automatisch die Vertrauenskette der Pipeline.

**Betriebsprofil**

Call 1: 6.49s. MCP-Latenz: 1.42s. Call 2: 34.44s. Total: 254.10s. Langsam.  
Kosten pro Run: 0.005853. Günstig.  
Im Verhältnis zur Leistung ist das Preisniveau attraktiv, die End-to-End-Laufzeit aber deutlich zu hoch für latenzkritische Orchestrierung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Werkzeugnutzung, Planungslogik und sauberes Fehlerverhalten wichtiger sind als knappe, hochwertige Endverdichtung. Gute Passung für interne Research-Orchestrierung, mehrstufige Agent-Flows und kostensensible Batch-Prozesse mit menschlicher Abnahme oder nachgelagerter Validierung. Nicht die erste Wahl für kundennahe Antwortsysteme, Compliance-Summaries oder Pipelines, in denen das Modell Tool-Ergebnisse präzise komprimieren und direkt entscheidungsreif formulieren muss.