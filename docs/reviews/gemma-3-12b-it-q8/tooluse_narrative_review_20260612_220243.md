**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:02:43


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, die Synthesequalität aber zu oft unter Produktionsniveau bleibt und bereits eine Halluzination im Lauf erkannt wurde. Der kombinierte Eindruck ist damit für Tool-Pipelines brauchbar, aber nicht vertrauensstark genug für unbeaufsichtigte Endausgaben.

**Tool-Execution-Profil**

Gemma 3 12B IT arbeitet auf MCP-Ebene sauber. Die Tool-Calls waren valide, ein Retry war nicht nötig, und die P1-Leistung zeigt klar, dass das Modell Werkzeuge nicht nur formal aufrufen kann, sondern meist auch das richtige auswählt. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und Direktabruf unterscheidet, erkennt es den Bedarf für web_search zuverlässig. Das spricht gegen ein starres Fetch-First-Muster und für echte Werkzeugwahl.

Schwächer ist es beim URL-Construction-Test, der korrekte Zieladressen aus Vorwissen ableiten muss. Dort reicht es nur zu brauchbarer, nicht deterministischer Präzision. Für feste Domains und bekannte Routen ist das akzeptabel. Für fragile Pipelines mit exakter URL-Ableitung bleibt es ein Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Werte zeigen ein klares Muster: Das Modell beschafft Informationen besser, als es sie verdichtet. Besonders im Test HTTP Fetch & Extract, der präzise Fakten wie Jahreszahlen oder Eigennamen aus echtem Seiteninhalt verlangt, fällt die Verdichtungsqualität deutlich ab. Auch bei EU License Research und URL Construction & Fetch bleibt die Zusammenführung der Ergebnisse zu grob. Für produktive Pipelines heißt das: gute Retrieval-Schicht, schwächere letzte Meile.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt gegen aktuelle Web-Quellen prüft, bleibt es im Ergebnisraum und halluziniert nicht. Das ist ein wichtiges Vertrauenssignal. Gleichzeitig ist der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis darstellt, beschädigt es das Vertrauen in die gesamte Tool-Infrastruktur. Dieses Modell ist daher nicht für High-Trust-Ausgaben ohne nachgelagerte Validierung geeignet.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Abruf prüft, reagiert Gemma 3 12B IT akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehlschlag statt Ersatzwissen auszugeben. Das ist produktionsreif. Die Qualität der Fehlermeldung ist nicht stark, aber die Sicherheitslinie stimmt.

**Souveränitätsprofil**

Lokal betreibbar und praktisch nutzbar. Mit einem Sovereignty Gap von -1.37 Punkten unter dem Fleet-Ø von 67.62 bleibt es nahezu fleet-kompetitiv, ohne externen Datentransfer und ohne Cloud-Abhängigkeit.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines, in denen Tool-Aufrufe, Rechercheanstoß und robuste Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Gut passend für Assistenzsysteme mit Human-in-the-Loop, Vorrecherche, mehrsprachige Suchpfade und kontrollierte Orchestrierung. Nicht passend für Compliance-Ausgaben, präzise Extraktionspipelines oder autonome Agenten, die Tool-Ergebnisse ohne zweite Prüfschicht direkt an Nutzer oder nachgelagerte Systeme ausspielen.