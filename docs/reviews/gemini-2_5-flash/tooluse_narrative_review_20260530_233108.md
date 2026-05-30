**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:31:08


Bedingt deploy, weil Gemini 2.5 Flash Tools zuverlässig und protokollkonform nutzt, aber die Synthesequalität mit Combined 71.08 und aktiv erkannter Halluzination nicht stabil genug für hochvertrauenswürdige Output-Strecken ist.

**Tool-Execution-Profil**

Beim eigentlichen Tool-Einsatz ist das Modell stark. Tool-Calls waren valide, ein Retry war nicht nötig, und P1 liegt mit 90 auf produktionsfähigem Niveau. Besonders wichtig ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es korrekt, dass erst web_search nötig ist. Das spricht gegen reines Schema-Folgen und für brauchbare situative Tool-Intelligenz.

Schwächer wird es bei URL Construction & Fetch, also dort, wo das Modell die Ziel-URL aus eigenem Wissen ableiten und dann korrekt abrufen muss. P1 80 ist brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen reproduzierbare Zieladressen erwarten. Für MCP-Orchestrierung heißt das: gut als Tool-Nutzer, weniger gut als Quelle für präzise URL-Herleitung ohne zusätzliche Leitplanken.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 52.5 zeigt ein wiederkehrendes Muster: Das Modell beschafft Informationen meist korrekt, komprimiert sie dann aber zu grob oder lässt belastbare Details liegen. Das sieht man besonders bei HTTP Fetch & Extract, das präzise Faktenextraktion aus echtem Seiteninhalt prüft, mit P2 35, und bei EU License Research mit P2 40. Für Analysten- oder Compliance-Ausgaben ist das zu knapp.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen stammen, blieb es im verifizierten Inhaltsraum. Halluzination wurde dort nicht erkannt. Das ist der wichtigere Vertrauensanker. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als scheinbare Tool-Ergebnisse formuliert, beschädigt es die Glaubwürdigkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparentes Fehlermanagement statt erfundenen Ersatzinhalt misst, halluzinierte es keinen Seiteninhalt. P2 60 ist keine starke Nutzerführung, aber produktionsfähig, weil der zentrale Punkt erfüllt ist: Es verschleiert den Fehlschlag nicht.

**Betriebsprofil**

Call 1 1.26s, MCP-Latenz 0.77s, Call 2 4.22s, Gesamt 37.51s. Für Flash nicht schnell im End-to-End-Lauf. Kosten pro Run 0.005286 USD. Günstig. Preis-Leistung ist gut, Latenz unter Tool-Kette aber nicht niedrig.

**Fazit & Empfehlung**

Geeignet für kostenempfindliche MCP-Pipelines mit klarer Nachkontrolle, etwa Recherche-Vorstufen, Tool-Orchestrierung, Suchrouting und mehrsprachige Beschaffung. Nicht geeignet für Endausgaben, die präzise Verdichtung, belastbare Faktenkompression oder compliance-nahe Freigaben ohne zweiten Prüfschritt verlangen. Deploy als arbeitendes Beschaffungsmodell, nicht als letzte inhaltliche Instanz.