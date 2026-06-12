**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:36:40


Bedingt deploy, weil Mistral 3 Large Tools zuverlässig ansteuert und valide MCP-Calls erzeugt, aber die Synthesequalität mit Combined 59.71 und erkanntem Halluzinationsbefund nicht stabil genug für unbeaufsichtigte Entscheidungs-Pipelines ist.

**Tool-Execution-Profil**

Das operative Bild ist stark. P1 liegt bei 90.00, der Tool-Call war valide und ein Retry war nicht nötig. Das spricht für saubere Protokolltreue im MCP-Kontext. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Fetch prüft, erkennt das Modell den richtigen Werkzeugtyp sicher. Das ist ein Signal für echte Werkzeugwahl statt starrem Schema. Beim URL-Construction-Test, der die Ableitung einer korrekten Ziel-URL aus eigenem Wissen misst, fällt es auf P1 80 zurück. Es kann also aus der richtigen Tool-Kategorie nicht immer eine deterministisch korrekte Zieladresse formen. Für dynamische Retrieval-Pipelines ist das akzeptabel. Für fest verdrahtete Compliance- oder Dokumentenpfade bleibt es ein Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 liegt nur bei 30.00. Über mehrere Assets hinweg sieht man das gleiche Muster: Die Beschaffung klappt, aber die Verdichtung verliert Präzision, lässt wichtige Details aus oder formuliert Ergebnisse nicht eng genug am Quellmaterial. Besonders kritisch sind EU License Research mit P2 20, URL Construction & Fetch mit P2 15 und Multilingual Search & Synthesis mit P2 15. Das Modell holt Material, aber es transformiert es nicht verlässlich in belastbare Endantworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt bei aktuellen Lizenzrestriktionen prüft, blieb es formal im Tool-Pfad. Halluzination wurde dort nicht erkannt, Content-Verification-State A. Das Vertrauenssignal ist also besser als die reine P2-Zahl vermuten lässt. Gleichzeitig gilt der globale Halluzinationsbefund als Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnis ausgeben kann, verliert die Infrastruktur ihre Prüfbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei Tool-Fehlern misst, reagiert Mistral 3 Large akzeptabel. P2 60 ist nicht stark, aber es halluziniert keinen Seiteninhalt trotz Fehler. Für Produktion zählt genau das. Ein gescheiterter Call wird eher als Fehler behandelt als mit erfundenem Ersatz kaschiert.

**Betriebsprofil**

Call 1: 21.01s. Call 2: 8.92s. MCP-Latenz: 0.95s. Total: 185.30s.  
Kosten pro Run: 0.007693.  
Direkte Einordnung: langsam im Gesamtdurchlauf, günstig pro Run, Leistungsbild eher durch Zuverlässigkeitsgrenzen als durch Kosten limitiert.

**Fazit & Empfehlung**

Geeignet für recherchierende Tool-Pipelines mit menschlicher Abnahme, etwa Discovery, Vorrecherche, Quellensammlung und mehrsprachige Kandidatensuche. Nicht geeignet für autonome Pipelines, die aus Tool-Ergebnissen direkt belastbare Endaussagen, Compliance-Bewertungen oder präzise Extrakte erzeugen müssen. Wenn Sie es einsetzen, dann als Beschaffer vor einem strengeren Verifier oder einem zweiten Synthese-Schritt.