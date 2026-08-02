**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:21:53


Bedingt deploy, weil die Tool-Ausführung insgesamt brauchbar ist, aber die Synthesequalität mit Combined 62.33 und formal ungültigen Tool-Calls nicht robust genug für vertrauenskritische MCP-Pipelines wirkt.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl-Kompetenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, trifft es die Entscheidung sauber und erreicht P1 100. Auch beim URL-Construction-Test, der die Herleitung einer Ziel-URL aus eigenem Wissen und den anschließenden Fetch misst, arbeitet es mit P1 80 weitgehend korrekt. Das spricht für brauchbare Agentik in offenen Recherchepfaden.

Der Haken liegt in der Protokolltreue. Tool-Call valide ist false, obwohl kein Retry nötig war. Das wirkt nicht wie ein Verständnisproblem, sondern wie ein Stabilitätsproblem im Call-Format oder in der letzten Meile der MCP-Ausgabe. Für produktive Tool-Pipelines ist das relevant, weil ein inhaltlich richtiger Plan an einer formal falschen Übergabe scheitern kann. Positiv ist, dass HTTP Fetch & Extract mit Combined 70 solide ausfällt. Negativ ist der Einbruch bei EU License Research mit Combined 26, sobald aktuelle externe Quellen sauber eingebunden und verdichtet werden müssen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 49.17 ist der zentrale Warnwert dieses Profils. Das Modell findet Informationen häufiger, als es sie verlässlich in knappe, belastbare Antworten überführt. Besonders sichtbar wird das bei Multilingual Search & Synthesis: P1 100, aber P2 40. Die Recherche funktioniert, die Verdichtung auf Deutsch verliert Präzision und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen erzwingen soll, ist das Vertrauenssignal gemischt. Es halluziniert nicht offen, was wichtig ist. Aber P2 20 zeigt, dass es die abgerufenen Quellen nicht zuverlässig in belastbare Aussagen überführt. Für Compliance-nahe Pipelines ist das zu schwach.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call prüft, erfindet das Modell keinen Seiteninhalt. Das ist der produktionsrelevante Mindeststandard. P2 40 zeigt aber, dass die Fehlerkommunikation eher knapp oder unvollständig ist. Akzeptabel für Produktion mit Guardrails, nicht stark genug für unbeaufsichtigte Recovery-Pfade.

**Betriebsprofil**

Call 1: 16.47s. Call 2: 195.44s. MCP-Latenz: 0.84s. Total: 1276.51s.  
Lokal betreibbar, daher direkte Run-Kosten lokal. Für die gezeigte Leistung klar langsam.

**Fazit & Empfehlung**

Geeignet für interne Recherche- und Agent-Pipelines mit nachgelagerter Validierung, vor allem dort, wo Tool-Auswahl wichtiger ist als perfekte Ergebnisverdichtung. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere High-Trust-Workflows, in denen Tool-Antworten präzise zusammengefasst und formal sauber an die Infrastruktur übergeben werden müssen. Wenn Sie es einsetzen, dann mit strikter Schema-Validierung, Response-Checking und einem zweiten Prüfschritt für Synthese.