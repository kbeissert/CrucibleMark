**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:14


Bedingt deploy, weil Ministral 3B valide Tool-Calls produziert und im Execution-Pfad stark ist, aber mit erkannter Halluzination bei nur moderater Gesamtleistung kein vertrauenswürdiger Synthese-Endpunkt für kritische Pipelines ist.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsebene belastbar. P1 von 89.17 passt zu den Asset-Werten: Bei Web Search & Tool Selection, also der Frage ob ohne expliziten Hinweis Suche statt Direktabruf nötig ist, wählt es das richtige Werkzeug sicher. Das spricht gegen ein starres Fetch-Muster und für brauchbare Werkzeugwahl im laufenden Betrieb. Auch bei EU License Research und Multilingual Search & Synthesis löst es den Recherchepfad korrekt aus.

Schwächer ist die Präzision beim URL-Construction-Test, der die Ziel-URL aus Modellwissen ableiten und dann sauber abrufen lässt. P1 80 zeigt: brauchbar, aber nicht deterministisch genug für Pipelines, die exakte Endpunkte ohne Korrekturschleife erwarten. Da ein Retry erforderlich war, wirkt das eher wie ein Format- oder Ausführungsproblem im Tool-Loop als ein grundsätzliches Verständnisdefizit. Das Modell findet meist den richtigen Pfad, braucht aber gelegentlich Nachführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 40.00 ist der klare Engpass. Besonders auffällig sind EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis mit jeweils P2 15. Das Modell kann Informationen beschaffen, verliert aber bei der Verdichtung Präzision, Priorisierung und Quellentreue. Für produktive Antworten reicht die Retrieval-Leistung damit nicht aus.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der genau prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training kommen, wurde eine Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Fakten als Ergebnis eines Tool-Laufs ausgibt, untergräbt es das Vertrauen in die gesamte MCP-Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert Ministral 3B akzeptabel. Im 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt prüft, lag P2 bei 80 und es wurde kein Seiteninhalt erfunden. Das ist produktionsrelevant positiv: Das Modell kann Scheitern offen melden, statt still falsche Fakten zu erzeugen.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Im Ergebnis liegt es jedoch 5.32 Punkte unter dem Fleet-Ø von 66.76. Der Vorteil liegt klar in lokaler Verfügbarkeit, nicht in fleet-kompetitiver Endqualität.

**Fazit & Empfehlung**

Geeignet ist Ministral 3B als lokaler Tool-Dispatcher, Vorfilter oder Recherche-Orchestrator, wenn ein nachgelagerter Verifizierer die Endantwort kontrolliert. Nicht geeignet ist es als finales Antwortmodell in Compliance-, Policy-, Lizenz- oder anderen faktenkritischen Pipelines. Wer MCP-Tools zuverlässig ansteuern will, kann es einsetzen. Wer den daraus erzeugten Aussagen vertrauen muss, sollte ein strengeres Synthese- und Verifikationsmodell dahinter setzen.