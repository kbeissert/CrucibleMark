**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:23:39


Bedingt deploy, weil die Tool-Ausführung stark ist, aber der ungültige Tool-Call und die erkannte Halluzination das Vertrauen in produktive MCP-Pipelines begrenzen. Der Gesamteindruck ist brauchbar, aber nicht freigabefähig für unbeaufsichtigte Entscheidungen.

**Tool-Execution-Profil**

Hermes 4.3 36B zeigt echte Werkzeugintelligenz statt bloßer Schablonen-Nutzung. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es korrekt, dass zuerst web_search nötig ist. Das spricht für brauchbare Orchestrierung in offenen Aufgaben. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Fetch misst, ist es noch solide, aber weniger präzise. P1 80 heißt hier: funktional, jedoch nicht deterministisch genug für fragile Fetch-Pfade.

Kritisch ist der Befund tool_call_valid=false. Das heißt nicht, dass das Modell Werkzeuge grundsätzlich falsch versteht. Es heißt, dass die Protokolltreue im konkreten Run nicht stabil genug war. Da kein Retry nötig war, wirkt das eher wie ein singulärer Form- oder Call-Fehler als ein wiederkehrendes Schleifenproblem. Für MCP-Infrastrukturen bleibt das dennoch ein Integrationsrisiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. Die P2-Leistung ist der klare Schwachpunkt. Besonders HTTP Fetch & Extract und Multilingual Search & Synthesis zeigen, dass das Modell abgerufene Inhalte nicht konstant präzise in belastbare Antworttexte überführt. Es findet die Quelle oft, verliert aber beim Verdichten Details, Prioritäten oder sprachübergreifende Genauigkeit.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt es im akzeptablen Bereich und halluziniert nicht. Das ist das wichtigste Vertrauenssignal. Der globale Halluzinationsbefund bleibt aber ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen erfundenen Seiteninhalt abgrenzt, reagiert das Modell akzeptabel. Es halluziniert trotz Fehlschlag keinen Ersatzinhalt. P2 60 ist nicht elegant, aber produktionsfähig. Für operative Systeme ist diese Form von Ehrlichkeit wichtiger als sprachliche Glätte.

**Betriebsprofil**

Total 275.54s pro Run. Call 1: 5.22s. MCP-Latenz: 1.23s. Call 2: 39.48s. Lokal betrieben, daher direkte Laufzeitkosten nicht relevant. Gemessen an der nur moderaten Gesamtleistung ist das langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Orchestrierungs-Pipelines, in denen ein Modell Tools auswählen und Fehler offen melden soll, aber jede inhaltliche Synthese noch durch Validatoren, Schema-Checks oder menschliche Freigabe abgesichert wird. Nicht geeignet für Compliance-, Policy- oder Executive-Summary-Pipelines, in denen das Modell Tool-Ergebnisse präzise verdichten und ohne jede erfundene Ergänzung wiedergeben muss. Wer Hermes 4.3 36B einsetzt, sollte es als Tool-Dispatcher mit nachgelagerter Verifikation behandeln, nicht als vertrauenswürdige Endinstanz.