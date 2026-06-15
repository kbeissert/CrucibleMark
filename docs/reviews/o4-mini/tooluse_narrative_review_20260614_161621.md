**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:16:21


Bedingt deploy, weil o4-mini zwar valide Tool-Calls liefert und im Combined-Score tragfähig wirkt, aber der erkannte Halluzinationsbefund das Vertrauen in toolgestützte Antworten für sensible Produktionspfade bricht.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klar stärkere Seite dieses Modells. Es produziert valide MCP-konforme Aufrufe und erkennt im Web Search & Tool Selection-Test, der die Wahl zwischen Suche und direktem Fetch ohne expliziten Hinweis prüft, zuverlässig das richtige Werkzeug. Das spricht gegen ein bloß starres Muster. Gleichzeitig fällt die Präzision beim URL-Construction-Test ab: Die Ziel-URL wird häufig brauchbar abgeleitet, aber nicht stabil genug für deterministische Fetch-Pipelines. Das ist kein Planungsfehler, sondern ein Genauigkeitsproblem im letzten Schritt.

Dass ein Retry erforderlich war, wirkt hier eher wie ein Ausführungs- oder Formatproblem im Ablauf als wie ein grundsätzliches Missverständnis der Aufgabe. P1 von 85 bestätigt: Das Modell kann eine Tool-Infrastruktur bedienen. Es braucht aber Guardrails für Replays, Argumentvalidierung und URL-Prüfung vor dem Netzaufruf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 von 40.83 ist für produktive Synthesis niedrig. Besonders schwach ist die Verdichtung in EU License Research und Multilingual Search & Synthesis. Das Modell holt Informationen oft korrekt ein, transformiert sie aber nicht stabil in belastbare, knappe Ergebnistexte. Für reine Extraktion oder Zwischenschritte ist das noch tragbar. Für Endnutzerantworten ist es zu fehleranfällig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht konsistent. Im Honeypot EU License Research, der gezielt prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen stammen, halluziniert das Modell trotz verfügbarer Tool-Pfade. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene oder aus dem Training stammende Fakten als Tool-Ergebnis ausgibt, verliert die gesamte MCP-Pipeline ihren Verifikationswert.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call prüft, bleibt o4-mini akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler grundsätzlich sauber. P2 von 60 ist nicht elegant, aber produktionsfähig. Für robuste Systeme ist dieses Verhalten wichtiger als sprachliche Glätte.

**Betriebsprofil**

Total 73.58s pro Run. Einzelaufrufe 4.42s und 6.85s, MCP-Latenz 1.00s. Damit nicht schnell. Kosten pro Run 0.047125 USD. Günstig bis moderat, gemessen an der gezeigten Leistung.

**Fazit & Empfehlung**

Geeignet für interne Tool-Orchestrierung, Vorverarbeitung, Web-Recherche mit nachgelagerter Validierung und Pipelines, in denen ein zweites System die Antwort gegen Tool-Rohdaten prüft. Nicht geeignet für Compliance, Lizenzbewertung, regulatorische Recherche oder andere Pfade, in denen die Antwort strikt an Tool-Belege gebunden bleiben muss. Wenn Sie o4-mini einsetzen, dann als ausführendes Werkzeugmodell, nicht als letzte vertrauensgebende Syntheseschicht.