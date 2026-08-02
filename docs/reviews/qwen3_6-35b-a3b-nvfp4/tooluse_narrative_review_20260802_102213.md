**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:22:13


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Modell für unbeaufsichtigte MCP-Pipelines noch nicht vertrauenswürdig genug machen.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis search statt fetch gewählt wird, trifft es die richtige Entscheidung konsistent. Das spricht gegen bloßes Musterfolgen. Auch bei Multilingual Search & Synthesis und EU License Research greift es zuverlässig zu externen Quellen.

Die Schwäche liegt nicht in der Frage, ob ein Tool nötig ist, sondern in der Ausführungsschärfe. Beim URL-Construction-Test, der die präzise Ableitung einer Ziel-URL und anschließendes Fetch prüft, bleibt es brauchbar, aber nicht deterministisch genug für eng validierte Pipelines. Der Befund „Tool-Call valide: false“ ist hier der zentrale operative Makel. MCP-konformes Verhalten ist damit nicht durchgehend gesichert. Positiv ist, dass kein Retry erforderlich war. Das spricht eher für punktuelle Formfehler oder unpräzise Call-Argumente als für ein grundlegendes Orchestrierungsversagen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher nur ausreichend. P2 von 45.83 ist für produktive Retrieval- oder Compliance-Strecken zu schwach. Das Modell findet Informationen, aber es komprimiert sie nicht stabil in belastbare, präzise Antworttexte. Besonders sichtbar wird das bei EU License Research mit P2 40 und bei Web Search & Tool Selection mit P2 35. Für reine Recherche-Orchestrierung reicht das eher als für entscheidungsnahe Synthese.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, weicht es nicht in offensichtliche Trainingsantworten aus. Das ist der wichtige Vertrauenspunkt. Gleichzeitig bleibt die global erkannte Halluzination ein Sicherheitsrisiko. In einer Tool-Pipeline zählt nicht nur, ob halluziniert wird, sondern ob erfundene Inhalte als Ergebnis der Infrastruktur erscheinen. Genau das untergräbt die Beweiskette der gesamten MCP-Strecke.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt misst, reagiert das Modell produktionsgerecht. Es halluziniert keinen Seiteninhalt und bleibt bei der Fehlersituation sichtbar am Tool-Zustand. Das ist für Betrieb wichtiger als stilistische Qualität. Fehler werden damit nicht verschleiert.

**Betriebsprofil**

Total 59.29s pro Run. Call 1: 1.06s. MCP-Latenz: 1.03s. Call 2: 7.79s. Lokal betrieben, daher direkte Inferenzkosten praktisch günstig. Für die gezeigte Leistung eher langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Vorstufen-Pipelines, in denen Tool-Auswahl, Web-Zugriff und transparente Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Nicht geeignet für unbeaufsichtigte Compliance-, Policy- oder Executive-Summary-Pipelines, in denen jede Synthese als belastbare Tool-Wiedergabe gelten muss. Wenn Sie es einsetzen, dann mit strikt validierten Tool-Schemas, Output-Checks und einer nachgelagerten Verifikationsstufe für jede zusammenfassende Aussage.