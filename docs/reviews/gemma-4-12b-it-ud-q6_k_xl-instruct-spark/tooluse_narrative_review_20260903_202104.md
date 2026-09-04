**Deployment-Urteil**

> **Erstellt am:** 03.09.2026, 20:21:04


Bedingt deployen, weil die Tool-Nutzung meist zweckrichtig und halluzinationsfrei ist, aber die Tool-Calls nicht durchgängig valide sind und die Verdichtung der Ergebnisse für belastbare Produktionsausgaben zu flach bleibt.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber. Das spricht für agentische Grundkompetenz in MCP-gestützten Flows. Auch EU License Research und Multilingual Search & Synthesis laufen auf dieser Ebene stark.

Schwächer ist die Ausführung im Detail. Beim URL-Construction-Test, der die korrekte Ziel-URL aus internem Wissen ableiten und dann fetch ausführen lässt, reicht es nur zu brauchbarer Präzision. Das ist für interaktive Assistenten tolerierbar, für deterministische Pipelines aber ein Risiko, weil schon kleine URL-Fehler nachgelagerte Schritte kippen können. Der Befund „Tool-Call valide: False“ ist deshalb zentral: Das Modell versteht meist, welches Werkzeug gebraucht wird, produziert aber nicht konsistent protokollsaubere oder vollständig belastbare Aufrufe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ausreichend. Die P2-Leistung ist über alle Aufgaben konstant bei 60 und zeigt ein Muster: Das Modell fasst Ergebnisse knapp und meist korrekt zusammen, extrahiert aber nicht zuverlässig die volle operative Substanz aus den Tool-Outputs. Für Recherche-Assistenz genügt das. Für Compliance, Vertragsprüfung oder präzise Faktenketten ist es zu dünn.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt es im sicheren Bereich. Es halluziniert nicht und ersetzt fehlende Evidenz nicht durch Trainingswissen. Das ist ein gutes Vertrauenssignal für produktive Tool-Pipelines.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der einen fehlschlagenden Tool-Call provoziert, erfindet das Modell keinen Seiteninhalt. Es bleibt transparent über den Fehlerzustand. Diese Eigenschaft ist wichtiger als Eleganz in der Formulierung, weil sie verhindert, dass defekte Infrastruktur stillschweigend in falsche Fachantworten umschlägt.

**Betriebsprofil**

Total 157.24s pro Run. Call 1: 3.76s. MCP-Latenz: 1.05s. Call 2: 21.40s. Lokal betrieben, daher direkte Run-Kosten praktisch niedrig. Für die gezeigte Leistung ist das Gesamtprofil eher langsam.

**Fazit & Empfehlung**

Geeignet für lokale Recherche-, Discovery- und Vorverarbeitungs-Pipelines, in denen Tool-Auswahl wichtiger ist als perfekte Endverdichtung und ein nachgelagerter Validator die Tool-Calls absichert. Nicht die erste Wahl für strikt deterministische MCP-Orchestrierung, Compliance-Ausgaben ohne menschliche Kontrolle oder Pipelines, in denen URL- und Fetch-Präzision direkt geschäftskritisch ist. Als lokales Modell für souveräne Tool-Assistenz ist es brauchbar. Als autonomer Endpunkt für belastbare Tool-Resultate noch nicht robust genug.