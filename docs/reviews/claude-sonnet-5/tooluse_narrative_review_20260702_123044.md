**Deployment-Urteil**

> **Erstellt am:** 02.07.2026, 12:30:44


Bedingt deploy, weil die Gesamtausführung solide ist und keine Halluzination erkannt wurde, aber die Tool-Calls nicht durchgehend valide waren und die Fehlersynthese für produktive MCP-Pipelines zu unzuverlässig bleibt.

**Tool-Execution-Profil**

Claude Sonnet 5 zeigt echte Werkzeugintelligenz statt bloßem Routinenverhalten. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis zwischen Suche und Direktabruf unterschieden wird, wählt es das richtige Tool sicher. Das spricht für brauchbare Orchestrierung in offenen Pipelines. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es brauchbar, aber nicht deterministisch genug für enge Produktionspfade. Genau hier liegt der operative Vorbehalt: Es versteht den Arbeitsschritt, produziert aber nicht in jedem Fall einen vollständig verlässlichen MCP-konformen Call. Dass kein Retry nötig war, spricht gegen ein reines Formatproblem. Es ist eher eine Frage der Ausführungspräzision unter realen Tool-Bedingungen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung zeigt ein Modell, das Fakten aus Tool-Ausgaben zusammenführen kann, aber nicht konstant präzise priorisiert. Das sieht man an EU License Research und besonders an Multilingual Search & Synthesis: Recherche gelingt, die Verdichtung auf Deutsch verliert aber Schärfe und Relevanz.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen beantwortet werden, bleibt das Modell auf der sicheren Seite. Kein Halluzinationsbefund ist hier das entscheidende Vertrauenssignal. Es ist also kein Modell, das Compliance-nahe Fakten frei ergänzt, auch wenn die Zusammenfassung nicht immer stark genug ist.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, ist das Ergebnis operativ gemischt. Positiv ist der zentrale Punkt: Es halluziniert keinen Seiteninhalt trotz Fehler. Das hält die Pipeline vertrauensfähig. Negativ ist die schwache Fehlerkommunikation selbst. Für Produktion ist das akzeptabel, aber nur dann, wenn der aufrufende Orchestrator Fehlerzustände selbst strikt behandelt und nicht auf das Modell für saubere Exception-Kommunikation vertraut.

**Betriebsprofil**

Total 82.37s pro Run. Call 1: 2.64s. MCP-Latenz: 1.04s. Call 2: 10.04s. Für die gezeigte Leistung langsam. Kosten: local.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Routing-Pipelines, in denen Tool-Wahl, Web-Suche und mehrstufige Planung wichtiger sind als perfekte Verdichtung im letzten Schritt. Nicht die erste Wahl für Compliance-Synthesen, mehrsprachige Ergebnisverdichtung oder strikt deterministische Fetch-Pfade, wenn das Modell selbst fehlerfrei formulierte Tool-Calls liefern muss. Deployen, wenn ein robuster Orchestrator Validierung, Fehlerbehandlung und Ergebnisprüfung übernimmt. Nicht deployen als weitgehend unbeaufsichtigte Tool-Instanz.