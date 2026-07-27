**Deployment-Urteil**

> **Erstellt am:** 19.07.2026, 23:28:00


Bedingt deploy, weil die Tool-Nutzung operativ oft funktioniert, aber ungültige Tool-Calls und eine schwache Synthesetreue das Vertrauen in produktive MCP-Pipelines begrenzen. Der Combined-Score von 62.58 bestätigt ein nutzbares, aber nicht robustes Produktionsprofil.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl-Kompetenz, nicht nur starres Fetch-Verhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es P1 100 und erkennt den richtigen Zugriffspfad zuverlässig. Beim Test URL Construction & Fetch, der die eigenständige Herleitung einer Ziel-URL und den anschließenden Abruf misst, ist es mit P1 80 noch brauchbar, aber nicht präzise genug für deterministische Abläufe.

Kritisch ist der Meta-Befund: Tool-Call valide = false. Das heißt, die Pipeline bekommt nicht durchgehend protokollsaubere Aufrufe, obwohl das Modell inhaltlich oft das richtige Werkzeug identifiziert. Für MCP-Umgebungen ist das ein Integrationsrisiko. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein reines Formatflattern und eher für punktuelle Ausführungs- oder Parametrisierungsfehler.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 45.83 ist der eigentliche Engpass dieses Modells. Es kann recherchieren und abrufen, verdichtet die Ergebnisse aber zu oft unpräzise oder lässt wichtige Details liegen. Besonders sichtbar wird das bei HTTP Fetch & Extract, wo der Abruf gelingt, die strukturierte Extraktion realer Fakten aber mit P2 15 klar zu schwach ausfällt. Auch Multilingual Search & Synthesis zeigt mit P2 40, dass Sprachgrenzen bei der Verdichtung Qualität kosten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Vertrauenssignal gemischt. Es halluziniert dort nicht offen, aber P2 20 zeigt, dass die Antwort kaum belastbar aus dem recherchierten Material verdichtet wurde. Da global eine Halluzination erkannt wurde, ist das als Sicherheitsrisiko zu werten. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgeben kann, verliert die gesamte Tool-Infrastruktur ihren Prüfpfad.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlgeschlagene Tool-Calls statt erfundenem Ersatzinhalt misst, verhält sich das Modell produktionsgerecht. P2 80 und keine Halluzination trotz Fehler sprechen für saubere Fehlerkommunikation. Das ist ein relevanter Pluspunkt für überwachte Agentenabläufe.

**Betriebsprofil**

Total 54.20s. MCP-Latenz 0.95s. Modellaufrufe 1.64s und 6.44s. Für die erreichte Qualität langsam. Kosten pro Run: local. Inferenzkosten niedrig, Zeitkosten hoch.

**Fazit & Empfehlung**

Geeignet ist das Modell für lokale, kostenkontrollierte Pipelines mit menschlicher Nachkontrolle, vor allem dort, wo Tool-Auswahl wichtiger ist als präzise Endverdichtung. Weniger geeignet ist es für Compliance-, Research- oder Extraktionsstrecken, in denen Tool-Ergebnisse exakt, prüfbar und protokollkonform in die Antwort überführt werden müssen. Für autonome MCP-Agenten ohne enges Guardrailing würde ich es nicht als Primärmodell einsetzen.