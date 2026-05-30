**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:19


Bedingt deploybar, weil Ministral 3B valide Tool-Calls erzeugt, aber mit erkannter Halluzination und nur moderater Gesamtsicherheit kein vertrauenswürdiger Synthese-Endpunkt für produktive Tool-Pipelines ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Mit P1 89.17 wählt es Werkzeuge meist korrekt und bleibt MCP-konform. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, traf es die richtige Entscheidung durchgehend. Das spricht gegen reines Schema-Folgen und für brauchbare Werkzeugwahl in offenen Retrieval-Situationen. Beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL und anschließenden Fetch misst, bleibt es mit P1 80 brauchbar, aber nicht präzise genug für streng deterministische Pipelines.

Der erforderliche Retry wirkt hier eher wie ein Ausführungs- oder Formatproblem als ein grundsätzliches Verständnisdefizit. Das Modell findet meist das richtige Werkzeug, braucht aber nicht in jedem Lauf den saubersten ersten Schuss. Für orchestrierte Umgebungen mit automatischem Retry ist das akzeptabel. Für eng getaktete Single-shot-Pipelines ist es ein Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 40.00 zeigt, dass Ministral 3B Rohbefunde nicht zuverlässig in präzise, belastbare Endantworten überführt. Das Muster ist konsistent: EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis enden jeweils bei P2 15, obwohl die Tool-Nutzung dort funktional gelingt. Das Modell kann also beschaffen, aber nicht stabil verdichten.

Bleibt es im Tool-Ergebnis? Nein, und das ist der kritische Befund. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen stammen, wurde eine Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder aus dem Vorwissen rekonstruierte Aussagen als Tool-Ergebnis ausgibt, unterläuft es die Verifikationskette der gesamten Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell brauchbar. Im 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt misst, lag P2 bei 80 und es erfand keinen Seiteninhalt. Das ist für Produktion ein wichtiges positives Signal. Scheitert ein Tool-Aufruf, bleibt die Antwort anschlussfähig und ehrlich statt kompensatorisch erfunden.

**Souveränitätsprofil**

Lokal betreibbar und operativ attraktiv für souveräne Setups. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Damit ist es im lokalen Betrieb konkurrenzfähig, aber nicht stark genug, um seinen Vertrauensnachteil in Synthese-Aufgaben zu kompensieren.

**Fazit & Empfehlung**

Geeignet ist Ministral 3B für lokale, kostenkritische MCP-Pipelines, in denen das Modell primär Tools auswählt, Calls ausführt und Fehler transparent weiterreicht. Nicht geeignet ist es als letzter Antwortgenerator für Compliance-, Research- oder mehrsprachige Synthese-Pipelines, in denen jede Schlussaussage strikt an Tool-Output gebunden bleiben muss. Wenn Sie es einsetzen, dann mit hartem Response-Gating, Quellenausgabe und nachgelagerter Validierung durch ein verlässlicheres Modell oder eine regelbasierte Prüfschicht.