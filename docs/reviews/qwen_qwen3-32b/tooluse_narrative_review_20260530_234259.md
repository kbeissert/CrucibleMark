**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:59


Bedingt deploy, weil Qwen 3 32B valide Tool-Calls erzeugt und im MCP-Ablauf stabil wirkt, aber mit erkannter Halluzination bei nur moderater Gesamtleistung das Vertrauen in faktische Tool-Pipelines nicht durchgehend trägt.

**Tool-Execution-Profil**

Auf der Ausführungsseite ist das Modell brauchbar. P1 mit 86.67 zeigt, dass es Tools grundsätzlich korrekt ansteuert. Wichtig ist der Unterschied zwischen Werkzeugwahl und nachgelagerter Präzision: Beim Test Web Search & Tool Selection, der ohne Hinweis die Wahl zwischen Suche und Fetch verlangt, erkennt es den richtigen Pfad sehr sicher und erreicht P1 100. Das spricht gegen bloßes Schema-Folgen und für echte Tool-Selection-Kompetenz. Beim Test URL Construction & Fetch, der die Ziel-URL aus Vorwissen ableiten und dann korrekt abrufen lässt, fällt es auf P1 80 zurück. Es versteht also den Ablauf, ist aber bei deterministischen Vorstufen weniger exakt. Positiv: Die Tool-Calls waren valide, ein Retry war nicht nötig. Das ist kein Protokollproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 von 43.33 ist für produktive Nachverarbeitung zu niedrig. Besonders kritisch sind EU License Research mit P2 15 und Multilingual Search & Synthesis mit P2 15. Das Modell holt Informationen oft noch an die Oberfläche, verdichtet sie aber nicht verlässlich in belastbare Aussagen für nachgelagerte Systeme.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Ein Modell, das erfundene oder aus dem Training rekonstruierte Fakten als Tool-Resultat ausgibt, unterläuft die Kontrollfunktion der gesamten Tool-Infrastruktur.

**Fehlerresilienz**

Hier liegt der produktionskritische Befund. Im Test Tool Failure Handling (404), der transparenten Umgang mit fehlgeschlagenem Abruf prüft, halluziniert das Modell trotz 404 weiter und erreicht nur P2 35. Ein akzeptables Produktionsverhalten wäre klares Stoppen, Fehlermeldung und gegebenenfalls Nachfrage. Erfundenen Seiteninhalt nach Tool-Fehlern darf man in keiner verlässlichen Pipeline tolerieren.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Deployments operativ attraktiv. Leistung bleibt aber 5.32 Punkte unter dem Fleet-Ø von 66.76. Kosten pro Run von 0.002685 sind günstig. Die Laufzeit von 31.49s gesamt ist für die erreichte Qualität eher lang.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische MCP-Pipelines, in denen Tool-Aufrufe korrekt orchestriert werden müssen und ein zweiter Validierungsschritt die Ausgabe prüft. Nicht geeignet für Compliance, regulatorische Recherche, Incident-Workflows oder jede Pipeline, in der Tool-Ergebnisse als verifizierte Fakten weitergereicht werden. Wer Qwen 3 32B einsetzt, sollte es als Tool-Bediener mit strikter nachgelagerter Verifikation verwenden, nicht als vertrauenswürdige Syntheseinstanz.