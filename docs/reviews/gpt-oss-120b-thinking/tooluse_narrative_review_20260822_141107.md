**Deployment-Urteil**

> **Erstellt am:** 22.08.2026, 14:11:07


Bedingt deploy: Das Modell führt Tools oft stark aus, aber die erkannte Halluzination im Honeypot und der nicht valide Tool-Call brechen das Vertrauen für unbeaufsichtigte produktive Pipelines.

**Tool-Execution-Profil**

GPT-OSS 120B zeigt klare Werkzeugintelligenz, nicht nur starres Call-Muster. Beim Test Web Search & Tool Selection, der ohne Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search zuverlässig. Das ist ein starkes Signal für dynamische MCP-Pipelines. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen ableiten und dann fetch ausführen lässt, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 ist dafür ausreichend, aber nicht beruhigend.

Über die Aufgaben hinweg ist die operative Trefferquote hoch. EU License Research und Multilingual Search & Synthesis erreichen jeweils volle Tool-Ausführung. Trotzdem ist der Gesamtbefund nicht sauber, weil mindestens ein Tool-Call formal nicht valide war. Da kein Retry nötig war, wirkt das weniger wie ein wiederkehrendes Formatproblem als wie ein punktueller Protokollfehler. Für MCP bedeutet das: orchestration-fähig, aber nicht blind vertrauenswürdig.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 55 zeigt, dass das Modell Ergebnisse oft verwertbar zusammenzieht, aber nicht stabil präzise genug für belastbare Schlussfassungen. Das Muster ist uneinheitlich: Tool Failure Handling (404) ist mit P2 100 vorbildlich, HTTP Fetch & Extract mit P2 60 nur durchschnittlich, und EU License Research bricht mit P2 15 deutlich ein.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, halluziniert das Modell statt sich an den abgerufenen Bestand zu halten. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene Fakten als Ergebnis einer Tool-Pipeline ausgibt, verliert die gesamte Infrastruktur ihre Prüfspur.

**Fehlerresilienz**

Hier ist das Modell produktionsfähig. Im 404-Test, der transparenten Umgang mit einem gescheiterten Tool-Aufruf prüft, kommuniziert es den Fehler korrekt und erfindet keinen Seiteninhalt. Genau dieses Verhalten ist in produktiven Pipelines erforderlich: sichtbarer Fehler statt plausibler Falschinformation.

**Betriebsprofil**

Call 1: 12.18s. Call 2: 35.38s. MCP-Latenz: 1.06s. Total: 291.68s.  
Langsam für die gezeigte Gesamtqualität.  
Kosten/Run: local. Günstig im Betrieb, aber zeitintensiv.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Setups mit menschlicher Abnahme, Fehlerschranken und nachgelagerter Faktenprüfung. Besonders brauchbar dort, wo Tool-Auswahl wichtiger ist als finale Verdichtung. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere High-Trust-Pipelines, in denen das Modell Tool-Ergebnisse strikt konservieren muss. Wer es einsetzt, sollte Antworten gegen Tool-Rohdaten verifizieren und formale Tool-Call-Validierung erzwingen.