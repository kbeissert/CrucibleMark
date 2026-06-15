**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:09:52


Bedingt deploy, weil die Tool-Aufrufe valide und meist passend sind, die Synthesequalität aber nur begrenzt verlässlich ist und eine erkannte Halluzination das Vertrauen in toolgestützte Ausgaben einschränkt.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsebene brauchbar. Tool-Calls sind valide, MCP-konform und es brauchte keinen Retry. Das spricht gegen ein Protokoll- oder Formatproblem. Bei **Web Search & Tool Selection**, also dem Test, ob ohne Hinweis das richtige Werkzeug gewählt wird, erkennt es klar, dass zuerst gesucht statt direkt gefetcht werden muss. Das ist ein echtes Signal für Werkzeugwahl und nicht nur starres Befolgen eines Schemas. Beim **URL Construction & Fetch**, also der Ableitung einer Ziel-URL aus Vorwissen vor dem Abruf, arbeitet es noch solide, aber nicht deterministisch genug für fragile Pipelines. Das Muster ist damit klar: gute Tool-Intelligenz bei der Wahl des Werkzeugtyps, geringere Präzision bei der letzten Meile der Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist der schwache Teil dieses Modells. In **HTTP Fetch & Extract**, also bei strukturierter Faktenübernahme aus echtem Seiteninhalt, und in **Multilingual Search & Synthesis**, also sprachübergreifender Recherche mit deutscher Zusammenfassung, verliert es Präzision und verdichtet zu grob. Für produktive Pipelines heißt das: Das Modell kann Daten holen, aber nicht zuverlässig in belastbare, kompakte Ergebnistexte überführen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb es im Tool-Pfad und halluzinierte nicht. Das ist das wichtigere Vertrauenssignal. Gleichzeitig steht global eine erkannte Halluzination im Lauf. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird die gesamte MCP-Infrastruktur weniger auditierbar.

**Fehlerresilienz**

Beim **Tool Failure Handling (404)**, also dem Test auf transparente Reaktion bei fehlschlagendem Abruf, kommuniziert das Modell den Fehler akzeptabel und erfindet keinen Seiteninhalt. Das ist für Produktion entscheidend. Der P2-Wert bleibt nur mittel, aber das Kernkriterium ist erfüllt: kein halluzinierter Ersatzinhalt nach Tool-Fehler.

**Souveränitätsprofil**

Lokal betreibbar auf kleinerer Hardware und damit attraktiv für souveräne Setups. Leistungsseitig liegt es jedoch 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist nah genug für pragmatische On-Prem-Nutzung, aber nicht stark genug, um Qualitätsaufsicht in der Synthese einzusparen.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Pipelines mit klarer Tool-Orchestrierung, nachgelagerter Validierung und geringer Toleranz für Cloud-Abhängigkeit. Nicht geeignet als alleinige Instanz für Compliance-nahe Zusammenfassungen, präzise Extraktion oder direkt vertrauenswürdige Endberichte. Setzen Sie es als Tool-Executor ein, nicht als letzte semantische Kontrollschicht.