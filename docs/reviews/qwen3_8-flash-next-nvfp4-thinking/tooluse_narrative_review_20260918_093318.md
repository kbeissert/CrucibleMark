**Deployment-Urteil**

> **Erstellt am:** 18.09.2026, 09:33:18


Bedingt deploy, weil die Tool-Nutzung stark ist und keine Halluzination erkannt wurde, aber die Tool-Calls nicht durchgängig valide waren und die Synthesequalität für vertrauenskritische Pipelines zu uneinheitlich bleibt.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz statt bloßem Musterfolgen. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis erst gesucht statt direkt gefetcht werden muss, wählt es das richtige Tool zuverlässig. Das ist ein gutes Signal für dynamische MCP-Pipelines. Auch EU License Research und Multilingual Search & Synthesis liefen auf P1-Niveau sauber durch.

Die Schwäche liegt nicht in der grundsätzlichen Orchestrierung, sondern in der formalen Ausführung. Tool-Call valide: false ist hier der entscheidende Produktionshinweis. Das passt zum Befund aus URL Construction & Fetch: Beim Test, ob es eine Ziel-URL aus Eigenwissen korrekt ableitet und dann fetch sauber ausführt, arbeitet es brauchbar, aber nicht deterministisch genug. Für Pipelines mit loser Toleranz ist das akzeptabel. Für streng typisierte Tool-Schemas und fest verdrahtete URL-Pfade ist es ein Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. Der P2-Wert von 62.50 passt zum Muster über die Assets: solide bei HTTP Fetch & Extract, Tool Failure Handling (404), URL Construction & Fetch und Multilingual Search & Synthesis, aber mit erkennbarer Unschärfe bei der eigentlichen Verdichtung. Das Modell extrahiert und kombiniert, formuliert aber nicht immer präzise genug für Compliance-, Legal- oder Audit-Ausgaben.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb es auf der sicheren Seite. P2=60 ist kein Qualitätsausweis, aber halluzinationsfrei. Das ist wichtig: Das Modell wirkt eher vorsichtig und leicht unpräzise als erfinderisch. Für produktive Tool-Infrastrukturen ist das die bessere Fehlerrichtung.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Test Tool Failure Handling (404), der prüft, ob ein fehlgeschlagener Tool-Call transparent kommuniziert wird, hat das Modell keinen Ersatzinhalt halluziniert. P2=80 zeigt: Es kann mit Scheitern umgehen und den Fehlerzustand sichtbar halten. Genau das braucht eine robuste Pipeline.

**Betriebsprofil**

Total: 160.38s. Call 1: 3.03s. MCP-Latenz: 1.01s. Call 2: 22.69s. Lokal betrieben, daher direkte Run-Kosten unkritisch. Für die gezeigte Leistung ist das Betriebsprofil langsam.

**Fazit & Empfehlung**

Geeignet für agentische Recherche-, Search-and-Fetch- und mehrsprachige Tool-Pipelines, in denen saubere Werkzeugwahl und transparente Fehlerbehandlung wichtiger sind als hochpräzise Endverdichtung. Nicht die erste Wahl für Compliance-nahe, rechtliche oder deterministische Produktionsstrecken, in denen jeder Tool-Call schemafest sein und jede Synthese eng am Quellmaterial bleiben muss. Deploy als Orchestrierungsmodell mit nachgelagerter Validierung oder zweitem Prüfschritt. Nicht als alleinige vertrauensgebende Instanz.