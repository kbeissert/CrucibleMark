**Deployment-Urteil**

> **Erstellt am:** 15.08.2026, 12:32:09


Bedingt deploy, weil die Tool-Ausführung stark ist, aber der nicht valide Tool-Call und die nur mittlere Synthesetreue das Vertrauen für unbeaufsichtigte Produktionspipelines begrenzen.

**Tool-Execution-Profil**

Upstage Solar Pro4 zeigt echte Werkzeugintelligenz statt bloßem Musterfolgen. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, entscheidet das Modell korrekt und sicher. Das spricht für brauchbare Orchestrierung in offenen Aufgabenlagen. Auch bei Multilingual Search & Synthesis bleibt die Tool-Nutzung diszipliniert.

Schwächer wird es bei der formalen Ausführung. Beim URL-Construction-Test, der prüft ob das Modell die Ziel-URL selbst ableitet und dann fetch korrekt ausführt, ist die Leistung brauchbar, aber nicht deterministisch genug für fragile MCP-Ketten. Der Gesamtbefund passt dazu: hohe P1-Stärke, aber mindestens ein Tool-Call war nicht valide. Da kein Retry nötig war, wirkt das weniger wie ein grundlegendes Verständnisproblem als wie ein Präzisionsproblem in der finalen Call-Form.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung liegt sichtbar unter der Ausführungsstärke. HTTP Fetch & Extract sowie Multilingual Search & Synthesis zeigen, dass das Modell Ergebnisse meist korrekt zusammenzieht, aber nicht konsistent präzise genug für faktenempfindliche Verdichtung. Das Risiko liegt nicht in freier Erfindung, sondern in weicher Zusammenfassung, Auslassung oder unklarer Gewichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht zuverlässig genug. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, fällt die Verdichtung mit P2 40 klar ab. Es halluziniert zwar nicht offen, aber das Vertrauen leidet trotzdem: In Compliance-nahen Pipelines reicht es nicht, nur nichts zu erfinden. Das Modell muss sichtbar am abgerufenen Material bleiben.

**Fehlerresilienz**

Bei Tool-Fehlern ist das Modell produktionsfähig. Im 404-Test, der prüft ob ein fehlgeschlagener Tool-Call transparent behandelt wird, kommuniziert es den Fehler sauber und erfindet keinen Seiteninhalt. Das ist der richtige Sicherheitsmodus für reale MCP-Pipelines. Fehler werden als Zustand behandelt, nicht mit plausibel klingendem Ersatz verdeckt.

**Betriebsprofil**

Total 68.89s pro Run. Call-Latenzen 1.71s und 8.33s, MCP-Latenz 1.43s. Für die gezeigte Leistung langsam. Kosten aktuell sehr günstig bei $0.03/1M Input und $0.12/1M Output, aber nur im Einführungsfenster.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Routing-Pipelines, in denen Tool-Wahl wichtiger ist als perfekte Verdichtung und ein nachgelagerter Validator vorhanden ist. Nicht erste Wahl für Compliance, regulatorische Auswertung oder andere Workflows, in denen die Zusammenfassung selbst als belastbarer Endzustand gilt. Deployen, wenn Sie Tool-Calls und Final-Synthesis strikt kontrollieren. Nicht deployen als unbeaufsichtigten Synthese-Endpunkt.