**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:03:20


Bedingt deploy, weil die Tool-Nutzung oft funktional ist, aber die Vertrauensschicht darüber nicht stabil genug arbeitet: kein Halluzinationsbefund, jedoch invalide Tool-Calls und nur moderate Gesamteignung.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt bloßem Standardmuster. Beim Test **Web Search & Tool Selection**, der prüft, ob ohne Hinweis erkannt wird, dass Suche statt direktem Fetch nötig ist, wählt es das richtige Werkzeug zuverlässig. Das spricht für brauchbare Orchestrierungslogik. Beim Test **URL Construction & Fetch**, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug. Genau dort sieht man die Grenze: Es kann den nächsten sinnvollen Schritt oft erkennen, produziert aber nicht durchgehend protokollfeste Aufrufe. Dass der globale Tool-Call als nicht valide markiert ist, wiegt schwerer als die guten P1-Teilwerte. Für MCP-Pipelines heißt das: als assistiver Planner vertretbar, als autonomer Tool-Operator nur mit strikter Call-Validierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist der klare Schwachpunkt. Bei **HTTP Fetch & Extract** und **Web Search & Tool Selection** verdichtet es Ergebnisse noch ordentlich, aber bei **EU License Research** und **Multilingual Search & Synthesis** bricht die Präzision sichtbar ein. Das Modell holt Informationen also oft korrekt herein, formt daraus aber keine belastbar knappe, priorisierte Endantwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen bezogen werden, wurde keine Halluzination erkannt. Das ist der wichtigste Vertrauenspunkt in diesem Run. Der niedrige Synthesis-Wert zeigt dennoch, dass Quellentreue nicht automatisch zu guter Entscheidungsaufbereitung führt.

**Fehlerresilienz**

Beim Test **Tool Failure Handling (404)**, der den Umgang mit einem gescheiterten Abruf prüft, erfindet das Modell keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die Antwortqualität bleibt schwach, aber die Reaktion bleibt transparent genug, um nachgelagerte Systeme nicht zu vergiften. Für produktive Nutzung ist das akzeptabel, solange der Orchestrator Fehlerzustände selbst streng behandelt.

**Betriebsprofil**

Call 1: 19.16s. MCP-Latenz: 2.39s. Call 2: 99.41s. Total: 725.77s.  
Lokal betrieben, daher direkte Run-Kosten ohne API-Gebühr.  
Für die gezeigte Leistung klar langsam.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Research-Pipelines mit Human-in-the-Loop, in denen Tool-Auswahl wichtiger ist als die letzte Verdichtungsstufe und jeder Tool-Call validiert wird. Nicht geeignet für Compliance-, Incident- oder Entscheidungs-Pipelines, in denen das Modell Tool-Ergebnisse selbstständig präzise zusammenziehen und formal sauber weiterreichen muss. Der offene, abliterierte Fine-Tune erhöht zusätzlich das Governance-Risiko. Als Vorschaltmodell für Suche und Fetch vertretbar. Als letzte Instanz über Tool-Wahrheit nicht.