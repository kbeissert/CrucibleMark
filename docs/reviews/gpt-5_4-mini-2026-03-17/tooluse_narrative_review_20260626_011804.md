**Deployment-Urteil**

> **Erstellt am:** 26.06.2026, 01:18:04


Bedingt deploy, weil die Tool-Nutzung oft zielgerichtet ist, aber ein invalider Tool-Call plus erkannte Halluzination das Modell für vertrauenskritische MCP-Pipelines ohne zusätzliche Absicherung disqualifizieren.

**Tool-Execution-Profil**

GPT-5.4 Mini zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der die Wahl zwischen Suche und direktem Fetch ohne expliziten Hinweis prüft, wählt es das richtige Werkzeug zuverlässig. Auch beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus eigenem Wissen und den anschließenden Fetch misst, arbeitet es grundsätzlich brauchbar, aber nicht deterministisch genug für eng validierte Abläufe. Das Gesamtbild ist daher gemischt: hohe Treffer bei der Werkzeugwahl, aber keine durchgehend protokollsaubere Ausführung. Der Befund „Tool-Call valide: False“ ist hier der operative Kern. Für produktive MCP-Setups heißt das: Tool-Schema strikt validieren, Argumente vor Ausführung prüfen und bei kritischen Aktionen keinen direkten Durchgriff erlauben.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die Verdichtung fällt mit P2 55.83 sichtbar hinter die Tool-Ausführung zurück. Das sieht man an mehreren Aufgaben mit starkem Recherche- oder Extraktionsanteil: EU License Research, das aktuelle Lizenzrestriktionen aus Web-Quellen verlangt, endet trotz korrekter Beschaffung nur in einer schwachen Verdichtung. Gleiches Muster bei Multilingual Search & Synthesis und Web Search & Tool Selection. Wo der Input klar strukturiert ist, wie bei HTTP Fetch & Extract, bleibt die Ausgabe deutlich solider.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research halluziniert es nicht in alte Weltkenntnis hinein, was positiv ist. Gleichzeitig ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Pipeline ausgibt, verliert die gesamte Infrastruktur ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen gescheiterten Tool-Call statt erfundenem Ersatzinhalt misst, verhält sich das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler und kommuniziert den Ausfall ausreichend offen. Das ist produktionsfähig. Es zeigt, dass die Sicherheitsgrenze bei offensichtlichen Tool-Fehlern grundsätzlich vorhanden ist.

**Betriebsprofil**

Call 1: 2.38s  
MCP-Latenz: 2.52s  
Call 2: 3.25s  
Total: 48.91s  
Preis: $0.75/1M Input, $4.5/1M Output  
Schnell pro Einzelaufruf, aber langsamer Gesamt-Run. Günstig für API-Betrieb. Preis-Leistung nur dann gut, wenn strikte Guardrails den Zuverlässigkeitsverlust abfangen.

**Fazit & Empfehlung**

Geeignet für kostensensitive Assistenten, Recherche-Frontends und nichtkritische Tool-Pipelines mit menschlicher Sichtkontrolle oder harter Nachvalidierung der Tool-Outputs. Nicht geeignet für Compliance, Lizenzprüfung, autonomes Retrieval mit direkter Weiterverarbeitung oder andere Workflows, in denen ein einzelner erfundener Synthesesatz operativen Schaden auslösen kann. Wenn Sie es einsetzen, dann als schneller Vorarbeiter mit engen Schranken, nicht als vertrauenswürdige letzte Instanz.