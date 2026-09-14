**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:29:31


Bedingt deploy, weil die Tool-Ausführung oft brauchbar ist, das Modell aber mit erkannter Halluzination und ungültigem Tool-Call kein verlässlicher Endpunkt für faktensensitive MCP-Pipelines ist.

**Tool-Execution-Profil**

Phi-4 Mini zeigt echte Werkzeugorientierung, aber keine durchgehend saubere Protokolldisziplin. Die Ausführung liegt mit P1 88.33 klar über der Syntheseleistung. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, erkennt das Modell meist korrekt, dass zuerst gesucht werden muss. Das spricht gegen ein rein starres Fetch-Muster. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Produktionspfade. Kritisch ist der Gesamtbefund „Tool-Call valide: false“. Das bedeutet: Auch wenn die Werkzeugwahl oft intelligent wirkt, ist die MCP-konforme Übergabe nicht stabil genug, um der Laufzeit ohne zusätzliche Guardrails überlassen zu werden. Positiv ist, dass kein Retry erforderlich war. Das Problem liegt daher eher in Ausführungsgenauigkeit als in bloßem Formatdrift.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 47.50 ist der eigentliche Bremsfaktor dieses Modells. Besonders auffällig sind EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis mit jeweils nur 15 Punkten in der Verdichtung. Das Modell kann also Informationen beschaffen, verliert aber bei der Rückführung in die Antwort Präzision, Quellenbindung und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als scheinbar recherchiertes Ergebnis ausgibt, unterläuft es den Kernzweck der gesamten Infrastruktur.

**Fehlerresilienz**

Hier ist das Modell produktionsnäher. Im Test Tool Failure Handling (404), der transparentes Verhalten bei fehlgeschlagenem Abruf misst, kommuniziert es den Fehler sauber und erfindet keinen Ersatzinhalt. P2 100 in diesem Pfad ist ein starkes Signal. Für operative Systeme ist das akzeptabel: Ein offener Fehler ist beherrschbar, halluzinierter Seiteninhalt wäre es nicht.

**Souveränitätsprofil**

Lokal betreibbar, MIT-lizenziert und damit organisatorisch gut integrierbar. Mit Combined 66.25 liegt es 1.50 Punkte unter dem Fleet-Ø von 67.75. Damit ist es lokal fast fleet-kompetitiv, aber nicht stark genug, um seine Vertrauensprobleme allein durch Souveränitätsvorteile zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische Assistenz-Pipelines mit klar begrenztem Tool-Scope, robuster Schema-Validierung und nachgelagerter Ergebnisprüfung. Nicht geeignet für Compliance-, Recherche-, Lizenz- oder andere faktensensitive Workflows, in denen Tool-Ergebnisse als verlässlich übernommene Wahrheit gelten. Wenn Sie es einsetzen, dann als vorvalidierten Zwischenschritt, nicht als letzte Instanz.