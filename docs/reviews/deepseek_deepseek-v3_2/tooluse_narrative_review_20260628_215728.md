**Deployment-Urteil**

> **Erstellt am:** 28.06.2026, 21:57:28


Bedingt deploy, weil die Tool-Ausführung insgesamt tragfähig ist, aber die Synthesetreue mit Halluzinationssignal und ungültigem Tool-Call nicht ausreicht, um das Modell unbeaufsichtigt in kritische MCP-Pipelines zu setzen.

**Tool-Execution-Profil**

DeepSeek V3.2 zeigt echte Werkzeugintelligenz, nicht nur starres Call-Muster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, wählt es das richtige Werkzeug sicher. Das spricht für brauchbare Planungsfähigkeit in dynamischen Pipelines. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus eigenem Wissen misst, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Produktionspfade. Der P1-Wert von 83.33 ist daher belastbar, aber nicht sauber genug, um auf harte Protokolltreue zu schließen. Kritisch ist, dass mindestens ein Tool-Call formal nicht valide war. Das ist kein reines Qualitätsdetail, sondern ein Integrationsrisiko für MCP-Orchestrierung, weil ein einziger fehlerhafter Call ganze Ketten stoppt. Positiv ist, dass kein Retry nötig war. Das wirkt eher wie punktuelle Protokollungenauigkeit als wie grundlegendes Verständnisproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung von 52.50 zeigt ein klares Muster: starke Extraktion bei HTTP Fetch & Extract, aber schwache Verdichtung sobald mehrere Quellen, Sprachwechsel oder unklare Fehlersituationen zusammenkommen. Besonders der Test Multilingual Search & Synthesis, der grenzüberschreitende Recherche und deutsche Zusammenfassung misst, ist mit P2=15 für produktive Wissenspipelines klar zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, bleibt das Modell grundsätzlich im Tool-Pfad und halluziniert nicht. Das ist der wichtigste positive Vertrauensbefund. Gleichzeitig bleibt das globale Halluzinationssignal ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als abgerufene Inhalte ausgibt, verliert die Infrastruktur ihren Nachweischarakter.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit gescheiterten Tool-Aufrufen misst, erfindet DeepSeek V3.2 keinen Seiteninhalt. Das ist die Mindestanforderung für Produktion und wurde erfüllt. Die P2=40 zeigt aber, dass die Fehlerkommunikation nicht präzise genug ist. Für Nutzer bedeutet das: eher vage oder unvollständige Fehlereinordnung statt klarer operativer Diagnose.

**Betriebsprofil**

Total 89.72s. Call 1 2.80s, MCP-Latenz 0.88s, Call 2 11.27s. Für die gezeigte Leistung langsam. Kosten/Run lokal, damit finanziell attraktiv, aber die Laufzeit ist für interaktive oder hochvolumige Pipelines schwer zu rechtfertigen.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Abrufpipelines mit Human-in-the-Loop, vor allem wenn Tool-Wahl wichtiger ist als saubere Endverdichtung. Nicht geeignet für Compliance, regulatorische Dokumentation, kundensichtbare Antwortketten oder autonome Agentenpfade, in denen jede Synthese als belastbarer Tool-Nachweis gelten muss. Wenn Sie es einsetzen, dann hinter strikter Tool-Call-Validierung, Response-Schema-Prüfung und einem zweiten Verifikationsschritt für die finale Zusammenfassung.