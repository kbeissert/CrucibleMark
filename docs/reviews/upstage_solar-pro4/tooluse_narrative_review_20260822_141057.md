**Deployment-Urteil**

> **Erstellt am:** 22.08.2026, 14:10:57


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein ungültiger Tool-Call und erkannte Halluzinationen das Vertrauen in produktive MCP-Pipelines begrenzen. Der Gesamteindruck ist gut, die Sicherheitslage nicht.

**Tool-Execution-Profil**

Upstage Solar Pro4 zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die richtige Wahl zwischen Suche und Direktabruf prüft, erkennt es den Bedarf für web_search zuverlässig. Das ist ein starkes Signal für agentische Orchestrierung. Beim URL-Construction-Test, der die korrekte Ableitung einer Zieladresse und anschließenden fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für sensible Pfade.

P1 von 90 spricht für hohe operative Kompetenz. Der Haken ist die Protokolltreue: Tool-Call valide ist False. Damit liegt das Risiko nicht in der Frage, ob das Modell Tools grundsätzlich einsetzen will, sondern ob einzelne Calls sauber genug für eine strikte MCP-Infrastruktur formatiert und ausgeführt werden. Da kein Retry erforderlich war, wirkt das eher wie ein punktuelles Validitätsproblem als ein systematisches Verständnisversagen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. P2 von 66.67 ist der klare Abstandshalter zur starken Ausführung. Bei EU License Research, also einer aktuellen Web-Recherche zu Lizenzrestriktionen, verdichtet es die Ergebnisse nur mäßig. Bei HTTP Fetch & Extract bleibt die Extraktion solide, aber nicht präzise genug, um ohne nachgelagerte Validierung als Referenzantwort zu dienen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es formal im sicheren Bereich: keine Halluzination erkannt. Das ist wichtig. Gleichzeitig steht global Halluzination erkannt auf True. Damit wird das Thema nicht zu einem Qualitätsmangel, sondern zu einem Sicherheitsrisiko. Wenn ein Modell erfundene Inhalte als Tool-Ergebnis ausgibt, verliert die gesamte Pipeline ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Hier fällt das Modell durch. Beim 404-Test, der transparenten Umgang mit einem gescheiterten Tool-Aufruf prüft, halluziniert es trotz Fehler Seiteninhalt. P2 von 15 ist in diesem Fall zweitrangig. Entscheidender ist der Befund selbst: halluzinierter Ersatzinhalt statt klarer Fehlermeldung. Das ist für Produktion kritisch ohne Ausnahme.

**Betriebsprofil**

Total 232.48s pro Run. Langsam. Call 1: 2.91s, MCP-Latenz: 1.44s, Call 2: 34.40s.  
Kosten/Run: local. Günstig. Im Verhältnis zur Leistung attraktiv, im Verhältnis zur Laufzeit träge.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Routing-Pipelines, in denen Tool-Wahl wichtiger ist als harte Verlässlichkeit der Endantwort und ein Guardrail-Layer jede Ausgabe prüft. Nicht geeignet für Compliance, Support-Automation, Incident-Flows oder jede Pipeline, in der ein Tool-Fehler strikt als Fehler stehen bleiben muss. Wer Solar Pro4 einsetzt, sollte Tool-Output-Verifikation, strikte 404-Abbruchlogik und Antwort-Gating verbindlich davor schalten.