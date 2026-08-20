**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:21:54


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Calls nicht durchgängig valide sind und die Synthesequalität für produktive Tool-Pipelines zu ungleich ausfällt.

**Tool-Execution-Profil**

Kimi K2.7 Code zeigt echtes Werkzeugverständnis, nicht nur starres Abarbeiten. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, entscheidet es korrekt und sicher. Das spricht für brauchbare Orchestrierung in offenen Retrieval-Pfaden. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL mit anschließendem Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für Pipelines mit harter Schema- oder Routing-Erwartung. Dass der Tool-Call insgesamt als nicht valide markiert ist, wiegt deshalb schwerer als der hohe P1-Wert vermuten lässt. Das Modell versteht, welches Werkzeug nötig ist. Es produziert aber nicht zuverlässig genug MCP-konforme Aufrufe, um ohne Guardrails direkt in kritische Automationsketten zu gehen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung zeigt, dass Kimi Ergebnisse meist sinnvoll zusammenführt, aber Präzision bei Extraktion und Verdichtung sichtbar verliert. Das sieht man besonders bei HTTP Fetch & Extract und noch deutlicher bei Multilingual Search & Synthesis, wo die Recherche gelingt, die deutschsprachige Endverdichtung aber schwach bleibt. Für Engineering-Workflows mit nachgelagerter menschlicher Prüfung ist das tragbar. Für autonome Entscheidungsausgaben ist es zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellgedächtnis kommen, halluziniert es nicht. Das ist das wichtigste Vertrauenssignal in diesem Lauf. P2 60 zeigt zwar keine strenge Quellentreue im Wortlaut, aber keinen Befund, dass es erfundene Aktualität in Tool-Ergebnisse mischt.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen gescheiterten Tool-Call statt erfundenen Ersatzinhalt misst, bleibt Kimi auf der sicheren Seite: keine Halluzination trotz Fehler. Das ist produktionsrelevant positiv. Schwach ist die Nutzbarkeit der Fehlerkommunikation selbst. P2 40 heißt: Es sagt nicht gut genug, was fehlgeschlagen ist, was noch unklar bleibt und welcher nächste Schritt nötig wäre. Sicher, aber operativ nicht sauber.

**Betriebsprofil**

Call 1 1.89s. MCP-Latenz 1.31s. Call 2 15.14s. Total 110.05s. Langsam für die gezeigte Gesamtqualität. Kosten/Run: local. Kostenseitig attraktiv bei Eigenbetrieb, aber die Laufzeit ist für interaktive Agenten und enge SLAs ungünstig.

**Fazit & Empfehlung**

Geeignet für coding-nahe Agenten, Recherche- und Tool-Selection-Pipelines mit Human-in-the-Loop, besonders wenn lokaler Betrieb wichtig ist. Nicht geeignet für Compliance-, Dokumentations- oder Support-Pipelines, die aus Tool-Ergebnissen präzise, belastbare Endtexte erzeugen müssen. Wenn du es einsetzt, dann mit strikter Tool-Call-Validierung, Antwort-Schema-Prüfung und einer zweiten Instanz für Final-Synthesis.