**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:09:43


Bedingt deploy, weil das Modell Tool-Aufrufe zuverlässig und protokollkonform ausführt, aber die Verdichtung der Tool-Ergebnisse für belastbare Produktionsantworten zu ungleichmäßig bleibt.

**Tool-Execution-Profil**

Die operative Basis ist stark. P1 mit 90 zeigt, dass das Modell valide Tool-Calls erzeugt, MCP-konform bleibt und keinen Retry brauchte. Das ist für eine Tool-Pipeline der erste harte Filter, und den besteht es.

Wichtiger ist hier die Werkzeugwahl. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis statt fetch eine Suche nötig ist, erkennt das Modell die richtige Strategie sicher. Das spricht gegen ein starres Call-Muster und für echte situative Tool-Auswahl. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt, ist es schwächer. Die URL-Konstruktion ist brauchbar, aber nicht präzise genug, um in deterministischen Pipelines als selbstverständlich zu gelten. Insgesamt wirkt das Modell bei der Tool-Wahl intelligenter als bei der exakten Vorbereitung einzelner Abrufe.

**Synthesetreue**

Wie gut verdichtet es? Nur solide. P2 mit 63.33 reicht für einfache Ergebniszusammenfassungen, aber nicht für Antworten, bei denen Nuancen, Einschränkungen oder exakt extrahierte Details erhalten bleiben müssen. Das sieht man besonders bei EU License Research, wo die Recherche zwar gelingt, die Zusammenführung der Ergebnisse aber zu flach bleibt, und bei Multilingual Search & Synthesis, wo die sprachübergreifende Recherche besser ist als die deutsche Endverdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal deutlich besser als die P2-Werte. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das Modell bleibt also an die beschafften Inhalte gebunden, auch wenn es sie nicht immer präzise genug verdichtet.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparenten Umgang mit Tool-Fehlern gegen erfundenen Ersatzinhalt prüft, halluziniert das Modell keinen Seiteninhalt. P2 60 zeigt, dass die Fehlerkommunikation nicht besonders stark formuliert ist, aber sie bleibt ehrlich. Für produktive Pipelines ist das der entscheidende Punkt.

**Souveränitätsprofil**

Lokal betreibbar und fleet-kompetent genug für souveräne Setups. Mit einem Combined-Score von 76.33 liegt es 1.37 Punkte unter dem Fleet-Ø von 67.84. Auf lokaler Infrastruktur ist das ein tragfähiges Profil, auch wenn die Community-Quant-Provenienz für sensible Deployments separat abgesichert werden sollte.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Retrieval- und Orchestrierungs-Pipelines, in denen korrekte Tool-Nutzung und ehrlicher Umgang mit Fehlern wichtiger sind als perfekte Endredaktion. Nicht die richtige Wahl für Compliance-nahe, juristische oder andere hochpräzise Synthese-Stufen, in denen aus Tool-Ergebnissen belastbare Finalantworten entstehen müssen. Als lokaler Tool-Operator oder vorgeschalteter Recherche-Agent ist es sinnvoll. Als letzte Instanz für präzise Ergebnisverdichtung eher nicht.