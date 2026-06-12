**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:03:46


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber ein invalider Tool-Call bei gleichzeitig erkannter Halluzination das Vertrauensmodell für produktive MCP-Pipelines beschädigt. Der Combined-Score von 66.58 bestätigt kein Ausfallbild, aber auch keine Freigabe ohne Leitplanken.

**Tool-Execution-Profil**

Mit P1 90.00 zeigt Gemma 3 12B IT grundsätzlich, dass es Werkzeuge aktiv einbinden will und operative Schritte nicht meidet. Das ist für eine Desktop-Klasse positiv. Der kritische Punkt ist jedoch nicht die Bereitschaft zur Tool-Nutzung, sondern die Protokolltreue: Der Tool-Call war am Ende nicht valide. Damit bleibt offen, ob das Modell in einer echten MCP-Kette stabil formatiert oder nur häufig die richtige Absicht zeigt.

Für die beiden Auswahltests liegt kein Asset-Einzelwert vor. Deshalb lässt sich nicht sauber trennen, ob es beim Web-Search-&-Tool-Selection-Test eigenständig erkannt hat, dass statt fetch eine Suche nötig ist, oder ob es eher einem festen Abrufmuster folgt. Dass kein Retry erforderlich war, spricht gegen ein bloßes temporäres Formatproblem und eher für einen strukturellen Zuverlässigkeitsrand: Das Modell produziert oft brauchbare Tool-Intention, aber nicht durchgehend deterministische Übergaben.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. P2 42.50 ist für produktive Nachverarbeitung zu niedrig, wenn präzise Extraktion, Verdichtung und saubere Bindung an Tool-Outputs gefordert sind. Das Modell kann Ergebnisse offenbar einsammeln, verliert aber bei der konsistenten, belastbaren Zusammenführung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist ein gutes Vertrauenssignal. Gleichzeitig steht global ein Halluzinationsbefund im Lauf. Genau das ist das Sicherheitsrisiko: Nicht die sprachliche Qualität ist das Problem, sondern die Möglichkeit, dass erfundene Inhalte als implizite Tool-Ergebnisse erscheinen.

**Fehlerresilienz**

Beim Tool Failure Handling (404), das transparente Reaktion auf einen fehlgeschlagenen Abruf prüft, hat das Modell keinen Ersatzinhalt halluziniert. Das ist produktionsgerecht. Eine Pipeline kann mit offen kommunizierten Tool-Fehlern arbeiten. Sie kann nicht mit erfundenem Seiteninhalt arbeiten.

**Souveränitätsprofil**

Lokal gut betreibbar und damit für sensible Umgebungen attraktiv. Gleichzeitig liegt das Modell 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist nah genug für souveräne Deployments, aber kein Argument, Qualitätskontrollen zu lockern.

**Fazit & Empfehlung**

Geeignet für lokale, datensensible Pipelines mit menschlicher Abnahme, klaren Tool-Schemas und nachgelagerter Validierung der Tool-Outputs. Nicht geeignet für Compliance-, Research- oder Entscheidungsstrecken, in denen das Modell Tool-Ergebnisse frei verdichten oder unbeaufsichtigt weiterreichen soll. Wenn Sie es einsetzen, dann als kosteneffizienten lokalen Executor mit strikter Antwortvalidierung, nicht als vertrauenswürdige Syntheseinstanz.