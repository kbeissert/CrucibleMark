**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:48:33


Bedingt deploy, weil das Modell Tool-Aufrufe zuverlässig und protokollkonform ausführt, aber die Verdichtung der Tool-Ergebnisse für produktive Entscheidungsstrecken zu ungenau bleibt. Combined 71.83 ist dafür solide, die operative Grenze liegt hier klar bei der Synthese, nicht bei der Tool-Nutzung.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsebene belastbar. Tool-Calls waren valide, es brauchte keinen Retry, und es zeigt keine MCP-Formatprobleme. Besonders stark ist es beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt werden muss: Hier erkennt es die passende Werkzeugklasse sicher. Das spricht gegen ein starres Muster und für echte Werkzeugwahl.

Schwächer ist es beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetch sauber ausführt. P1=80 ist brauchbar, aber nicht präzise genug für deterministische Pipelines mit strikten URL-Annahmen. Insgesamt wirkt Grok 4.1 Fast Reasoning wie ein Modell, das Tool-Intelligenz besitzt, aber bei der letzten Meile der Ausführung noch Fehlertoleranz in der Infrastruktur braucht.

**Synthesetreue**

Wie gut verdichtet es? Nur eingeschränkt. P2=53.33 zeigt ein wiederkehrendes Muster: Es beschafft die richtigen Quellen, komprimiert die Ergebnisse aber oft zu grob. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, beide mit P2=40. Für produktive Pipelines heißt das: Das Modell liefert verwertbare Roharbeit, aber keine verlässlich präzise Ergebnisverdichtung für Compliance, Policy oder andere textkritische Ausgaben.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt prüft, bleibt das Vertrauenssignal intakt. Content-Verification-State A, keine erkannte Halluzination. Das ist der entscheidende Befund: Es erfindet keine aktuellen Lizenzrestriktionen, obwohl die Zusammenfassung schwach ist. Vertrauen in die Datenherkunft ist also höher als Vertrauen in die Darstellung.

**Fehlerresilienz**

Im 404-Test, der misst ob ein fehlgeschlagener Tool-Call transparent offengelegt oder mit erfundenem Seiteninhalt kaschiert wird, reagiert das Modell akzeptabel. P2=40 zeigt keine gute Fehleraufbereitung, aber es halluziniert keinen Ersatzinhalt. Für Produktion ist das wichtig: Der Fehlerpfad bleibt ehrlich und beschädigt die Tool-Infrastruktur nicht durch erfundene Fakten.

**Betriebsprofil**

Call 1: 2.53s. MCP-Latenz: 0.92s. Call 2: 5.49s. Total: 53.65s.  
Günstig pro Run mit 0.002499 USD.  
Latenz insgesamt lang im Verhältnis zur nur soliden Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell primär recherchiert, Tools korrekt auswählt und Ergebnisse an einen nachgelagerten Validator, Reranker oder strukturierenden Schritt übergibt. Nicht geeignet als letzter Antwortgenerator in Compliance-, Policy-, oder Executive-Summary-Strecken, in denen die Verdichtung selbst belastbar sein muss. Wenn Sie ein ehrliches Tool-Modell mit guter Werkzeugwahl suchen, ist es ein Kandidat. Wenn Sie der Endantwort ohne zusätzliche Absicherung vertrauen müssen, ist es keiner.