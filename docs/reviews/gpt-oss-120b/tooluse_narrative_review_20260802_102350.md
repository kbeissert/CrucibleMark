**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:23:50


Bedingt deploy: Das Modell führt Tools oft zielgerichtet aus, ist aber für vertrauenskritische MCP-Pipelines nicht freigabefähig, weil Halluzination erkannt wurde und Tool-Calls nicht durchgängig valide waren.

**Tool-Execution-Profil**

Die Tool-Nutzung zeigt echtes Auswahlvermögen, aber keine durchgehend saubere Protokolldisziplin. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, wählt das Modell das richtige Werkzeug sicher. Das spricht gegen ein starres Muster. Auch bei Multilingual Search & Synthesis und EU License Research greift es operativ zu den richtigen Werkzeugen.

Schwächer ist die Ausführungsschicht. Tool-Call valide: false ist für MCP-Umgebungen relevant, weil schon einzelne Form- oder Parameterfehler Orchestratoren aus dem Tritt bringen. Beim URL-Construction-Test, der die eigenständige Ableitung der Ziel-URL und anschließendes Fetch prüft, bleibt die Leistung brauchbar, aber nicht deterministisch. Das Modell zeigt also Werkzeugintelligenz, aber keine verlässliche Call-Präzision über alle Fälle.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung von 45 zeigt ein klares Muster: Rohzugriff ist stärker als Nachverarbeitung. Beim HTTP Fetch & Extract verdichtet das Modell solide, ebenso beim URL-Construction-Test. In mehreren recherchelastigen Aufgaben kippt es aber von Extraktion in freie Rekonstruktion. Für Pipelines, die exakte Zusammenfassungen aus Tool-Output verlangen, ist das zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, und genau das ist das Kernrisiko. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen beantwortet werden, halluziniert das Modell. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsproblem. Wenn ein Modell erfundene oder vorab gelernte Fakten als Ergebnis einer Tool-Recherche ausgibt, verliert die gesamte Tool-Infrastruktur ihren Vertrauenswert.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Aufruf prüft, erfindet das Modell keinen Seiteninhalt. Das ist der richtige Produktionsreflex. Die inhaltliche Einordnung bleibt schwach, aber die entscheidende Grenze hält es ein: Fehler offenlegen statt Ersatzfakten erzeugen. Für robuste Orchestrierung ist das akzeptabel.

**Betriebsprofil**

Call 1: 8.05s. Call 2: 40.00s. MCP-Latenz: 0.93s. Total: 293.89s.  
Langsam für die gelieferte Gesamtsicherheit.  
Kosten/Run: local. Günstig im Betrieb, aber die Zeitkosten sind hoch.

**Fazit & Empfehlung**

Geeignet ist das Modell für interne Tool-Pipelines mit menschlicher Abnahme, etwa Recherchevorstufen, URL-Ermittlung, Such-zu-Fetch-Routing und nicht bindende Zusammenfassungen. Nicht geeignet ist es für Compliance, Lizenzprüfung, regulatorische Auskunft, Incident-Analyse oder jede Pipeline, in der Tool-Ergebnisse als belastbare Tatsachen weitergereicht werden. Wer es einsetzt, sollte harte Validierung der Tool-Calls, Source-Gating und eine nachgelagerte Antwortprüfung erzwingen.