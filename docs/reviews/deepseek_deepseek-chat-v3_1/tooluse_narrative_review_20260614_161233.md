**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:12:33


Bedingt deploy, weil DeepSeek V3.1-671B valide Tool-Calls erzeugt und in der Ausführung stark ist, aber die Synthesequalität mit Halluzinationssignal für produktive Tool-Pipelines nicht durchgehend vertrauenswürdig ist.

**Tool-Execution-Profil**

Das Modell kann eine MCP-gestützte Tool-Infrastruktur grundsätzlich bedienen. Die Tool-Calls waren valide, ein Retry war nicht nötig. Das spricht für saubere Protokolltreue und stabile Ausführung. Besonders stark ist der Test Web Search & Tool Selection, der prüft, ob ohne Hinweis statt fetch eine Suche nötig ist. Hier zeigt das Modell klare Werkzeugwahl und nicht nur starres Folgen eines Schemas. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL aus Vorwissen prüft, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Das Muster ist damit klar: gute Tool-Intelligenz bei der Auswahl, etwas weniger Präzision bei selbst konstruierten Endpunkten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Der P2-Wert von 52.50 passt zum Asset-Bild: Tool Failure Handling (404), Web Search & Tool Selection und URL Construction & Fetch sind in der Verdichtung solide, aber EU License Research und Multilingual Search & Synthesis brechen deutlich ein. Das Modell findet also oft die richtigen Quellen, überführt sie aber nicht konsistent in eine präzise, knappe und belastbare Antwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen beantwortet werden, blieb es formal im Tool-Pfad. Halluzination wurde dort nicht erkannt. Trotzdem ist das globale Halluzinationssignal ein Sicherheitsrisiko: In einer Tool-Pipeline reicht schon einzelne erfundene Faktizität, um die Vertrauenskette zwischen Tool-Ausgabe und Modellantwort zu brechen.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, hat das Modell keinen Seiteninhalt erfunden und den Fehler sauber behandelt. Genau dieses Verhalten ist in produktiven Systemen entscheidend, weil es Fehler offenlegt statt sie mit plausibel klingendem Ersatztext zu verdecken.

**Betriebsprofil**

Call 1: 5.08s. Call 2: 10.65s. Total: 94.38s. Kosten pro Run: $0.001656. Günstig, aber für den erzielten Gesamtwert langsam.

**Fazit & Empfehlung**

Geeignet für kostenkritische Pipelines mit klaren Tool-Grenzen, guter Downstream-Validierung und geringer Toleranz für verdeckte Tool-Fehler. Auch brauchbar für Recherche-Orchestrierung, wenn ein nachgelagerter Verifier die Verdichtung prüft. Nicht geeignet für Compliance-, Policy- oder mehrsprachige Entscheidungs-Pipelines, in denen die Antwort selbst als belastbare Endrepräsentation dienen muss. Wer dem Modell Tools gibt, sollte die Ausführung nutzen, aber die Synthese nicht ungeprüft freigeben.