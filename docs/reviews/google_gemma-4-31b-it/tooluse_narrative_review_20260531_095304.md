**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:53:04


Bedingt deploy, weil Gemma 4 31B valide Tool-Calls produziert und nicht halluziniert, aber die Synthesequalität mit Combined 74.17 nur dann tragfähig ist, wenn nachgelagerte Validierung oder enge Ausgabeformate vorhanden sind.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsebene klar produktionsnah. P1 von 90 zeigt, dass es MCP-konform arbeitet, gültige Aufrufe erzeugt und kein Retry brauchte. Besonders stark ist der Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis statt fetch ein Such-Tool nötig ist: hier erkennt das Modell den Werkzeugbedarf sicher. Das spricht gegen starres Musterfolgen und für echte Werkzeugwahl.

Weniger sauber ist der Test URL Construction & Fetch, der prüft, ob das Modell die Ziel-URL aus eigenem Wissen präzise ableitet und dann korrekt abruft. Mit P1 80 gelingt der Ablauf brauchbar, aber nicht deterministisch genug für Pipelines, die aus freier URL-Konstruktion harte Verlässlichkeit erwarten. Das Muster ist damit klar: gute Tool-Intelligenz bei der Auswahl, etwas geringere Präzision bei der eigenständigen Vorstrukturierung des Inputs.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 von 60 ist der eigentliche Warnhinweis dieses Laufs. Solide Ergebnisse bei HTTP Fetch & Extract sowie Tool Failure Handling (404) zeigen, dass es extrahierte Fakten oft sauber zusammenziehen kann. Kritisch sind aber EU License Research mit P2 40 und Multilingual Search & Synthesis mit P2 20. Das Modell nutzt Tools, verliert aber bei verdichteter, mehrsprachiger oder compliance-naher Ausgabe an Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt das Vertrauenssignal intakt. Der Test prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden. Trotz schwacher Verdichtung wurde keine Halluzination erkannt, Content-Verification-State A. Das ist wichtig: Das Modell erfindet hier keine Quelle, sondern arbeitet auf echter Tool-Basis.

**Fehlerresilienz**

Im 404-Test reagiert Gemma 4 31B produktionstauglich. Der Test misst, ob ein fehlgeschlagener Tool-Call transparent benannt oder durch erfundenen Seiteninhalt ersetzt wird. Mit P2 80 und ohne Halluzination trotz 404 kommuniziert das Modell den Fehler akzeptabel und wahrt die Grenze zwischen fehlender Evidenz und vorhandenem Inhalt. Das ist für produktive Tool-Pipelines ein Muss und hier erfüllt.

**Souveränitätsprofil**

Lokal betreibbar und fleet-nah kompetent. Der Sovereignty Gap liegt bei -2.89 Punkten unter dem Fleet-Ø von 65.84. Für eine local_sovereign-Gruppe ist das ein belastbares Ergebnis.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Such-, Fetch- und Fehlerbehandlungslogik, wenn die Ausgabe knapp strukturiert ist und kritische Synthese noch geprüft wird. Besonders passend für souveräne Retrieval-Workflows, interne Recherche und Tool-orientierte Assistenz. Nicht die erste Wahl für Compliance-Summaries, mehrsprachige Verdichtung oder frei formulierte Abschlussantworten, bei denen die Qualität der Zusammenfassung selbst das Produkt ist.