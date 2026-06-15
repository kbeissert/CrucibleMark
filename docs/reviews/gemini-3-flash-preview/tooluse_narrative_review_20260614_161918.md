**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:19:18


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination erkannt wurde, die Synthesetreue aber für tool-zentrierte Produktionspipelines nur mittel belastbar bleibt.

**Tool-Execution-Profil**

Gemini 3 Flash Preview verhält sich auf MCP-Ebene brauchbar. Der Tool-Call war valide, ein Retry war nicht nötig, und der P1-Wert zeigt ein insgesamt stabiles Ausführungsprofil. Das ist die zentrale Eintrittskarte für produktiven Tool-Einsatz.

Bei der Werkzeugwahl zeigt das Modell echte, aber begrenzte Adaptivität. Im Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis search statt fetch gewählt wird, erreicht es P1 80. Das spricht dafür, dass es den Informationsbedarf meist richtig erkennt, aber nicht deterministisch. Im Test URL Construction & Fetch, der die Herleitung einer Ziel-URL aus Vorwissen und den anschließenden Fetch misst, liegt es ebenfalls bei P1 80. Es folgt also nicht nur einem starren Suchmuster, sondern kann auch direkte Fetch-Pfade bilden. Für dynamische Pipelines ist das ausreichend. Für streng regelbasierte Orchestrierung mit hoher Fehlertoleranzreserve bleibt es jedoch unter dem Niveau, bei dem man Tool-Entscheidungen ungeprüft laufen lassen sollte.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. P2 56.67 ist der schwächste Teil des Profils. Besonders sichtbar wird das in Web Search & Tool Selection und Multilingual Search & Synthesis, wo die Ausführung gelingt, die Verdichtung aber zu grob bleibt. Das Modell holt Informationen also oft korrekt ein, transformiert sie aber nicht konsistent in belastbare, knappe Arbeitsantworten für nachgelagerte Systeme oder Entscheider.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil deutlich besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, blieb das Modell im verifizierten Inhaltsraum. Content-Verification-State A und keine erkannte Halluzination sind für Compliance-nahe Tool-Pipelines ein klares Vertrauenssignal.

**Fehlerresilienz**

Beim 404-Test, der transparentes Scheitern gegen erfundenen Seiteninhalt abgrenzt, reagiert das Modell akzeptabel. Es halluziniert trotz Fehler keinen Ersatzinhalt. P2 60 zeigt keine besonders gute Fehlereinordnung, aber die entscheidende Sicherheitsbedingung ist erfüllt: Es erfindet bei Tool-Ausfall keine Fakten. Für Produktion ist das tragbar.

**Betriebsprofil**

Call 1 1.61s. MCP-Latenz 1.25s. Call 2 6.95s. Total 58.85s.  
Kosten pro Run: $0.007878.  
Direktes Urteil: bei Einzelaufrufen schnell, im Gesamtrun lang; sehr günstig im Verhältnis zur gebotenen Tool-Kompetenz.

**Fazit & Empfehlung**

Geeignet für allgemeine MCP-Pipelines mit Web-Recherche, Fetch und kontrollierter Fehlerbehandlung, vor allem wenn Kosten niedrig bleiben sollen und eine nachgelagerte Validierung der Antwortverdichtung existiert. Nicht die richtige Wahl für Pipelines, in denen die Modellantwort selbst bereits das Endprodukt ist, etwa Compliance-Summaries, mehrsprachige Entscheidungsbriefings oder präzise Executive-Synthesen. Dort ist nicht die Tool-Nutzung das Risiko, sondern die zu schwache Verdichtung der Tool-Ergebnisse.