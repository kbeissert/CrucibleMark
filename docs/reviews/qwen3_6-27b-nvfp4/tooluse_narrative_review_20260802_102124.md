**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:21:24


Bedingt deploy, weil die Tool-Ausführung insgesamt stark ist, aber der MCP-Tool-Call nicht durchgehend valide bleibt und die Synthesequalität für produktive Wissenspipelines zu ungleich ausfällt.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl-Intelligenz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, erkennt es den Bedarf für web_search sauber. Das spricht gegen starres Musterverhalten. Auch EU License Research und Multilingual Search & Synthesis laufen auf der Tool-Seite kontrolliert. Kritischer ist der Test URL Construction & Fetch: Das Modell kann eine Ziel-URL grundsätzlich herleiten und abrufen, aber nicht präzise genug für deterministische Pipelines. Das erklärt den nur teilweise sauberen Tool-Layer trotz guter P1-Leistung. Für MCP heißt das: brauchbar für agentische Recherchepfade, aber nicht robust genug für strikt validierte Tool-Contracts ohne zusätzliche Guardrails. Retry war nicht nötig. Das Problem liegt daher eher in der Erstpräzision als in bloßem Formatdrift.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. Die P2-Leistung von 51.67 zeigt sich auch im Asset-Bild: mehrheitlich 60er-Werte bei EU License Research, HTTP Fetch & Extract, URL Construction & Fetch und Multilingual Search & Synthesis. Das Modell holt Informationen aus den Tools, komprimiert sie dann aber nicht konstant präzise genug für Übergaben in nachgelagerte Systeme. Für lesbare Operator-Antworten reicht das oft. Für strukturkritische Entscheidungsnotizen eher nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Vorwissen kommen, bleibt das Modell vertrauenswürdig. Keine Halluzination erkannt. Das ist der wichtigere Sicherheitsbefund. Es zeigt Schwäche in der Verdichtung, aber keinen Bruch der Quellenbindung.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Aufruf misst, kommuniziert das Modell den Fehler, statt Seiteninhalt zu erfinden. P2 80 ist hier ein gutes Signal. Für reale MCP-Pipelines ist das entscheidend, weil Fehler sichtbar bleiben und nicht als scheinbar valide Ergebnisse weitergereicht werden.

**Betriebsprofil**

Total 147.94s pro Run. Call 1: 3.00s. MCP-Latenz: 1.36s. Call 2: 20.30s. Lokal betrieben, daher direkte Laufkosten lokal statt API-basiert. Für die erreichte Leistung eher langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Agent-Pipelines, in denen Tool-Wahl, Fehlertoleranz und Quellenbindung wichtiger sind als erstklassige Verdichtung. Nicht erste Wahl für Compliance-Summaries, strukturierte Briefings oder Automationsketten, die aus Tool-Output unmittelbar präzise Synthesen erzeugen müssen. Deploy nur mit Output-Prüfung, Schema-Validierung und klaren Fallbacks für URL-Konstruktion und Zusammenfassungsqualität.