**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:30:17


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Protokolltreue und die Synthesetreue nicht stabil genug sind, um dem Modell unbeaufsichtigt eine MCP-Infrastruktur zu übergeben. Der kombinierte Wert ist gut, aber `tool_call_valid: false` und das erkannte Halluzinationssignal sind für Produktion ein harter Vorbehalt.

**Tool-Execution-Profil**

Ornith 1.0 9B zeigt echte Werkzeugintelligenz, nicht nur starres Abarbeiten. Beim Web-Search-and-Tool-Selection-Test erkennt es ohne expliziten Hinweis, dass zuerst Suche statt direktem Fetch nötig ist, und löst das sauber. Das spricht für brauchbare Planungslogik in dynamischen Pipelines. Beim URL-Construction-Test konstruiert es die Ziel-URL grundsätzlich richtig, bleibt aber nicht präzise genug für deterministische Abläufe. Das ist kein Verständnisabriss, sondern ein Genauigkeitsproblem in der letzten Meile.

Kritisch ist der Befund `tool_call_valid: false`. Die hohe P1-Leistung zeigt, dass das Modell Werkzeuge meist sinnvoll auswählt und einsetzt. Die formale oder schematische Ausführung ist aber nicht durchgehend MCP-sauber. Da kein Retry nötig war, liegt das Problem eher in einzelner Call-Validität als in systematischem Formatkollaps.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. Die P2-Seite ist mit 52.50 der klare Schwachpunkt. Strukturierte Extraktion aus Fetch-Inhalten gelingt noch solide, und auch bei URL Construction & Fetch hält die Verdichtung das Niveau. Sobald mehrere Quellen, Mehrsprachigkeit oder regulatorische Details zusammengeführt werden müssen, bricht die Präzision sichtbar ein. Besonders EU License Research und Multilingual Search & Synthesis zeigen, dass das Modell Ergebnisse nicht sauber genug in belastbare Endantworten überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, halluziniert es nicht offen aus dem Training. Das ist positiv. Trotzdem ist das globale Halluzinationssignal als Sicherheitsrisiko zu werten. Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als scheinbar abgerufene Ergebnisse ausgibt, ist nicht nur die Antwortqualität betroffen, sondern das Vertrauen in die gesamte Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call prüft, bleibt Ornith kontrolliert. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler grundsätzlich akzeptabel. P2 60 ist kein Glanzwert, aber für Produktion ausreichend, weil die zentrale Grenze gehalten wird: kein halluzinierter Ersatzinhalt trotz Fehler.

**Souveränitätsprofil**

Lokal betreibbar, MIT-lizenziert und mit Combined 70.75 fleet-kompetitiv. Das Modell liegt n/a-Punkte unter dem Fleet-Ø von 67.75.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Pipelines mit Human-in-the-Loop, in denen das Modell suchen, fetch auslösen und Rohmaterial vorstrukturieren soll. Gut passend für agentische Research- oder Coding-Scaffolds auf Edge-Hardware. Nicht geeignet als letzte Instanz für Compliance, Lizenzprüfung, mehrsprachige Synthese oder andere Workflows, in denen die Endantwort als verifizierte Werkzeugwiedergabe gelten muss. Wenn Sie es einsetzen, dann mit strikter Tool-Call-Validierung, Antwortbegrenzung und nachgelagerter Verifikation der finalen Synthese.