**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:04


Bedingt deploy, weil Claude Haiku 4.5 valide Tool-Calls produziert und die Infrastruktur nicht bricht, aber die Synthesetreue mit Combined 68.92 und Halluzinationssignal für produktionskritische Wissenspipelines zu unsicher bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist der tragfähige Teil dieses Modells. Tool-Calls waren valide, MCP-protokollkonform, und ein Retry war nicht nötig. Das spricht gegen ein Formatproblem und für stabile Basiskompatibilität in einer Tool-Pipeline.

Bei der Werkzeugwahl zeigt das Modell brauchbare, aber nicht robuste Urteilsfähigkeit. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es P1 80. Das ist ein positives Signal, aber kein Beleg für verlässliche Tool-Intelligenz unter offenen Bedingungen. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließendes Fetch misst, liegt es ebenfalls bei P1 80. Daraus folgt: Es kann Werkzeuge passend einsetzen, wirkt dabei aber eher heuristisch als präzise geplant. Für deterministische Pipelines ist das ausreichend, für stark dynamische Tool-Router nur mit enger Leitplanke.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher begrenzt. P2 52.50 ist der klare Engpass. Die Einzeltests bestätigen das Muster: EU License Research 40, HTTP Fetch & Extract 35, Web Search & Tool Selection 40, Multilingual Search & Synthesis 40. Das Modell beschafft Informationen oft korrekt, verdichtet sie danach aber zu flach oder zu unscharf. Genau dort entstehen in Produktion Anschlussfehler: nicht im Call, sondern in der Antwort, die aus Tool-Output wieder operative Aussage macht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, bleibt das Ergebnis formal im sicheren Bereich: Content-Verification-State A, keine Halluzination erkannt. Trotzdem ist der P2-Wert von 40 kein Vertrauensbeweis, sondern ein Warnsignal. Zusätzlich ist der globale Halluzinationsbefund als Sicherheitsrisiko zu lesen. Sobald ein Modell erfundene Fakten als Tool-Ergebnisse ausgibt, verliert die gesamte Pipeline ihren Vertrauenskern.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Aufruf misst, reagiert das Modell produktionsgerecht. P2 80 und keine Halluzination trotz 404 bedeuten: Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. Das ist für Betrieb wichtiger als elegante Formulierung.

**Betriebsprofil**

5.43s erster Call, 3.35s zweiter Call, 1.35s MCP-Latenz, 60.75s gesamt. Schnell im Einzelaufruf, aber der End-to-End-Run ist nicht kurz. Kosten pro Run: $0.034324. Günstig bis moderat, gemessen an der nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klarer Tool-Führung, niedriger inhaltlicher Fallhöhe und starker nachgelagerter Validierung: Fetch, Search, einfache Extraktion, Fehlerweitergabe. Nicht geeignet als eigenständig vertrauenswürdige Synthese-Schicht für Compliance, Lizenzbewertung, mehrsprachige Rechercheauswertung oder andere Workflows, in denen Tool-Ergebnis und formulierte Aussage deckungsgleich sein müssen. Wenn Sie es einsetzen, dann als schnellen Tool-Operator, nicht als finalen Entscheider.