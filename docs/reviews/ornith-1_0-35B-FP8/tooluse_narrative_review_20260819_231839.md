**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:18:39


Bedingt deploy, weil die Tool-Ausführung oft brauchbar ist, das Modell aber bei Tool-Wahl und Ergebnisverdichtung nicht verlässlich genug für autonome MCP-Pipelines arbeitet. Der fehlende Halluzinationsbefund entschärft das Risiko, die ungültigen Tool-Calls und der nur moderate Gesamteindruck nicht.

**Tool-Execution-Profil**

Ornith 1.0 35B kann Tools ausführen, aber nicht konsistent protokolltreu. P1 von 80.83 zeigt operative Grundfähigkeit. Das Problem liegt nicht im simplen Abruf, sondern in der Wahl des richtigen Werkzeugs. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis search statt fetch gewählt wird, fällt das Modell mit P1 35 klar ab. Das spricht gegen robuste Werkzeugintelligenz und eher für ein festes Muster: bekannte URLs oder direkte Fetch-Pfade funktionieren, offene Recherchepfade deutlich schlechter. Das bestätigt der Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus internem Wissen prüft, mit P1 80. Auch HTTP Fetch & Extract und Multilingual Search & Synthesis zeigen, dass es vorhandene Quellen brauchbar verarbeitet, wenn der Zugriffspfad bereits klar ist. Für dynamische Tool-Router ist das zu schwach. Für vorstrukturierte Pipelines mit enger Tool-Auswahl ist es brauchbar.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 62.50 ist der eigentliche Engpass. Ornith extrahiert oft genug relevante Fakten, verdichtet sie aber nicht stabil in präzise, entscheidungsreife Antworten. Das sieht man besonders bei EU License Research mit P2 40, obwohl der Tool-Zugriff selbst gelingt, und bei Tool Failure Handling (404) ebenfalls mit P2 40.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil besser als die Verdichtungsqualität. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist ein starkes Signal für Compliance-nahe Pipelines. Es bedeutet aber nicht, dass die Antwortqualität hoch ist. Es bedeutet nur, dass das Modell die Infrastruktur nicht durch erfundene Quelleninhalte unterläuft.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit gescheiterten Tool-Calls misst, halluziniert Ornith keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die Kommunikation des Fehlers bleibt aber zu schwach verdichtet und nicht immer entscheidungsorientiert. Akzeptabel für überwachte Systeme. Zu unsicher für vollautonome Agent-Loops.

**Souveränitätsprofil**

Lokal betreibbar, MIT-lizenziert und ohne Cloud-Zwang einsetzbar. Gleichzeitig liegt es  -1.85 Punkte unter dem Fleet-Ø von 67.58. Das ist nah genug am Flottenschnitt, um für souveräne Umgebungen ernsthaft relevant zu sein, aber nicht stark genug, um Qualitätsdefizite durch Betriebsfreiheit zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines mit festen Tool-Pfaden, menschlicher Abnahme und klaren Fallbacks. Nicht geeignet als autonomer Orchestrator, der selbst zwischen Search, Fetch und Fehlerbehandlung sicher wählen muss. Wenn Sie ein lokales Modell für dokumentennahe Recherche, mehrsprachige Synthese und kontrollierte Tool-Nutzung suchen, kann Ornith arbeiten. Wenn die Pipeline eigenständige Werkzeugwahl und belastbare Endverdichtung verlangt, sollten Sie es nur hinter Guardrails und mit Supervisor einsetzen.