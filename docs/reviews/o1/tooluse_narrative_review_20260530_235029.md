**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:50:29


Bedingt deploy, weil OpenAI o1 valide Tool-Calls produziert und insgesamt brauchbar mit MCP arbeitet, aber die erkannte Halluzination die Vertrauenskette in produktiven Tool-Pipelines begrenzt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist stark. Mit P1 90 zeigt o1, dass es das Protokoll einhält, valide Calls erzeugt und ohne Retry auskommt. Das ist für MCP-Betrieb ein klares Positivsignal. Besonders überzeugend ist Web Search & Tool Selection: Beim Test, ob das Modell ohne expliziten Hinweis erkennt, dass web_search statt fetch nötig ist, trifft es die Werkzeugwahl sicher. Das spricht gegen starres Musterverhalten und für echte Tool-Intelligenz.

Schwächer ist URL Construction & Fetch: Beim Test, ob es die Ziel-URL aus eigenem Wissen ableitet und dann fetch korrekt ausführt, bleibt die Ausführung brauchbar, aber nicht präzise genug für deterministische Pipelines. Das Modell kann Tools also gut auswählen, ist aber weniger verlässlich, wenn es erst den exakten Zugriffspfad konstruieren muss. Für Architekturen mit vorgegebenen Endpunkten passt das deutlich besser als für frei navigierende Retrieval-Flows.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 65 ist für ein Frontier-Reasoning-Modell kein starkes Signal. Die Verdichtung ist in HTTP Fetch & Extract sehr gut, bricht aber bei URL Construction & Fetch und Multilingual Search & Synthesis sichtbar ein. Das Muster ist klar: Wenn die Beschaffung sauber ist, fasst o1 solide zusammen. Wenn Quellenlage oder Sprachwechsel Reibung erzeugen, verliert die Antwort an Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt o1 im Wesentlichen auf dem Web-Ergebnis und halluziniert nicht. Das ist das wichtigere Vertrauenssignal. Gleichzeitig gilt: Der globale Halluzinationsbefund ist ein Sicherheitsrisiko, kein bloßer Qualitätsmangel. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Glaubwürdigkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt prüft, reagiert o1 produktionsgerecht. Es erfindet keinen Seiteninhalt und kommuniziert den Fehlschlag sauber. P2 80 ist dafür ausreichend. Für robuste Pipelines ist das akzeptabel, weil der Fehler sichtbar bleibt und nachgelagerte Systeme korrekt reagieren können.

**Betriebsprofil**

Call 1: 6.54s. Call 2: 16.93s. MCP-Latenz: 1.14s. Total: 147.62s. Langsam. Kosten pro Run: $0.708810. Teuer. Im Verhältnis zur Leistung nur für hochwertige, nicht zeitkritische Runs vertretbar.

**Fazit & Empfehlung**

Geeignet für kontrollierte MCP-Pipelines mit klaren Tool-Grenzen, vorgegebenen APIs und hohem Bedarf an mehrstufigem Reasoning. Nicht geeignet als frei laufender Recherche-Agent, wenn URL-Konstruktion, mehrsprachige Synthese oder strikt faktengebundene Ausgaben geschäftskritisch sind. Deploy nur mit Quellennachweis, Output-Checks und harten Guardrails zwischen Tool-Ergebnis und finaler Antwort.