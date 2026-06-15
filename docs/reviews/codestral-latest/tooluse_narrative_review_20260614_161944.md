**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:19:44


Bedingt deploy, weil Codestral valide Tool-Calls erzeugt und die Tool-Ausführung solide ist, aber die Synthesequalität mit Combined 64.96 nur moderat ausfällt und ein Halluzinationssignal im Gesamtlauf für produktive Wissenspipelines ein Sicherheitsrisiko bleibt.

**Tool-Execution-Profil**

Die Werkzeugseite ist die klar stärkere Hälfte dieses Modells. P1 83.33 zeigt, dass Codestral MCP-konform arbeitet, valide Calls produziert und ohne Retry auskommt. Das spricht für stabile Einbindung in bestehende Tool-Infrastrukturen.

Bei Web Search & Tool Selection, also dem Test, ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, trifft es die Werkzeugwahl sehr sicher und erreicht P1 100. Das ist kein blindes Fetch-Muster. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Abruf prüft, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines, P1 80. Das Muster ist damit klar: gute Tool-Intelligenz bei der Auswahl, etwas weniger Präzision bei der letzten Meile der Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 47.50 ist der eigentliche Bremsfaktor. Besonders schwach sind EU License Research mit P2 20, also aktuelle Lizenzrestriktionen aus Web-Quellen verdichten, sowie Multilingual Search & Synthesis mit P2 15. Codestral holt Informationen an, verliert aber bei Verdichtung, Gewichtung und sauberer Übertragung in die Antwort an Qualität. Für produktive Pipelines heißt das: Das Tooling funktioniert besser als die inhaltliche Auswertung der Tool-Ausgabe.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research ist das Vertrauensbild gemischt. Es halluziniert dort nicht und bleibt formal innerhalb des abgerufenen Materials, was besser ist als ein Training-Ausweichmanöver. Der Content-Verification-State B1 bei P2 20 zeigt aber, dass die Bindung an das Quellmaterial schwach bleibt. Da im Gesamtlauf ein Halluzinationssignal erkannt wurde, ist das kein bloßer Qualitätsfehler, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen scheiternden Tool-Call prüft, verhält sich Codestral produktionsgerecht. P2 80 und keine Halluzination trotz 404 bedeuten: Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. Das ist für robuste Automationspfade akzeptabel.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistung liegt mit einem Sovereignty Gap von -1.37 Punkten unter dem Fleet-Ø von 67.84 fast auf Fleet-Niveau.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Code-nahe Tool-Orchestrierung, strukturierte Abrufe und saubere Fehlerbehandlung wichtiger sind als hochwertige Endsynthese. Gut einsetzbar als lokales Ausführungsmodell hinter engeren Guards, festen Antwortschemata und nachgelagerter Verifikation. Nicht die richtige Wahl für Compliance-, Research- oder mehrsprachige Wissenspipelines, in denen die letzte Antwort selbst belastbar sein muss.