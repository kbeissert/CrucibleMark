**Deployment-Urteil**

> **Erstellt am:** 04.07.2026, 18:47:21


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Halluzinationssignal und ungültigem Tool-Call nicht stabil genug für unüberwachte Produktionspipelines wirkt. Der Combined-Score von 69.29 bestätigt ein brauchbares, aber nicht vertrauensfestes Gesamtbild.

**Tool-Execution-Profil**

GPT-OSS 120B zeigt echte Werkzeugintelligenz statt reinem Schema-Folgen. Beim Web-Search-&-Tool-Selection-Test erkennt es ohne expliziten Hinweis korrekt, dass erst Suche und nicht direkter Fetch nötig ist, was für dynamische MCP-Pipelines ein starkes Signal ist. Auch beim URL-Construction-Test leitet es die Ziel-URL grundsätzlich korrekt her und führt den Fetch meist brauchbar aus, aber die Präzision ist nicht durchgehend deterministisch. Das passt zum P1-Profil: 100 bei Werkzeugwahl, 80 bei URL-Konstruktion.

Kritisch bleibt die Protokollseite. Tool-Call valide: false bedeutet, dass die Pipeline trotz guter Absicht mit fehlerhaften oder nicht vollständig MCP-konformen Aufrufen rechnen muss. Da kein Retry erforderlich war, wirkt das eher wie ein Ausführungs- oder Formatfehler im Einzelcall als wie ein grundsätzliches Verständnisproblem. Für produktive Orchestrierung braucht dieses Modell deshalb einen strikten Tool-Wrapper mit Validierung vor dem tatsächlichen Aufruf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 bei 52.50 ist der eigentliche Schwachpunkt dieses Laufs. Das Modell kann Ergebnisse zusammenziehen, verliert dabei aber zu oft Präzision, Priorisierung oder Belegnähe. Das sieht man besonders an EU License Research mit P2 20 sowie Web Search & Tool Selection mit P2 35. Es beschafft Informationen oft besser, als es sie anschließend belastbar zusammenfasst.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil negativ. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Vorwissen kommen, wurde zwar keine Halluzination im Einzelfall markiert, aber der sehr niedrige P2-Wert zeigt, dass das Modell die externe Evidenz nicht sauber in eine verlässliche Antwort überführt. Da global Halluzination erkannt: true gesetzt ist, muss das als Sicherheitsrisiko gelesen werden. In einer Tool-Pipeline reicht schon gelegentlich erfundener Ergebnisinhalt, um die Verlässlichkeit der gesamten Infrastruktur zu unterlaufen.

**Fehlerresilienz**

Im 404-Test reagiert das Modell produktionsnah. Es kommuniziert den fehlgeschlagenen Tool-Aufruf transparent und erfindet keinen Seiteninhalt. Das ist akzeptabel für den Einsatz. P2 80 in diesem Szenario zeigt, dass es bei klaren Fehlerzuständen disziplinierter arbeitet als bei offener Recherche und anschließender Synthese.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Combined 69.29 liegt 2.49 Punkte über dem Fleet-Ø von 66.80. Damit ist es ohne Cloud-Abfluss fleet-kompetitiv, auch wenn die inhaltliche Verlässlichkeit nicht auf demselben Niveau liegt wie die reine Tool-Steuerung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit starker Guardrail-Schicht: Tool-Call-Validierung, Antwortprüfung gegen Tool-Output und im Zweifel menschliche Freigabe. Gut einsetzbar für Recherche, Routing und Fehlerbehandlung. Nicht geeignet für Compliance-, Regulatorik- oder andere High-Trust-Workflows, in denen die finale Synthese als belastbare Tatsache übernommen wird. Wenn Sie diesem Modell Tools geben, dann als ausführendes Glied unter Aufsicht, nicht als letzte Instanz.