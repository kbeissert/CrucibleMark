**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:48:44


Bedingt deployen, weil die Tool-Ausführung stark ist, aber die Synthese nicht verlässlich genug am Tool-Ergebnis haftet und der Tool-Call im Lauf nicht durchgehend valide war.

**Tool-Execution-Profil**

Xiaomi MiMo V2.5 zeigt klare Orchestrierungsstärke. Es erkennt beim Web-Search-&-Tool-Selection-Test ohne expliziten Hinweis, dass statt eines direkten Fetch zunächst Websuche nötig ist. Das spricht für echte Werkzeugwahl statt eines starren Fetch-First-Musters. Auch beim URL-Construction-Test leitet es die Ziel-URL grundsätzlich selbst her und führt den Abruf brauchbar aus, aber nicht mit der Präzision, die man für deterministische Pipelines erwartet. P1 über die gesamte Suite ist stark. Das Modell plant also gut, produziert aber nicht durchgehend protokollsaubere Tool-Calls. Für MCP-Infrastrukturen heißt das: als Orchestrator brauchbar, als strikt formale Tool-Schnittstelle noch absicherungsbedürftig.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung ist mit 70 kein Ausfall, aber für ein Frontier-Agentenmodell zu schwankend. Solide bei HTTP Fetch & Extract und bei URL Construction & Fetch, deutlich schwächer bei EU License Research und Multilingual Search & Synthesis. Das Muster ist klar: Fakten aus einem einzelnen Abruf kann es brauchbar zusammenziehen, aber bei mehrdeutigen oder grenzüberschreitenden Recherchelagen verliert die Verdichtung an Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot zur EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Webquellen gezogen werden, endet ohne erkannte Halluzination. Das ist der entscheidende Vertrauenspunkt. Gleichzeitig ist P2 dort nur 40. Das Modell erfindet also nichts Offensichtliches, aber es hält die gewonnenen Befunde nicht scharf genug zusammen. Für Compliance-nahe Antworten ist das zu weich.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation statt erfundenem Seiteninhalt misst, bleibt das Modell auf der sicheren Seite. Es halluziniert trotz Fehlschlag keinen Ersatzinhalt. P2 60 zeigt jedoch, dass die Kommunikation des Fehlers nicht immer knapp und operativ sauber genug ist. Für Produktion ist das akzeptabel. Das Verhalten bricht die Tool-Integrität nicht.

**Betriebsprofil**

Call 1: 4.16s. MCP-Latenz: 1.22s. Call 2: 12.63s. Total: 108.08s. Langsam für die gezeigte Qualität. Kosten/Run: local. Günstig im Betrieb, wenn eigene Hardware bereits vorhanden ist.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen Tool-Auswahl, mehrstufige Recherche und fehlertolerante Orchestrierung wichtiger sind als hochpräzise Endverdichtung. Geeignet auch für lokale oder kontrollierte Deployments, wenn offene Gewichte und Multimodalität zählen. Nicht die erste Wahl für Compliance-, Policy-, Lizenz- oder Executive-Summary-Pipelines, in denen die Antwort strikt und eng am Tool-Befund bleiben muss. Dort sollte ein nachgelagerter Verifier oder ein stärkeres Synthesis-Modell die Endantwort übernehmen.