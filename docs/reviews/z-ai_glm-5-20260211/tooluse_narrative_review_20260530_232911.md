**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:29:11


Bedingt deploy, weil GLM-5 valide Tool-Calls ohne Halluzinationsbefund produziert, aber die Synthesetreue mit 66.67 zu inkonsistent ist, um unbeaufsichtigt sensible Ergebnisverdichtung zu tragen.

**Tool-Execution-Profil**

Die Tool-Ausführung ist produktionsnah. Mit P1 90 zeigt GLM-5, dass es MCP-konform arbeitet, valide Calls erzeugt und keinen Retry benötigt. Das stärkste Signal ist Web Search & Tool Selection: Beim Test, der prüft, ob ohne Hinweis web_search statt fetch nötig ist, wählt es das richtige Werkzeug zuverlässig. Das spricht gegen starres Musterfolgen und für echte Werkzeugwahl unter Unsicherheit. Beim URL-Construction-Test, der die korrekte Ziel-URL aus eigenem Wissen verlangt, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 ist für flexible Research-Pipelines tragfähig, für eng spezifizierte Fetch-Ketten mit exakter URL-Ableitung aber zu fehleranfällig. Insgesamt ist die Tool-Schicht belastbar. Die Schwäche liegt nicht im Aufruf, sondern in dem, was danach aus den Ergebnissen gemacht wird.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur solide. Die Breite ist sichtbar: HTTP Fetch & Extract und Tool Failure Handling (404) liegen bei P2 80, Multilingual Search & Synthesis bei 60, EU License Research nur bei 40. GLM-5 kann gefundene Inhalte zusammenziehen, verliert aber gerade bei Recherche mit regulatorischem oder mehrdeutigem Material an Präzision. Für Architekturen, in denen das Modell Rohdaten knapp zusammenfasst und ein nachgelagerter Validator prüft, ist das akzeptabel. Für direkte Entscheidungsoutputs ist es zu ungleichmäßig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, halluziniert es nicht und der Content-Verification-State ist A. Das ist das zentrale Vertrauenssignal. Der schwache P2-Wert bedeutet hier nicht erfundene Fakten, sondern unzureichend saubere Verdichtung eines korrekt beschafften Befunds.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei gescheitertem Tool-Call prüft, reagiert GLM-5 produktionsgerecht. Es erfindet keinen Seiteninhalt und kommuniziert den Fehlschlag nachvollziehbar. P2 80 ist dafür ausreichend. Für produktive Pipelines ist genau dieses Verhalten entscheidend, weil die Infrastruktur dadurch vertrauenswürdig bleibt, auch wenn einzelne Quellen ausfallen.

**Betriebsprofil**

Total 242.58s. Einzelaufrufe 12.68s und 26.75s. MCP-Latenz 1.01s. Langsam für einen Generalist-Frontier-Einsatz. Kosten pro Run 0.007638. Günstig im Verhältnis zur gezeigten Tool-Kompetenz.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Research-, Retrieval- und Assistenzpipelines, in denen Tool-Wahl und Fehlertransparenz wichtiger sind als hochpräzise Endverdichtung. Nicht die erste Wahl für Compliance-nahe, regulatorische oder direkt entscheidende Outputs ohne zweite Prüfschicht. Deployen, wenn ein struktureller Guardrail die Zusammenfassung kontrolliert, Quellen sichtbar hält und kritische Aussagen gegen die Tool-Ausgabe zurückprüft.