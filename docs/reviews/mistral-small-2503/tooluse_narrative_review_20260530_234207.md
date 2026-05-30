**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:07


Bedingt deploy, weil die Tool-Ausführung oft brauchbar ist, das Modell aber mit erkannter Halluzination, invalidem Tool-Call und Retry-Pflicht kein verlässlicher Erstzugriff für produktive MCP-Pipelines ist.

**Tool-Execution-Profil**

Mistral Small 3.1 führt einfache, gut spezifizierte Tool-Schritte ordentlich aus, zeigt aber keine stabile Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis zwischen web_search und fetch unterschieden wird, fällt es deutlich ab. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Fetch misst, arbeitet es dagegen solide. Das spricht nicht für adaptive Tool-Wahl, sondern eher für ein festes Muster: Wenn der Zielpfad schon eng vorgezeichnet ist, kommt es zurecht. Wenn die Pipeline erst das richtige Werkzeug erkennen muss, wird es unsicher. Dass der Tool-Call nicht durchgehend valide war und ein Retry nötig wurde, wirkt hier eher wie ein Verständnisproblem in der Tool-Orchestrierung als ein reines Formatproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die Verdichtung aus realen Tool-Ausgaben bleibt inkonsistent. Positiv fällt HTTP Fetch & Extract auf, wo strukturierte Fakten aus Fetch-Content präzise zusammengeführt werden. Schwach ist dagegen die Recherche- und Syntheseleistung in offenen und mehrsprachigen Aufgaben. Für Pipelines, in denen aus mehreren Web-Treffern ein belastbarer Ergebnistext entstehen muss, reicht das Niveau nicht stabil aus.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das eigentliche Risiko. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell. Das ist kein bloßer Qualitätsverlust, sondern ein Sicherheitsproblem. Wenn ein Modell erfundene oder vorab gelernte Inhalte als Ergebnis einer Live-Recherche ausgibt, ist die Vertrauenskette der gesamten Tool-Infrastruktur gebrochen.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der transparenten Umgang mit einem fehlschlagenden Abruf prüft, halluziniert Mistral Small 3.1 keinen Seiteninhalt. Das ist der richtige Produktionsreflex. Die Kommunikation bleibt jedoch nur mäßig hilfreich und stoppt eher, als dass sie sauber in einen alternativen Pfad überleitet. Für robuste Pipelines ist das akzeptabel, solange der Orchestrator Retries und Fallbacks selbst steuert.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. In der Leistung bleibt es jedoch 5.32 Punkte unter dem Fleet-Ø von 66.76. Der Vorteil liegt also primär in Kontrolle, Kosten und Betriebsmodell, nicht in überdurchschnittlicher MCP-Kompetenz.

**Fazit & Empfehlung**

Geeignet für kostensensitive, lokal betriebene Pipelines mit enger Tool-Führung, klaren Prompts und externer Validierung jedes Ergebnisses. Nicht geeignet als autonomer Recherche- oder Compliance-Agent, nicht für offene Web-Recherche mit freier Tool-Wahl und nicht für Workflows, in denen Tool-Ausgaben ohne nachgelagerte Verifikation direkt weiterverarbeitet werden. Wer es einsetzt, sollte Tool-Routing, Retries und Antwortprüfung strikt außerhalb des Modells absichern.