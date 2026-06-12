**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:29:02


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Syntheseleistung aber zu schwach bleibt und eine erkannte Halluzination das Vertrauen in nachgelagerte Automationsschritte begrenzt.

**Tool-Execution-Profil**

Hermes 3 8B arbeitet auf Protokollebene sauber. Die Tool-Calls waren valide, ein Retry war nicht nötig. Das ist für MCP-Pipelines der erste wichtige Befund: Das Modell bricht nicht an der Schnittstelle.

Bei der Werkzeugwahl zeigt es echte Selektionsfähigkeit statt bloßem Schema-Following. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis Suche statt direktem Fetch gewählt wird, lag es bei P1 100. Auch EU License Research und Multilingual Search & Synthesis liefen auf dieser Ebene fehlerfrei. Schwächer ist es beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen ableitet: P1 40. Das Muster ist klar. Wenn ein Discovery-Tool vorhanden ist, nutzt das Modell es sinnvoll. Wenn es URLs selbst konstruieren muss, sinkt die Zuverlässigkeit deutlich. Für dynamische Tool-Stacks ist das brauchbar. Für deterministische Fetch-Pipelines mit impliziter URL-Ableitung ist es zu fehleranfällig.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung von 30 zeigt, dass Hermes 3 8B Ergebnisse zwar einsammelt, aber beim Verdichten, Priorisieren und präzisen Wiedergeben häufig Substanz verliert. Das sieht man besonders bei HTTP Fetch & Extract, Web Search & Tool Selection und Multilingual Search & Synthesis mit jeweils P2 15. Für produktive Systeme ist das kein Schönheitsfehler, sondern ein Problem bei Übergaben an Menschen oder Folgeprozesse.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen gegen trainiertes Vorwissen abgrenzt, blieb es auf dem Tool-Pfad. P2 40 ist inhaltlich nur mäßig, aber der Vertrauensbefund ist positiv: keine Halluzination, Content-Verification-State A. Gleichzeitig gilt der globale Halluzinationsbefund als Sicherheitsrisiko. Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Resultat ausgibt, wird die Infrastruktur selbst unzuverlässig. Hier liegt die zentrale Einsatzgrenze.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit Tool-Fehlern statt erfundenem Ersatzinhalt prüft, verhielt sich das Modell produktionsgerecht. P2 80, keine Halluzination trotz Fehler. Das ist akzeptabel für reale Systeme: Fehler werden kommuniziert, nicht kaschiert.

**Souveränitätsprofil**

Lokal betreibbar und damit souverän einsetzbar. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist ein kleiner Abstand und spricht für ein solides lokales Tool-Modell, sofern man die Synthese extern absichert.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines, in denen das Modell primär Tools auswählt, Calls formuliert und Fehler transparent meldet. Nicht geeignet als alleinige Instanz für faktenkritische Zusammenfassungen, Compliance-Ausgaben oder extraktionsnahe Endantworten. Empfehlung: als Tool-Operator vor einem strikten Verifier oder einem stärkeren Synthese-Modell einsetzen. Nicht als ungeprüfter finaler Antwortgenerator.