**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:16:30


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und die Calls valide sind, die Synthese aber mit erkannter Halluzination nicht durchgehend belastbar genug für unkontrollierte Output-Pfade bleibt.

**Tool-Execution-Profil**

o3-mini kann einer MCP-gestützten Pipeline grundsätzlich Werkzeuge anvertrauen. Die Tool-Calls waren valide, Retry war nicht nötig, und mit P1 90 zeigt das Modell eine klare operative Stärke. Besonders wichtig: Beim Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis search statt fetch gewählt wird, traf es die Werkzeugwahl sauber. Das spricht gegen ein starres Muster und für echte Situationsentscheidung. Beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL aus Wissen und den anschließenden Fetch misst, war es brauchbar, aber nicht deterministisch genug für fragile Pfade. Das Modell erkennt also meist, welches Werkzeug es braucht, ist aber bei der exakten Adresskonstruktion weniger präzise als bei der Tool-Auswahl selbst.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. P2 55.83 ist der schwache Teil dieses Profils. Das Modell beschafft Informationen besser, als es sie konsistent und eng am Befund zusammenfasst. Das sieht man auch an Web Search & Tool Selection und Multilingual Search & Synthesis, wo die Tool-Nutzung stark bleibt, die Verdichtung aber deutlich abfällt. Für Pipelines mit nachgelagerter Validierung ist das tolerierbar. Für direkte Nutzerantworten auf Basis von Tool-Output ist es zu locker.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diese Versuchung bei aktuellen Lizenzrestriktionen prüft, bleibt es hinreichend auf der Web-Quelle. Content-Verification-State A und keine Halluzination in diesem Test sind ein gutes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlschlagenden Tool-Call prüft, reagierte o3-mini produktionsgerecht. Es halluzinierte keinen Seiteninhalt und kommunizierte den Fehler offen. Das ist für reale Tool-Ketten entscheidend, weil Ausfälle in Retrieval- oder Fetch-Schritten erwartbar sind.

**Betriebsprofil**

Total 67.24s pro Run. Tool-Call-Latenzen 2.19s und 7.51s, MCP-Latenz 1.51s. Eher langsam. Kosten 0.037873 pro Run. Günstig bis moderat für ein Thinking-Modell, gemessen an der Ausführungsstärke besser als an der Synthesequalität.

**Fazit & Empfehlung**

Geeignet für recherchierende, mehrstufige Pipelines mit klaren Guardrails, strukturierter Nachprüfung und separater Antwort-Politur. Gut für Tool-Routing, Web-Recherche und fehlertolerante Orchestrierung. Nicht die erste Wahl für Compliance-nahe oder kundensichtbare Endantworten, wenn das Modell selbst die finale Verdichtung liefern soll. Deployen, wenn ein zweiter Kontrollschritt die Synthese absichert. Ohne diesen Schritt nicht als letzte Instanz einsetzen.