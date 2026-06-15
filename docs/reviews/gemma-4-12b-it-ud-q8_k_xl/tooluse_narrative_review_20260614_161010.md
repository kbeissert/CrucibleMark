**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:10:10


Bedingt deploy, weil das Modell valide Tool-Calls ohne Retry erzeugt und nicht halluziniert, die nachgelagerte Verdichtung der Tool-Ergebnisse aber für produktive Entscheidungs- oder Compliance-Pipelines zu unpräzise bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist der belastbare Teil dieses Modells. Mit P1 83.33 wählt es Werkzeuge meist korrekt und bleibt MCP-konform. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis eher Suche als direkter Fetch nötig ist, erkennt es die richtige Werkzeugklasse sicher. Das spricht gegen reines Musterfolgen und für brauchbare Werkzeugwahl in offenen Recherchepfaden. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, ist es dagegen nur ordentlich. P1 80 heißt: funktional, aber nicht präzise genug für streng deterministische Flows, in denen die erste URL sofort sitzen muss. Positiv bleibt, dass der Tool-Call valide war und kein Retry nötig wurde. Das ist für lokale Agenten wichtiger als absolute Eleganz.

**Synthesetreue**

Wie gut verdichtet es? Eher schwach. P2 43.33 ist der eigentliche Engpass. Über die sechs Aufgaben hinweg bleibt das Modell bei der Zusammenführung der Tool-Ergebnisse oft zu grob, lässt relevante Differenzierungen liegen und wirkt in der Ergebnisdarstellung knapper als produktionssicher. Das sieht man auch an den konstant niedrigen P2-Werten in EU License Research, Web Search & Tool Selection, URL Construction & Fetch und Multilingual Search & Synthesis.

Bleibt es im Tool-Ergebnis? Ja, und das ist der zentrale Vertrauenspunkt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, blieb es im verifizierten Quellenraum. Content-Verification-State A bei ausbleibender Halluzination ist ein gutes Signal: Das Modell erfindet keinen Rechercheerfolg, auch wenn es die Befunde nur mäßig verdichtet.

**Fehlerresilienz**

Beim 404-Test, der misst, ob ein fehlgeschlagener Tool-Aufruf transparent behandelt oder mit erfundenem Seiteninhalt kaschiert wird, verhält sich das Modell akzeptabel. Es halluziniert trotz Fehler nicht. Die P2-Qualität bleibt auch hier niedrig, aber das ist operativ etwas anderes als ein Vertrauensbruch. Für Produktion gilt: unvollständige Fehlerkommunikation ist reparierbar, erfundener Ersatzinhalt wäre ein Ausschlusskriterium. Diesen Ausschlussbefund liefert das Modell nicht.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Setups attraktiv. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist nah genug am Flottenmittel, um als lokale Option vertretbar zu sein, sofern man die Synthese durch strikte Antwortschemata oder einen zweiten Prüfschritt absichert.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell primär recherchiert, das richtige Tool auswählt und Rohbefunde transparent zurückliefert. Weniger geeignet für Workflows, in denen die erste Antwort bereits entscheidungsreife Synthese sein muss, etwa Compliance-Auslegung, Lizenzbewertung oder präzise Executive Summaries. Für lokale souveräne Retrieval- und Agentenpfade ist es brauchbar. Für hochwertige Endverdichtung sollte ein stärkeres Review-Modell oder ein regelbasierter Validator dahinterstehen.