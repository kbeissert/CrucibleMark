**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:46:59


Bedingt deploy, weil GPT-4o Mini valide Tool-Calls liefert, aber bei der Synthese und beim Verankern im Tool-Ergebnis nicht stabil genug ist, um unbeaufsichtigt vertrauenswürdige MCP-Pipelines zu tragen.

**Tool-Execution-Profil**

Die operative Seite ist brauchbar. P1 liegt mit 83.33 klar über der Schwelle, Tool-Calls waren valide und es war kein Retry nötig. Das spricht für saubere MCP-Protokolltreue und dafür, dass das Modell Aufrufe formal korrekt absetzt.

Bei der Werkzeugwahl zeigt es jedoch mehr Ausführungssicherheit als Werkzeugintelligenz. Im Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt werden muss, bleibt die Ausbeute schwach. Das Modell erkennt den notwendigen Suchschritt nicht zuverlässig. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, arbeitet es dagegen solide. Das Muster ist klar: Wenn der Pfad relativ direkt ist, liefert es. Wenn erst entschieden werden muss, welches Tool überhaupt das richtige ist, sinkt die Zuverlässigkeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 liegt bei 48.33 und das sieht man an den Ausreißern: HTTP Fetch & Extract ist stark, aber Web Search & Tool Selection und Multilingual Search & Synthesis brechen deutlich ein. GPT-4o Mini kann gefundene Inhalte punktuell korrekt zusammenziehen, verliert aber bei mehrstufiger Recherche, Quellenabgleich und sprachübergreifender Verdichtung an Präzision. Für produktive Pipelines heißt das: brauchbar für Extraktion, nicht belastbar für komplexe Synthese.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus parametriertem Vorwissen beantwortet werden, erreicht es nur P2=40 bei Content-Verification-State B2. Zwar wurde dort keine Halluzination markiert, aber der globale Halluzinationsbefund bleibt ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgeben kann, verliert die gesamte Infrastruktur ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Aufruf prüft, reagiert das Modell akzeptabel. Es halluziniert keinen Seiteninhalt und bleibt bei der Fehlerkommunikation grundsätzlich ehrlich. P2=60 ist nicht stark, aber für Produktion vertretbar, solange der aufrufende Dienst Fehlerpfade selbst kontrolliert und Antworten nicht ungeprüft weiterreicht.

**Betriebsprofil**

Call 1: 1.87s. MCP-Latenz: 1.16s. Call 2: 3.56s. Total: 39.51s.  
Kosten pro Run: $0.001794.  
Direkte Einordnung: günstig, aber für die gemessene Syntheseleistung nicht schnell genug in langen Tool-Ketten.

**Fazit & Empfehlung**

Geeignet für kostensensitive Pipelines mit klaren Tools, einfachen Fetch- und Extraktionsaufgaben und harter nachgelagerter Validierung. Nicht geeignet für Compliance-nahe Recherche, dynamische Tool-Auswahl, mehrsprachige Wissensverdichtung oder autonome Agentenpfade, in denen das Modell selbst entscheiden und anschließend belastbar zusammenfassen muss. Wenn Sie es einsetzen, dann als günstigen Executor unter enger Führung, nicht als vertrauenswürdige Orchestrierungsinstanz.