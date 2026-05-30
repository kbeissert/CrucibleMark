**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:59


Bedingt deploy, weil Hermes 4 70B valide Tool-Calls liefert und keine Halluzination im Lauf gezeigt hat, die Gesamtreife mit 68.29 aber nur dann tragfähig ist, wenn die Pipeline Retries und nachgelagerte Validierung sauber abfängt.

**Tool-Execution-Profil**

Das stärkste Signal ist P1 84.17: Das Modell kann Tool-Aufrufe grundsätzlich korrekt formulieren und bleibt MCP-konform. Der valide Tool-Call spricht dafür, dass es Infrastruktur nicht durch formale Protokollfehler beschädigt. Kritisch ist jedoch `retry_required=true`. Ohne Asset-Einzelwerte bleibt offen, ob der Retry aus einem reinen Formatfehler oder aus unsauberer Aufgabeninterpretation kam. Für den Produktionseinsatz ist das ein Unterschied: Ein Formatproblem lässt sich meist mit strikterem Schema-Prompting und Parser-Härtung beheben, ein Verständnisproblem nicht. Aus dem vorhandenen Datensatz wirkt es eher wie ein Recoverability-Thema als wie grundlegendes Tool-Unverständnis.

Bei Web Search & Tool Selection und URL Construction & Fetch fehlen Einzeldaten. Deshalb lässt sich nicht belegen, ob Hermes 4 70B aktiv zwischen `web_search` und `fetch` unterscheidet oder vor allem einem gelernten Aufrufmuster folgt. Das Modellprofil als agentisch feinjustierter Generalist passt zu brauchbarer Werkzeugwahl, aber diese Intelligenz ist hier nicht ausreichend empirisch abgesichert.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 53.33 ist der schwache Teil des Runs und für einen Server-Dense-70B-Kandidaten klar unter der Schwelle, bei der man komplexe Tool-Ergebnisse ungeprüft in Nutzerantworten überführen würde. Das Modell kann also Werkzeuge verwenden, aber die inhaltliche Verdichtung, Priorisierung und saubere Ergebnisfusion ist nicht durchgehend stark genug für hochwertige Endantworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Es spricht dafür, dass das Modell die Tool-Kette nicht durch erfundene Aktualität unterläuft.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen scheiternden Tool-Call statt erfundenem Ersatzinhalt misst, hat Hermes 4 70B nicht halluziniert. Das ist für Produktion akzeptabel. Ein Modell darf an einem fehlgeschlagenen Abruf scheitern. Es darf nicht so tun, als hätte es Inhalt gesehen.

**Souveränitätsprofil**

Lokal betreibbar und mit 0.001167 Kosten pro Run sehr günstig. Gleichzeitig liegt das Modell 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist als souveräne Option brauchbar, aber nicht fleet-kompetitiv genug, um Qualitätskontrollen abzubauen.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klaren Tool-Schemata, Retry-Logik, Response-Validation und menschlicher oder regelbasierter Endkontrolle. Besonders passend ist es für souveräne interne Recherche- und Automationsketten, in denen Tool-Treue wichtiger ist als elegante Synthese. Nicht geeignet ist es als alleiniger Antwortgenerator für Compliance, Policy oder mehrquellige Entscheidungs-Workflows, wenn die finale Verdichtung ohne zusätzliche Prüfung direkt an Nutzer oder Systeme geht.