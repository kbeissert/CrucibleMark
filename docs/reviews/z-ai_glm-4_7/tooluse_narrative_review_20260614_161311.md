**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:13:11


Bedingt deploy, weil GLM-4.7 valide Tool-Calls erzeugt und im MCP-Ablauf stabil wirkt, aber die Synthesetreue mit Combined 62.75 und erkannten Halluzinationen nicht ausreicht, um ihm unbeaufsichtigt vertrauenskritische Tool-Pipelines zu übergeben.

**Tool-Execution-Profil**

Die operative Tool-Seite ist die klare Stärke. Mit P1 83.33 produziert das Modell valide Calls und zeigt kein Protokollproblem; ein Retry war nicht nötig. Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis search statt fetch gewählt wird, erreicht es P1 100. Das spricht für echte Werkzeugwahl statt bloßes Schema-Folgen. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen misst, fällt es auf P1 80 zurück. Es kann also bekannte Muster brauchbar in Fetch-Aufrufe übersetzen, arbeitet dabei aber nicht deterministisch genug für fragile Endpunkte. Für MCP-Orchestrierung ist das brauchbar, für strikt URL-sensitive Automationen nur mit Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach bis uneinheitlich. P2 42.50 ist der eigentliche Engpass. Besonders kritisch sind EU License Research mit P2 20 und Multilingual Search & Synthesis mit P2 20. Das Modell ruft Informationen ab, verliert aber bei Verdichtung, Priorisierung und präziser Rückbindung an den Quellinhalt an Zuverlässigkeit. Für Produktivsysteme heißt das: Die Beschaffung funktioniert öfter als die belastbare Auswertung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination markiert, aber der Content-Verification-State B1 und P2 20 zeigen nur schwache inhaltliche Bindung an die abgerufenen Quellen. Gleichzeitig ist global Halluzination erkannt: true ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Pipeline ausgibt, sinkt das Vertrauen in die gesamte Infrastruktur, auch wenn die Tool-Aufrufe formal korrekt waren.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei Tool-Fehlschlägen prüft, bleibt GLM-4.7 akzeptabel. P2 60 ist kein starkes Ergebnis, aber es halluziniert keinen Seiteninhalt trotz Fehler. Das ist für Produktion entscheidend. Ein fehlgeschlagener Abruf wird eher als Fehler behandelt als mit erfundenem Ersatz kaschiert.

**Betriebsprofil**

12.90s und 21.16s Einzelaufrufe, 1.44s MCP-Latenz, 212.95s total. Langsam für die gezeigte Gesamtleistung. 0.004277 USD pro Run. Günstig im Preis, aber ineffizient in Zeit pro nutzbarer Antwortqualität.

**Fazit & Empfehlung**

Geeignet für überwachte Recherche- und Tooling-Pipelines, in denen ein nachgelagerter Verifier oder ein regelbasierter Post-Processor die Antwort gegen Tool-Outputs prüft. Nicht geeignet für Compliance, Lizenzprüfung, mehrsprachige Wissenssynthese oder andere Pfade, in denen die verbale Verdichtung selbst das Endprodukt ist. Wenn Sie GLM-4.7 einsetzen, dann als Tool-bedienenden Beschaffer mit enger Quellbindungskontrolle, nicht als letzte Instanz für inhaltliche Aussagen.