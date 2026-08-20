**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:21:34


Bedingt deploy, weil die Gesamtergebnisse gut sind und keine Halluzination erkannt wurde, aber die Tool-Calls nicht durchgängig valide waren und damit die Übergabe einer MCP-Toolkette nicht ohne Guardrails erfolgen sollte.

**Tool-Execution-Profil**

Claude Opus 5 zeigt echte Werkzeugwahl statt reinem Musterfolgen. Beim Test Web Search & Tool Selection, der prüft ob das Modell ohne Hinweis zwischen Suche und direktem Abruf unterscheidet, wählt es das richtige Tool sicher. Das spricht für brauchbare Orchestrierungslogik in offenen Workflows. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch. Genau dort liegt die operative Grenze: Die Planungsentscheidung sitzt, die letzte Protokollpräzision nicht immer. Dass der globale Tool-Call-Status auf ungültig steht, obwohl kein Retry nötig war, deutet eher auf Format- oder Ausführungsungenauigkeit als auf ein grundlegendes Verständnisproblem. Für produktive MCP-Pipelines heißt das: Tool-Auswahl kann man ihm anvertrauen, Call-Validierung nicht blind.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht auf Referenzniveau. Die P2-Leistung von 80 zeigt gute Zusammenfassung echter Tool-Ausgaben, mit klarer Stärke bei HTTP Fetch & Extract und besonders bei URL Construction & Fetch. Schwächer wird es dort, wo präzise Verdichtung über Sprach- oder Quellenwechsel gefordert ist. Sowohl EU License Research als auch Multilingual Search & Synthesis landen bei P2 60. Das ist kein Ausfall, aber für Compliance-nahe oder mehrsprachige Entscheidungswege zu wenig Reserve.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, halluziniert es nicht. Das ist das wichtigere Signal. Das Modell hält die Vertrauenskette ein, auch wenn die Verdichtung der abgerufenen Inhalte nicht durchgehend scharf genug ist.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei scheiterndem Tool-Call misst, reagiert Claude Opus 5 produktionstauglich. Es erfindet keinen Ersatzinhalt und bleibt bei nachvollziehbarer Fehlerkommunikation. Der niedrige P1-Wert zeigt, dass der Ablauf nicht elegant war, aber der entscheidende Punkt stimmt: kein fingierter Seiteninhalt trotz Fehler. Das ist akzeptabel für produktive Systeme.

**Betriebsprofil**

Total 162.83s. Call 1 3.49s, MCP-Latenz 2.63s, Call 2 21.03s. Langsam. Preis nicht lokal günstig, sondern Frontier-typisch teuer: $5.0 pro 1M Input und $25.0 pro 1M Output. Im Verhältnis zur Leistung nur dann vertretbar, wenn Long-Context und agentische Planung den Ausschlag geben.

**Fazit & Empfehlung**

Geeignet für agentische Recherche-, Routing- und Long-Context-Pipelines mit nachgelagerter Call-Validierung, Schema-Prüfung und klarer Fehlerbehandlung. Ebenfalls geeignet, wenn Tool-Auswahl wichtiger ist als perfekte erste Ausführung. Nicht die erste Wahl für Compliance-kritische Abläufe, deterministische Fetch-Ketten oder mehrsprachige Synthese ohne menschliche oder programmatische Kontrolle. Wer ihm die Infrastruktur gibt, sollte ihm nicht das letzte Wort über korrekte Tool-Formate und finale Verdichtung geben.