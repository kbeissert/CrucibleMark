**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:06:38


Bedingt deploy: gemma3:12b ist für MCP-gestützte Tool-Pipelines grundsätzlich brauchbar, weil es valide Tool-Calls ohne Retry produziert und keine Halluzination erkannt wurde, aber die Synthesequalität mit P2 60 das Vertrauen in nachgelagerte Entscheidungen begrenzt.

**Tool-Execution-Profil**

Beim eigentlichen Tool-Einsatz liefert das Modell ein solides Produktionssignal. Der Tool-Call war valide, MCP-protokollkonform und ohne erneuten Anlauf ausführbar. Das spricht für stabile Formatdisziplin, was in verketteten Tool-Pipelines wichtiger ist als sprachlicher Stil. Der P1-Wert von 90 stützt dieses Bild: Das Modell kann Werkzeuge nicht nur ansprechen, sondern offenbar in einer Form, die operativ verwertbar bleibt.

Die Grenze der Bewertung liegt in den fehlenden Detaildaten. Für den Test zur Werkzeugwahl zwischen Websuche und direktem Fetch liegen keine Ergebnisse vor. Ebenso fehlen Daten zum URL-Construction-Test, der prüft, ob das Modell Ziel-URLs präzise aus eigenem Wissen ableitet. Deshalb lässt sich nicht belastbar sagen, ob gemma3:12b intelligent zwischen Werkzeugen unterscheidet oder vor allem einem stabilen Aufrufmuster folgt. Für produktive Orchestrierung ist das ein offener Punkt.

**Synthesetreue**

Wie gut verdichtet es? Nur eingeschränkt belastbar. Der P2-Wert von 60 zeigt, dass gemma3:12b Tool-Ergebnisse zwar verwerten kann, aber bei Verdichtung, Priorisierung und präziser Rückführung in die Antwort nicht durchgängig scharf arbeitet. Für einfache Extraktion und knappe Zusammenfassungen ist das ausreichend. Für Compliance, Policy-Auslegung oder mehrstufige Entscheidungslogik ist es zu weich.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Positiv, soweit messbar: Es wurde keine Halluzination erkannt. Das ist das zentrale Vertrauenssignal für produktive Tool-Nutzung. Für den Honeypot EU License Research, der genau dieses Verhalten unter aktueller Webabhängigkeit prüft, liegen allerdings keine Einzeldaten vor. Das Gesamturteil ist daher vorsichtig positiv, nicht abschließend abgesichert.

**Fehlerresilienz**

Für den 404-Test, der transparentes Verhalten bei fehlgeschlagenem Fetch prüft, liegen keine Daten vor. Deshalb gibt es keinen Nachweis, wie das Modell unter Tool-Fehlern reagiert. In Produktion ist das relevant: Ein sauberes Abbrechen mit klarer Fehlermeldung ist akzeptabel. Erfundener Ersatzinhalt wäre ein sofortiger Ausschlussgrund. Diese Flanke bleibt offen und sollte vor Rollout gezielt nachgetestet werden.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Die Gesamtleistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.84 und bleibt damit klar fleet-kompetitiv. Für lokale Infrastruktur ist das ein gutes Verhältnis aus Kontrolle und Nutzwert.

**Fazit & Empfehlung**

Geeignet für lokale Recherche-, Extraktions- und Assistenzpipelines, in denen ein valider Tool-Aufruf wichtiger ist als hochwertige Ergebnisverdichtung. Auch für interne MCP-Workflows mit menschlicher Sichtkontrolle ist das Modell plausibel einsetzbar. Nicht die erste Wahl für autonome Pipelines, in denen Tool-Ausgaben präzise priorisiert, fehlerrobust verarbeitet und ohne Rückfrage in belastbare Entscheidungen übersetzt werden müssen. Vor produktivem Einsatz sollten Werkzeugwahl und Fehlerverhalten separat verifiziert werden.