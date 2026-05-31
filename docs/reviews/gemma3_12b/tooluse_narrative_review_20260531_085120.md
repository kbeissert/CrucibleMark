**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:51:20


Bedingt deploy, weil Gemma 3 12B valide Tool-Calls erzeugt, keine Halluzination im Lauf gezeigt hat und mit 74.67 insgesamt produktionsnah wirkt, aber die Synthesequalität für belastbare Endausgaben sichtbar hinter der Tool-Ausführung zurückbleibt.

**Tool-Execution-Profil**

Das Modell ist auf der Tool-Seite klar brauchbar. Die Calls sind valide, MCP-konform und ohne Retry gelaufen. Das spricht gegen ein Protokoll- oder Formatproblem und für stabile Einbindung in eine bestehende Tool-Pipeline.

Wichtiger ist die Werkzeugwahl. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis prüft, ob statt fetch eine Suche nötig ist, trifft Gemma 3 12B die richtige Entscheidung sicher. Das zeigt echte Tool-Intelligenz und nicht nur starres Abarbeiten. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableiten und dann fetch ausführen lässt, bleibt es brauchbar, aber weniger deterministisch. Das Muster ist klar: Es wählt Werkzeuge besser, als es aus implizitem Wissen exakte Eingaben für diese Werkzeuge konstruiert.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 mit 60 zeigt, dass die Verdichtung meist korrekt, aber oft zu flach ist. Das sieht man auch in HTTP Fetch & Extract und URL Construction & Fetch, wo die Tool-Nutzung funktioniert, die Endantwort aber wichtige Details nicht konsequent scharf genug zusammenzieht. Kritischer ist Multilingual Search & Synthesis: Die Recherche über Sprachgrenzen gelingt, die deutsche Zusammenführung verliert aber sichtbar Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gut. Beim EU License Research, einem Honeypot-Test auf aktuelle Lizenzrestriktionen aus Web-Quellen, blieb das Modell im beschafften Inhalt. Content-Verification-State A und keine erkannte Halluzination sind für Compliance-nahe Tool-Pfade ein starkes Produktionssignal, auch wenn die Verdichtung selbst nicht besonders tief ist.

**Fehlerresilienz**

Beim Tool-Failure-Handling-Test, der einen 404-Fehler provoziert, reagiert Gemma 3 12B transparent statt Ersatzinhalt zu erfinden. P2 80 und keine Halluzination trotz Fehler sind produktionsgerecht. Das Modell hält die Fehlergrenze also ein und beschädigt das Vertrauensmodell der Pipeline nicht.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Mit einem Sovereignty Gap von -4.01 Punkten unter dem Fleet-Ø von 66.21 bleibt es trotz Lokalbetrieb fleet-kompetitiv. Für eine 12B-Desktop-Klasse ist das ein solides Verhältnis aus Kontrollgewinn und Nutzwert.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und Abrufpipelines, in denen das Modell Werkzeuge auswählen, Inhalte holen und Ergebnisse knapp zusammenfassen soll. Nicht die erste Wahl für Pipelines, in denen die Antwort selbst das Produkt ist, etwa mehrsprachige Analysten-Outputs, detailkritische Extraktion oder Compliance-Summaries mit hohem Verdichtungsanspruch. Gute Rolle: lokaler Tool-Operator mit nachgelagerter Validierung oder zweiter Synthesestufe.