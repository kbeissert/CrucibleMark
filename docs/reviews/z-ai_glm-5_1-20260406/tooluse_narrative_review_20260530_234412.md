**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:44:12


Bedingt deploybar, weil GLM 5.1 valide Tool-Calls liefert und in der Ausführung stark ist, aber die Synthesetreue mit erkannten Halluzinationen nicht verlässlich genug für hochkritische Tool-Pipelines bleibt.

**Tool-Execution-Profil**

Die operative Tool-Nutzung ist klar die Stärke dieses Modells. Mit P1 90 produziert GLM 5.1 valide MCP-konforme Aufrufe, ohne dass ein Retry nötig war. Das spricht gegen ein Protokoll- oder Formatproblem und für belastbare Basiskompetenz im Tooling.

Bei der Werkzeugwahl zeigt es echte Differenzierung statt bloßem Musterfolgen. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es P1 100. Es erkennt also, wann erst eine Websuche nötig ist. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann per Fetch abrufen lässt, fällt es auf P1 80. Das ist brauchbar, aber nicht präzise genug für deterministische Abläufe, die auf korrekte URL-Bildung ohne Korrekturschritt angewiesen sind.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 59.17 ist für ein Frontier-Generalist-Modell zu schwach. Die Einzelergebnisse zeigen das Muster deutlich: HTTP Fetch & Extract und Tool Failure Handling (404), beide mit klaren Quelltextsignalen, gelingen ordentlich. Sobald Auswahl, Verdichtung und Priorisierung mehr Deutung verlangen, fällt die Qualität ab, etwa bei EU License Research mit P2 40 und Web Search & Tool Selection mit P2 35.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Webquellen statt aus dem Trainingswissen beantwortet werden, bleibt der Befund gemischt. Halluzination wurde dort nicht erkannt und der Verifikationsstatus ist A, was positiv ist. Gleichzeitig ist global Halluzination erkannt: true. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Wenn ein Modell erfundene Fakten als aus Tools stammend ausgibt, verliert die gesamte Pipeline ihren Vertrauensanker.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Fehlermanagement statt erfundenem Ersatzinhalt misst, kommuniziert GLM 5.1 den Fehlschlag sauber. P2 80 und keine Halluzination trotz 404 zeigen, dass es bei Tool-Ausfällen nicht reflexhaft Seiteninhalt erfindet. Das ist eine zentrale Mindestanforderung für robuste Agentenpfade.

**Betriebsprofil**

Call 1: 9.61s. Call 2: 41.74s. MCP-Latenz: 0.77s. Total: 312.72s.  
Direkte Aussage: langsam im End-to-End-Lauf.  
Kosten pro Run: 0.014060.  
Direkte Aussage: günstig bis moderat bepreist, gemessen an der nur guten Gesamtleistung.

**Fazit & Empfehlung**

Geeignet für recherchierende Pipelines mit menschlichem Review, für Tool-gestützte Assistenten mit Fehlertoleranz und für Workflows, in denen korrekte Tool-Ausführung wichtiger ist als präzise Verdichtung. Nicht geeignet für Compliance-, Policy-, Vertrags- oder andere High-Trust-Pipelines, in denen jede Synthese streng an Tool-Belege gebunden bleiben muss. Wenn Sie GLM 5.1 einsetzen, dann hinter einer Verifikationsschicht, die Aussagen gegen Tool-Outputs zurückprüft.