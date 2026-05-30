**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:58


Bedingt deploybar, aber nicht als autonomes Tool-Modell: Der Combined-Score von 33.42 ist schwach, der Tool-Call war nicht valide und ein Retry war nötig, auch wenn keine Halluzination erkannt wurde.

**Tool-Execution-Profil**

Llama 4 Scout 17B zeigt in der Tool-Ausführung kein belastbares Orchestrierungsprofil. Die P1-Werte liegen durchgängig bei 35, sowohl beim Test zur Werkzeugwahl ohne expliziten Hinweis, ob web_search statt fetch nötig ist, als auch beim Test zur URL-Konstruktion mit anschließendem Fetch. Das spricht nicht für adaptive Werkzeugintelligenz, sondern eher für ein starres oder unsauber ausgeführtes Tool-Schema. Es erkennt also nicht überzeugend, wann Suche nötig ist und wann ein direkter Abruf reicht.

Der kritische Punkt ist nicht die Antwortqualität, sondern die Protokolltreue: Der Tool-Call war ungültig und musste wiederholt werden. Das wirkt eher wie ein Format- oder MCP-Compliance-Problem als wie reines Aufgabenmissverständnis. Für produktive Pipelines ist das relevant, weil solche Modelle Orchestratoren, Validatoren oder Retrieschichten brauchen, bevor sie stabil in einen Tool-Stack passen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? In fünf von sechs Assets liefert das Modell mit P2=40 eine brauchbare, knappe Verdichtung von Tool-Inhalten. Das reicht für einfache Extraktion, Zusammenfassung und sprachübergreifende Verdichtung, aber nicht für präzise Analysten- oder Compliance-Ausgaben. Der Ausreißer ist gravierend: Bei EU License Research, dem Honeypot-Test für aktuelle Lizenzrestriktionen aus Web-Quellen, fällt P2 auf 0.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gemischt. Formal wurde keine Halluzination erkannt, aber der Honeypot mit Content-Verification-State B2 zeigt, dass das Modell die aktuelle Quellenbindung nicht verlässlich hält. Für jede Pipeline, in der Aktualität oder Rechtslage an Web-Belege gekoppelt sein muss, ist das ein Vertrauensbruch auf Prozessniveau, auch ohne explizite Halluzination.

**Fehlerresilienz**

Beim 404-Test, der prüft, ob ein fehlgeschlagener Tool-Call transparent behandelt wird statt Seiteninhalt zu erfinden, reagiert das Modell akzeptabel. P2=40 und keine Halluzination trotz Fehler bedeuten: Es kommuniziert Scheitern sichtbar, statt Ersatzinhalt zu konstruieren. Das ist produktionsfähig und klar besser als Modelle, die aus einem Fetch-Fehler noch Fakten ableiten.

**Souveränitätsprofil**

Lokal betreibbar und kostengünstig, aber nicht fleet-kompetitiv genug für anspruchsvolle Tool-Pipelines. Sovereignty Gap: -5.32 Punkte unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet ist das Modell für lokal souveräne, kostenempfindliche Pipelines mit enger Aufsicht: einfache Fetch-Zusammenfassungen, transparente Fehlerweitergabe, vorbereitete Tool-Schritte. Nicht geeignet ist es als eigenständiger Agent für MCP-gestützte Recherche, Compliance, dynamische Tool-Wahl oder jede Pipeline, in der Tool-Calls ohne Retry strikt valide sein müssen. Wenn Sie es einsetzen, dann hinter einem strengen Call-Validator und mit externer Kontrolle der Quellenbindung.