**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:04:22


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die erkannte Halluzination im Honeypot das Vertrauen in toolgestützte Faktenausgabe für produktive Entscheidungen bricht.

**Tool-Execution-Profil**

Gemini 3.1 Flash Lite Preview arbeitet auf Tool-Ebene zuverlässig. P1 liegt mit 90 hoch, die Tool-Calls waren valide und es brauchte keinen Retry. Das ist für MCP-Pipelines der erste wichtige Befund: Das Modell versteht das Protokoll und erzeugt keine operative Reibung.

Bei der Werkzeugwahl zeigt es mehr als bloßes Schema-Folgen. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählt es das passende Tool sicher. Das spricht für brauchbare Orchestrierungsintelligenz in dynamischen Flows. Beim URL-Construction-Test, der prüft ob es die Ziel-URL aus Vorwissen ableiten und dann korrekt abrufen kann, bleibt es brauchbar, aber nicht deterministisch genug. Es kann also Tools richtig auswählen, ist aber schwächer, wenn präzise Zieladressen aus implizitem Wissen konstruiert werden müssen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 mit 59.17 zeigt, dass das Modell gefetchte oder gesuchte Inhalte oft nur mittelpräzise zusammenführt. Das passt zum Asset-Bild: solide bei HTTP Fetch & Extract und Multilingual Search & Synthesis, aber schwach bei EU License Research. Für Extraktion und einfache Zusammenfassungen reicht das oft aus. Für belastbare Entscheidungsprosa reicht es nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen geholt werden, fiel das Modell mit P2=15 auf und halluzinierte. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene Inhalte als Ergebnis einer Tool-Recherche ausgibt, unterläuft es die Kontrollfunktion der gesamten Tool-Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Seiteninhalt prüft, halluzinierte es nicht und erreichte P2=80. Das ist produktionsreif. Ein fehlgeschlagener Aufruf wird also eher als Fehler behandelt als mit Scheininhalt kaschiert.

**Betriebsprofil**

0.57s erster Call, 1.38s zweiter Call, 0.84s MCP-Latenz, 16.77s gesamt. Günstig mit 0.004118 USD pro Run. Operativ attraktiv, qualitativ nur für einfache Automatisierung passend.

**Fazit & Empfehlung**

Geeignet für kostensensitive MCP-Pipelines mit klaren Tool-Grenzen: Routing, Suche, Fetch, Extraktion, Vorstrukturierung und mehrsprachige Erstverdichtung. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere High-Trust-Pipelines, in denen das Modell strikt an Tool-Belege gebunden bleiben muss. Wenn Sie es einsetzen, dann nur mit nachgelagerter Verifikation und ohne Freigabe für entscheidungstragende Endaussagen.