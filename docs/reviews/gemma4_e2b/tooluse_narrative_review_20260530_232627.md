**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:27


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Synthese aber mit Combined 67.75 nur moderat bleibt und ein Halluzinationssignal im Gesamtlauf für produktive Tool-Pipelines ein Sicherheitsrisiko darstellt.

**Tool-Execution-Profil**

Gemma 4 2B arbeitet auf der MCP-Ebene sauber. Tool-Calls waren valide, ein Retry war nicht nötig. Das ist für lokale Edge-Setups ein starkes Signal. Vor allem erkennt das Modell beim Web-Search-and-Tool-Selection-Test, der die richtige Wahl zwischen Suche und direktem Fetch prüft, zuverlässig, wann erst gesucht werden muss. Das spricht gegen reines Schema-Folgen und für brauchbare Werkzeugwahl.

Schwächer ist die Präzision beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetch nutzt. P1 von 80 zeigt, dass es den Ablauf meist trifft, aber nicht deterministisch genug konstruiert. Für Pipelines mit offener Tool-Wahl ist das Modell damit brauchbar. Für Flows, in denen die URL exakt aus Modellwissen entstehen muss, bleibt ein Fehlerrand.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 45.83 ist der klare Engpass. Das Modell findet Informationen, verdichtet sie aber oft zu grob oder mit zu wenig Präzision. Das sieht man auch in EU License Research und Multilingual Search & Synthesis mit jeweils nur 40 Punkten sowie besonders deutlich in URL Construction & Fetch mit P2 von 15. Für produktive Systeme heißt das: Das Modell kann Daten beschaffen, aber die letzte Meile zur belastbaren, kompakten Antwort bleibt unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten gegen aktuelle Web-Quellen prüft, bleibt es im Ergebnisraum. Content-Verification-State A und keine Halluzination in diesem Test sind ein gutes Vertrauenssignal. Gleichzeitig gilt der globale Halluzinationsbefund als Sicherheitswarnung: Sobald ein Modell in einer Tool-Pipeline erfundene Inhalte als Tool-Ergebnis ausgeben kann, sinkt das Vertrauen in die gesamte Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Fehlverhalten statt erfundenem Seiteninhalt prüft, reagiert Gemma 4 2B akzeptabel. Es halluziniert trotz Fehler keinen Ersatzinhalt. P2 von 60 zeigt, dass die Fehlerkommunikation nicht immer ideal formuliert ist, aber sie bleibt operativ verwertbar. Für Produktion ist das deutlich wichtiger als stilistische Qualität.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Gleichzeitig liegt das Modell 5.32 Punkte unter dem Fleet-Ø von 66.76. Es ist also lokal praktikabel, aber nicht fleet-kompetitiv, wenn hohe Antworttreue in der Synthese gefordert ist.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen Tool-Aufrufe, Suche, einfache Extraktion und transparente Fehlerbehandlung wichtiger sind als präzise Endverdichtung. Geeignet als kostensensitiver Retrieval- und Tool-Worker mit nachgelagerter Validierung oder zweitem Modell für die finale Antwort. Nicht geeignet als alleinige Instanz für Compliance-nahe, entscheidungsrelevante oder stark verdichtete Ausgaben, bei denen jede Aussage direkt aus Tool-Ergebnissen sauber und vollständig abgeleitet sein muss.