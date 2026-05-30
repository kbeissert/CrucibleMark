**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:46:21


Bedingt deploy, weil Gemini 2.5 Pro valide Tool-Calls erzeugt und keine Halluzination im Tool-Kontext zeigte, aber die Synthesetreue für produktionsnahe Entscheidungs- und Compliance-Pipelines zu unzuverlässig bleibt.

**Tool-Execution-Profil**

Auf der Ausführungsebene arbeitet das Modell sicher. Tool-Call valide, kein Retry erforderlich, keine Protokollprobleme. Das ist für MCP-Pipelines der erste entscheidende Härtetest, und den besteht es. Bei Web Search & Tool Selection, also der Frage ob ohne Hinweis Suche statt direktem Fetch nötig ist, trifft es die Werkzeugwahl souverän. Das spricht gegen starres Call-Muster und für echte Tool-Intelligenz. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließenden Fetch prüft, bleibt es brauchbar, aber nicht präzise genug für strikt deterministische Flows. Daraus folgt ein klares Profil: stark bei Auswahl und Orchestrierung, etwas schwächer bei exakter Ableitung einzelner Fetch-Ziele.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung fällt deutlich hinter die Tool-Ausführung zurück. Bei HTTP Fetch & Extract und Multilingual Search & Synthesis fasst es Ergebnisse noch solide zusammen. Bei EU License Research bricht die Verdichtungsqualität jedoch stark ein. Für Pipelines, in denen aus recherchierten Quellen belastbare Entscheidungsnotizen, Compliance-Memos oder Freigabeempfehlungen entstehen sollen, ist das zu schwankend.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil besser als die Verdichtungsqualität. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das Modell erfindet also keine Quelle. Es nutzt den Tool-Kanal grundsätzlich vertrauenswürdig, auch wenn es die Inhalte daraus nicht konstant gut verdichtet.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Aufruf prüft, reagiert Gemini 2.5 Pro produktionsgerecht. Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. Das ist akzeptabel für reale Systeme. Ein Modell darf an einem Tool scheitern. Es darf aber nicht so tun, als hätte das Tool geliefert.

**Betriebsprofil**

Total 123.44s. Einzelaufrufe 8.11s und 11.54s. MCP-Latenz 0.93s. Damit klar langsam im Gesamtdurchlauf. Kosten pro Run 0.023781 USD. Für ein Frontier-Modell nicht teuer, aber angesichts der nur mäßigen Syntheseleistung auch nicht effizient.

**Fazit & Empfehlung**

Geeignet für agentische MCP-Pipelines, in denen Tool-Wahl, saubere Call-Erzeugung und transparente Fehlerbehandlung wichtiger sind als hochpräzise Endverdichtung. Gut nutzbar als Orchestrator, Recherche-Dispatcher oder vorgeschaltete Tool-Steuerung mit nachgelagerter Validierung. Nicht die richtige Wahl für Compliance-nahe, entscheidungsvorbereitende oder dokumentationskritische Pipelines, in denen die verbale Synthese selbst das Produkt ist.