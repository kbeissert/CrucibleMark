**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:05


Bedingt deploy, weil die Tool-Ausführung belastbar ist, aber die Synthesetreue mit Combined 63.29 und erkannter Halluzination nicht das Vertrauensniveau für autonome High-Trust-Pipelines erreicht.

**Tool-Execution-Profil**

Das Modell arbeitet auf der MCP-Seite solide. Tool-Call valide: true und kein Retry zeigen, dass es das Protokoll sauber trifft und keine Formatinstabilität erzeugt. Für Produktionsbetrieb ist das ein starkes Basissignal.

Bei der Werkzeugwahl zeigt es echtes Situationsverständnis statt nur eines festen Fetch-Musters. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und Direktabruf unterscheiden soll, greift es korrekt zum Suchtool. Das spricht für brauchbare Tool-Intelligenz in offenen Retrieval-Pipelines. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines mit harter URL-Präzision. Das Profil ist daher klar: gute Auswahl des richtigen Werkzeugs, etwas weniger Präzision im selbst konstruierten Einstiegspunkt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Hier liegt die eigentliche Schwäche. P2 von 39.17 ist für ein Frontier-Modell zu niedrig. Die Extraktion aus vorhandenem Material gelingt punktuell, etwa bei HTTP Fetch & Extract und URL Construction & Fetch. Sobald mehrere Quellen, Fehlerzustände oder mehrsprachige Verdichtung zusammenkommen, sinkt die Verlässlichkeit der Zusammenfassung deutlich. Das Modell kann Daten holen, aber es hält die semantische Spur beim Verdichten nicht stabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der aktuelle Lizenzrestriktionen ausdrücklich aus Web-Quellen erzwingen soll, ist das Warnsignal: P2=0 bei Content-Verification-State B2. Auch wenn in diesem Einzeltest keine Halluzination geflaggt wurde, ist der Gesamtbefund mit hallucination_flag=true ein Sicherheitsrisiko. In einer Tool-Pipeline zählt nicht nur, ob ein Call korrekt war, sondern ob die Antwort nach dem Call noch an die Quelle gebunden bleibt.

**Fehlerresilienz**

Im 404-Test, der prüft ob ein fehlgeschlagener Abruf offen kommuniziert oder durch erfundenen Seiteninhalt ersetzt wird, verhält sich das Modell akzeptabel. Es halluziniert keinen Ersatzinhalt. P2=20 zeigt aber, dass die Fehlerkommunikation schwach verdichtet und nur begrenzt hilfreich formuliert wird. Für Produktion ist das tragbar, solange nachgelagerte Systeme Fehlerzustände selbst behandeln.

**Betriebsprofil**

Call 1: 3.37s. MCP-Latenz: 1.24s. Call 2: 7.52s. Total: 72.82s.  
Kosten pro Run: 0.002596 USD.  
Direkte Einordnung: günstig, aber langsam im Verhältnis zur erzielten Synthesequalität.

**Fazit & Empfehlung**

Geeignet für assistierte MCP-Pipelines, in denen Tool-Auswahl, Abruf und erste Strukturierung im Vordergrund stehen und ein zweiter Prüfschritt die Antwort verifiziert. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere High-Trust-Pipelines, in denen die Antwort strikt an Tool-Ergebnisse gebunden bleiben muss. Wer dieses Modell einsetzt, sollte Retrieval und Synthesis entkoppeln und die finale Verdichtung durch ein stärker kontrolliertes Modell oder regelbasierte Verifikation absichern.