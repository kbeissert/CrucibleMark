**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:18:23


Bedingt deploy, weil die Tool-Nutzung stark ist und keine Halluzination erkannt wurde, aber die Tool-Calls nicht durchgehend valide waren und die Synthesequalität für vertrauenskritische Pipelines nur ausreichend ausfällt.

**Tool-Execution-Profil**

Gemini 3.7 Flash zeigt echtes Werkzeugverständnis, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis search statt fetch gewählt wird, erkennt es den Bedarf korrekt und liefert volle Tool-Execution-Sicherheit. Das spricht für brauchbare Orchestrierungsfähigkeit in dynamischen MCP-Pipelines.

Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließendes Fetch prüft, arbeitet es brauchbar, aber nicht deterministisch genug für harte Produktionspfade. P1 bleibt dort sichtbar hinter der Suchauswahl zurück. Das ist ein wichtiges Signal: Das Modell wählt Werkzeuge besser, als es eigenständig Zieladressen konstruiert. Für MCP-Setups mit Suchstufe vor Fetch ist das gut nutzbar. Für Pipelines, die auf präzise, modellgenerierte Endpunkte setzen, braucht es Guardrails. Dass der Tool-Call global nicht durchgehend valide war, bestätigt genau diese Grenze. Retry war nicht erforderlich. Das spricht eher gegen ein Formatproblem und eher für punktuelle Ausführungsschwächen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht präzise genug für hochwertige Analysten-Ausgaben. Die P2-Leistung von 70 zeigt: Es kann Ergebnisse zusammenziehen und in mehreren Assets brauchbar wiedergeben, verliert aber bei Compliance-nahen und mehrsprachigen Aufgaben an Schärfe. Besonders EU License Research und Multilingual Search & Synthesis fallen in der Verdichtung auf 60 zurück. Für produktive Kurzantworten reicht das. Für belastbare Entscheidungsgrundlagen oft nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt es vertrauenswürdig genug: keine Halluzination erkannt. Das ist der wichtigere Befund als die nur mittelstarke Verdichtung. Das Modell erfindet hier nichts, auch wenn es die Quelle nicht maximal sauber verdichtet.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Fehlverhalten statt erfundenem Ersatzinhalt misst, halluziniert Gemini 3.7 Flash keinen Seiteninhalt. Die Antwortqualität bleibt mit P2 60 begrenzt, aber das operative Verhalten ist richtig: Fehler werden nicht in scheinbare Fakten umgewandelt. Das ist für Tool-Pipelines entscheidend.

**Betriebsprofil**

Total 62.21s pro Run. Einzelaufrufe 2.86s und 6.20s. MCP-Latenz 1.30s. Schnell auf Call-Ebene, aber der Gesamtrun ist für ein Flash-Modell lang. Kosten/Run: local.

**Fazit & Empfehlung**

Geeignet für suchgestützte MCP-Pipelines, Agenten-Orchestrierung, Routing, Vorrecherche und robuste Tool-first-Workflows mit nachgelagerter Validierung. Nicht die erste Wahl für Compliance-Ausgaben, hochwertige Synthese oder deterministische Fetch-Pfade, in denen das Modell selbst präzise URLs oder belastbare Endfassungen liefern muss. Deploy ist sinnvoll, wenn die Infrastruktur Werkzeugwahl belohnt und Ergebnisverdichtung zusätzlich absichert.