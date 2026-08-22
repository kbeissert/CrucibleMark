**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:48:21


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauen in produktive MCP-Pipelines begrenzen. Der Combined-Score von 68.50 stützt kein unkontrolliertes Durchreichen an kritische Tool-Infrastruktur.

**Tool-Execution-Profil**

Hermes 4 405B versteht Werkzeugwahl grundsätzlich gut. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis Suche statt Direkt-Fetch gewählt wird, trifft es die richtige Entscheidung zuverlässig. Das spricht gegen ein starres Muster und für echte Situationsbewertung. Auch beim Test EU License Research greift es sauber zu externen Quellen, statt nur aus dem Training zu antworten.

Schwächer wird es bei der operativen Präzision. Beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL und den anschließenden Fetch misst, ist die Leistung brauchbar, aber nicht deterministisch genug für fragile Pipelines. Dazu passt das Signal tool_call_valid=false: Das Modell ist nicht durchgehend MCP-protokollsauber. Das ist kein Planungsproblem, sondern ein Ausführungsrisiko an der Tool-Grenze. Positiv ist, dass kein Retry erforderlich war. Das Verhalten wirkt also nicht instabil, sondern punktuell unpräzise.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mäßig. Die P2-Leistung von 60 zeigt ein klares Gefälle zwischen Beschaffung und Verarbeitung. Besonders bei HTTP Fetch & Extract und Multilingual Search & Synthesis, wo exakte Extraktion und sprachübergreifende Verdichtung gefordert sind, verliert das Modell Präzision. Für reine Retrieval-Pipelines ist das tolerierbar. Für Berichte, Compliance-Zusammenfassungen oder entscheidungsrelevante Verdichtung ist es zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es formal auf dem richtigen Pfad und halluziniert nicht aus dem Stand heraus. Das ist das wichtige Vertrauenssignal. Gleichzeitig ist hallucination_flag=true global ein Sicherheitsrisiko: Sobald ein Modell auch nur punktuell erfundene Fakten als Tool-Ergebnis ausgeben kann, wird die gesamte Tool-Kette überprüfungsbedürftig.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert Hermes 4 405B produktionsgerecht. Im 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt prüft, erfindet es keinen Seiteninhalt und kommuniziert den Fehlschlag sauber. Das ist für den Betrieb akzeptabel und deutlich wichtiger als eine elegante Formulierung.

**Betriebsprofil**

Total 62.80s pro Run. Call 1: 3.14s, MCP-Latenz: 1.13s, Call 2: 6.21s. Für die gezeigte Leistung langsam. Kosten/Run: local, daher finanziell günstig, aber infrastrukturell schwergewichtig.

**Fazit & Empfehlung**

Geeignet für agentische Retrieval-Pipelines mit klaren Guardrails, Logging und nachgelagerter Validierung der Tool-Ergebnisse. Nicht geeignet für Compliance-, Policy- oder Executive-Summary-Pipelines, in denen die erste Synthese bereits belastbar sein muss. Wenn Sie Hermes 4 405B einsetzen, dann als starken Tool-Benutzer mit kontrollierter Ausgabeschicht, nicht als vertrauenswürdige Endinstanz für verdichtete Fakten.