**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:29


Bedingt deploy, weil Claude Opus 4.6 valide Tool-Calls erzeugt und im Tool-Use stark ist, aber die erkannte Halluzination im Honeypot das Vertrauen für faktensensitive Produktionspipelines bricht.

**Tool-Execution-Profil**

Die Tool-Ausführung ist insgesamt belastbar. Tool-Calls waren valide, MCP-konform und ohne Retry ausführbar. Das spricht gegen ein Protokoll- oder Formatproblem. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die richtige Wahl zwischen Suche und direktem Abruf verlangt, erkennt das Modell den Suchbedarf sicher und erreicht volle Ausführungstreue. Das ist ein Signal für echte Werkzeugwahl statt starrem Fetch-Muster. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableitet und dann per Fetch abruft, arbeitet es brauchbar, aber nicht präzise genug für vollständig deterministische Flows. Insgesamt zeigt das Modell also Orchestrierungsintelligenz, nicht nur Schema-Folgen. Für Agenten-Pipelines ist das ein echter Pluspunkt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die Synthesis Quality liegt mit 65 nicht auf dem Niveau der Tool-Ausführung. Das sieht man an der starken Spreizung: HTTP Fetch & Extract und Multilingual Search & Synthesis sind sehr gut, Web Search & Tool Selection fällt in der Verdichtung deutlich ab, und EU License Research bricht fast vollständig ein. Das Modell kann also Ergebnisse gut zusammenführen, aber nicht konsistent.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das Produktionsrisiko. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell und erreicht nur P2=15. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsproblem. Wenn ein Modell in einer Tool-Pipeline erfundene oder nicht verifizierte Fakten als recherchiertes Ergebnis ausgibt, verliert die gesamte Infrastruktur ihren Vertrauensanker.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Aufrufen prüft, reagiert Claude Opus 4.6 produktionsgerecht. Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. Das ist für reale MCP-Pipelines akzeptabel und wichtig, weil Tool-Fehler im Betrieb unvermeidlich sind.

**Betriebsprofil**

Total 193.11s pro Run. Einzelaufrufe 14.39s und 16.63s, MCP-Latenz 1.17s. Langsam. Kosten pro Run 0.273305 USD. Teuer. Für diese Leistung nur dann vertretbar, wenn Planungsstärke wichtiger ist als Durchsatz.

**Fazit & Empfehlung**

Geeignet für agentische Orchestrierung, Tool-Auswahl, mehrstufige Recherche und Pipelines mit nachgelagerter Validierung oder Human Review. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere High-Trust-Pipelines, in denen Tool-Ergebnisse strikt quellengebunden bleiben müssen. Wer Claude Opus 4.6 einsetzt, sollte es als starken Planer und Executor behandeln, nicht als letzte Instanz für faktenkritische Synthese.