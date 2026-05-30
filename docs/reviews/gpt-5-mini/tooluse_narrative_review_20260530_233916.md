**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:16


Bedingt deploy, weil GPT-5 Mini zuverlässig gültige Tool-Calls erzeugt und keine Halluzinationen zeigt, aber die Synthesequalität mit Combined 73.17 und P2 56.67 für entscheidungskritische Ausgabeschichten zu ungleichmäßig bleibt.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsseite klar produktionsnah. Tool-Calls waren valide, ein Retry war nicht nötig, und P1 90 bestätigt stabile MCP-Konformität. Besonders wichtig: Beim Web Search & Tool Selection-Test, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählte es das richtige Werkzeug mit P1 100. Das spricht für echte Werkzeugwahl statt starrem Fetch-Muster. Beim URL-Construction-Test, der korrekte Ziel-URLs aus Modellwissen verlangt, fällt es auf P1 80. Es kann also bekannte Pfade brauchbar ableiten, arbeitet dabei aber nicht durchgehend deterministisch genug für fragile Fetch-Ketten.

Für MCP-Pipelines heißt das: als Operator des Toolings ist das Modell verlässlich. Die Schwäche liegt nicht in Protokoll oder Call-Form, sondern in der letzten Meile zwischen Beschaffung und sauberer Ergebnisformulierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Werte sind der klare Bremsfaktor dieses Runs. EU License Research und Multilingual Search & Synthesis landen jeweils bei P2 40. HTTP Fetch & Extract sowie Tool Failure Handling (404) bei 60. Nur URL Construction & Fetch erreicht 80. Das Modell holt Informationen also meist korrekt herein, komprimiert und priorisiert sie aber nicht konstant präzise genug für Berichte, Compliance-Zusammenfassungen oder andere Ausgaben, in denen Nuancen zählen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gut. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, blieb es trotz schwacher Verdichtung im Tool-Pfad. Content-Verification-State A, keine Halluzination erkannt. Das ist für produktive Tool-Infrastrukturen wichtiger als stilistische Qualität: Das Modell erfindet keine externen Befunde.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Abruf prüft, halluzinierte das Modell keinen Seiteninhalt. P2 60 zeigt keine starke Fehleraufbereitung, aber das Kernverhalten stimmt: Es macht den Ausfall sichtbar, statt Ersatzfakten zu liefern. Das ist die Mindestanforderung für robuste Pipelines.

**Betriebsprofil**

Call 1: 3.56s. MCP-Latenz: 0.89s. Call 2: 20.33s. Total: 148.69s.  
Kosten pro Run: 0.011345.  
Fazit: günstig, aber für die gelieferte Gesamtleistung klar langsam.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines, in denen Tool-Auswahl, valider Abruf und transparente Fehlerbehandlung wichtiger sind als hochpräzise Verdichtung. Gut einsetzbar für Recherche-Orchestrierung, Vorstufen von Analysten-Workflows und agentische Abrufketten mit nachgelagerter Validierung. Nicht die richtige Wahl für Compliance-Ausgaben, Executive Summaries oder kundensichtbare Antworten, wenn das Modell die Tool-Ergebnisse selbst verlässlich verdichten und formulieren soll.