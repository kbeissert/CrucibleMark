**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:08:32


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination im Tool-Kontext erkannt wurde, die Verdichtung der Ergebnisse aber zu oft nur durchschnittlich bleibt.

**Tool-Execution-Profil**

Gemma 4 E4B ist im MCP-Rahmen klar verwendbar. Die Tool-Calls waren valide, ein Retry war nicht nötig, und der Tool-Execution-Wert zeigt, dass das Modell Infrastruktur sauber anspricht statt am Protokoll zu scheitern. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch verlangt, erkennt es korrekt, dass zuerst gesucht werden muss. Das spricht gegen bloßes Musterfolgen und für brauchbare Werkzeugwahl.

Weniger stark ist es beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und dann fetch ausführen lässt. Dort ist die Leistung noch brauchbar, aber nicht präzise genug für streng deterministische Pipelines. Das Muster ist damit klar: gute Entscheidung für den Werkzeugtyp, etwas weniger zuverlässig bei der exakten Ausformulierung des konkreten Targets.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mit Vorbehalt. Die P2-Qualität bleibt über die Aufgaben hinweg sichtbar hinter der Ausführung zurück. Gemma 4 E4B holt Informationen meist korrekt ein, formuliert die Zusammenführung aber oft zu knapp oder mit begrenzter Präzision. Für einfache Extraktion und kurze Statusantworten reicht das. Für Compliance-Zusammenfassungen, verdichtete Research-Memos oder mehrschrittige Entscheidungsbegründungen ist das zu wenig robust.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde keine Halluzination erkannt. Der niedrige Synthese-Wert dort ist deshalb eher ein Verdichtungsproblem als ein Vertrauensbruch. Für Produktionsbetrieb ist das ein wesentlicher Unterschied.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der den Umgang mit fehlschlagenden Tool-Calls misst, reagiert das Modell akzeptabel. Es erfindet trotz 404 keinen Seiteninhalt und bleibt damit innerhalb der tatsächlichen Systemlage. Die Fehlerkommunikation ist nicht besonders stark verdichtet, aber transparent genug für produktive Pipelines. Das ist die Mindestanforderung, und sie wird erfüllt.

**Souveränitätsprofil**

Lokal betreibbar: ja. Fleet-kompetitiv: knapp darunter. Das Modell liegt 1.37 Punkte unter dem Fleet-Ø von 67.84 und bietet damit eine brauchbare lokale Option ohne externen Datentransfer. Für souveräne Desktop-Deployments ist das ein solides Profil.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit klaren Tool-Grenzen, etwa Web-Recherche, einfache Fetch-Extraktion, multilingualen Basisabgleich und transparente Fehlerpfade. Nicht die richtige Wahl für Pipelines, in denen die eigentliche Wertschöpfung aus präziser Verdichtung, juristisch belastbarer Zusammenfassung oder URL-Genauigkeit unter wenig Führung entsteht. Wenn die Infrastruktur die Synthese nachgelagert absichert oder Outputs eng strukturiert, ist das Modell gut einsetzbar.