**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:56


Bedingt deploy, weil Hermes 4 70B valide Tool-Calls liefert und keine Halluzination im Benchmark gezeigt hat, die Gesamtausführung mit 68.29 Punkten aber nur moderat ist und Retries benötigt.

**Tool-Execution-Profil**

Das Kernsignal ist positiv: Der Tool-Call war valide, also MCP-protokollkonform genug für eine echte Tool-Pipeline. Der P1-Wert von 84.17 spricht dafür, dass das Modell Werkzeuge grundsätzlich zuverlässig ausführt, statt nur sprachlich plausibel zu wirken. Kritisch ist der Retry-Bedarf. Das sieht hier eher nach Robustheitsproblem im Ablauf aus als nach grundlegendem Tool-Verständnis, weil der finale Call gültig war und kein Halluzinationssignal vorliegt.

Bei der Werkzeugwahl bleibt die Beweislage begrenzt, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelwerte vorliegen. Deshalb lässt sich nicht sauber sagen, ob Hermes 4 70B situativ zwischen web_search und fetch unterscheidet oder primär einem festen Muster folgt. Für Produktion heißt das: Tool-Use wirkt funktional, aber nicht ausreichend belegt für dynamische Orchestrierung mit vielen Verzweigungen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. Der P2-Wert von 53.33 ist der eigentliche Schwachpunkt dieses Laufs. Das Modell kann Ergebnisse offenbar einsammeln, verdichtet sie aber nicht stabil genug für Antworten, in denen Nuancen, Priorisierung und saubere Quellenbindung wichtig sind. Für reine Retrieval-Weitergabe ist das noch brauchbar. Für entscheidungsnahe Zusammenfassungen ist es zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist besser als die Verdichtungsqualität. Beim EU License Research, einem Honeypot-Test auf aktuelle Web-Recherche statt Trainingswissen, wurde keine Halluzination erkannt. Das ist für Compliance-nahe Pipelines ein starkes Signal: Das Modell hat das Werkzeug nicht durch auswendig gelerntes Weltwissen ersetzt.

**Fehlerresilienz**

Akzeptabel für Produktion. Beim Tool Failure Handling (404), das transparente Reaktion auf einen fehlschlagenden Tool-Call statt erfundenem Seiteninhalt prüft, halluzinierte Hermes 4 70B keinen Ersatzinhalt. Genau das ist die Mindestanforderung für vertrauenswürdige Tool-Infrastruktur. Ein Modell darf an einem Tool scheitern. Es darf aber nicht so tun, als hätte das Tool funktioniert.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistungsseitig bleibt es jedoch 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist nah genug für ernsthafte Erwägung, aber nicht stark genug, um den Lokalbetrieb allein durch Modellqualität zu rechtfertigen.

**Fazit & Empfehlung**

Geeignet für souveräne MCP-Pipelines, in denen Tool-Aufrufe korrekt ausgeführt werden müssen und transparente Fehlerbehandlung wichtiger ist als hochwertige Verdichtung. Nicht geeignet als alleinige Instanz für Recherche-Synthese, Compliance-Zusammenfassungen oder Architekten-Reports mit hoher Präzisionsanforderung. Empfehlung: als lokales Ausführungsmodell hinter klaren Tool-Schemata und mit nachgelagerter Validierung oder einem stärkeren Synthese-Modell einsetzen.