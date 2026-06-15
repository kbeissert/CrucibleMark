**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:09:25


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Tool-Calls valide bleiben und der Gesamteindruck gut ausfällt, aber die Synthesequalität mit erkannten Halluzinationen nicht stabil genug für unbeaufsichtigte High-Trust-Pipelines ist.

**Tool-Execution-Profil**

Dieses Modell kann man einer MCP-Toolkette grundsätzlich anvertrauen. Es wählt Werkzeuge nicht nur schematisch, sondern zeigt echte Auswahlintelligenz: Beim Web-Search-&-Tool-Selection-Test erkennt es ohne expliziten Hinweis korrekt, dass erst Suche statt direktem Fetch nötig ist. Das spricht für agentisches Verhalten in offenen Retrieval-Flows. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen ableiten und dann per Fetch abrufen soll, arbeitet es brauchbar, aber nicht deterministisch genug für Pipelines mit harter URL-Präzision. Die P1-Werte zeigen damit ein klares Profil: hohe Protokolltreue, gute Werkzeugwahl, leichte Schwäche in der exakten Vorstufe zum Abruf. Positiv ist auch, dass kein Retry nötig war. Das ist ein Verständnissignal, kein bloßer Format-Treffer.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. Die Ausführung ist stark, aber die nachgelagerte Verdichtung bleibt der Engpass. Besonders beim HTTP-Fetch-&-Extract-Test, der strukturierte Fakten wie Jahreszahlen und Eigennamen aus realem Seiteninhalt ziehen soll, fällt die Präzision sichtbar ab. Auch beim Web-Search-&-Tool-Selection-Test war die Werkzeugwahl korrekt, die Synthese des gefundenen Materials aber schwach. Für produktive Tool-Pipelines heißt das: Das Modell findet oft den richtigen Pfad, formuliert das Ergebnis aber nicht konsistent präzise genug.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, bleibt es im Ergebnisraum der Tools. Das ist das wichtigste Vertrauenssignal hier. Gleichzeitig steht ein global erkannter Halluzinationsbefund im Lauf. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Wenn ein Modell erfundene Fakten als Tool-Resultat ausgibt, unterläuft es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell produktionsgerecht. Im 404-Test, der transparentes Verhalten bei fehlgeschlagenem Abruf prüft, kommuniziert es den Fehler, statt Seiteninhalt zu erfinden. Genau dieses Verhalten ist für produktive Agents akzeptabel. Der Befund ist klar positiv.

**Souveränitätsprofil**

Lokal betreibbar und praktisch einsetzbar. Mit einem Combined-Score von 70.88 liegt es 1.37 Punkte über dem Fleet-Ø von 67.84. Für eine lokale Q4-GGUF-Variante ist das ein starker Souveränitätswert, gerade weil die Tool-Ausführung nicht sichtbar unter der Quantisierung kollabiert.

**Fazit & Empfehlung**

Geeignet für lokale Coding- und Agent-Pipelines, in denen Tool-Navigation, Web-Recherche, Fehlertransparenz und MCP-Konformität wichtiger sind als perfekte Endverdichtung. Nicht geeignet für Compliance-, Policy- oder Executive-Summary-Strecken ohne nachgelagerte Validierung. Empfehlenswert als Worker-Modell mit Guardrails: Tool-first, Zitate oder Rohresultate sichtbar halten, finale Synthese entweder überprüfen oder an ein stärkeres Verdichtungsmodell übergeben.