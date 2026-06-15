**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:19:53


Bedingt deploy, weil die Tool-Ausführung belastbar ist, aber die erkannte Halluzination im Honeypot das Vertrauen in jede faktenkritische Tool-Pipeline bricht.

**Tool-Execution-Profil**

Claude Sonnet 4.6 verhält sich auf MCP-Ebene diszipliniert. Die Tool-Calls waren valide, ein Retry war nicht erforderlich, und der P1-Wert von 83.33 zeigt eine robuste operative Basis. Entscheidend ist dabei nicht nur das Format, sondern die Werkzeugwahl: Beim Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis web_search statt fetch gewählt wird, traf das Modell die richtige Entscheidung durchgehend. Das spricht gegen starres Musterfolgen und für echte Orchestrierungslogik.

Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. P1=80 ist solide, aber kein Signal für hohe Präzision bei selbst konstruierten Endpunkten. Für Agenten-Workflows mit klaren Tool-Grenzen ist das gut einsetzbar. Für Pipelines, in denen das Modell URLs oder Query-Pfade autonom bilden muss, braucht es Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. Claude Sonnet 4.6 kann extrahierte Inhalte sehr gut zusammenführen, wenn der Input klar strukturiert ist, sichtbar bei HTTP Fetch & Extract mit P2=100. Sobald die Aufgabe stärker recherche- und interpretationsgetrieben wird, fällt die Verdichtungsqualität deutlich ab. EU License Research und Multilingual Search & Synthesis liegen jeweils bei P2=15. Das ist kein generelles Zusammenfassungsproblem, sondern ein Treueproblem unter Unsicherheit.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde eine Halluzination erkannt. Content-Verification-State B1 bei P2=15 ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder unbestätigte Fakten als Ergebnis einer Tool-Recherche ausgibt, untergräbt es die Kontrollfunktion der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt prüft, reagierte das Modell produktionsgerecht. P2=80 und keine Halluzination trotz Fehler zeigen, dass es Fehlschläge offenlegt statt Seiteninhalt zu erfinden. Das ist für reale Tool-Ketten akzeptabel.

**Betriebsprofil**

38.46s erster Call, 16.51s zweiter Call, 339.33s gesamt. Langsam für die erzielte Synthesequalität. MCP-Latenz 1.58s ist unkritisch. 0.296922 USD pro Run: moderat bepreist, aber im Verhältnis zur Vertrauenslücke nicht günstig.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit klarer Tool-Führung, strukturierter Extraktion und tolerierbaren Antwortzeiten. Nicht geeignet für Compliance-, Policy-, Lizenz-, Rechts- oder andere hochvertrauenspflichtige Rechercheketten, in denen das Modell strikt an Tool-Befunde gebunden bleiben muss. Wenn Sie es einsetzen, dann nur mit nachgelagerter Verifikation, Quellenzwang und harter Trennung zwischen Extraktion und finaler Aussage.