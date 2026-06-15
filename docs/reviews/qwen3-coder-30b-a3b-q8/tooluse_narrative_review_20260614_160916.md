**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:09:16


Bedingt deploy: Das Modell ist bei Tool-Aufrufen verlässlich und protokollkonform, aber die Synthese bleibt zu oft zu grob und es wurde mindestens eine Halluzination erkannt, was in produktiven Tool-Pipelines ein Sicherheitsrisiko darstellt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Mit P1 90 produziert es valide Calls, bleibt MCP-konform und brauchte keinen Retry. Das spricht gegen ein Formatproblem und für belastbares Verständnis der Aufgabensituation. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt das Modell den Bedarf für web_search zuverlässig. Das ist ein Signal für echte Werkzeugwahl statt starrem Fetch-Muster. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Abruf misst, arbeitet es brauchbar, aber nicht vollständig deterministisch. P1 80 ist für Assistenz-Workflows tragbar, für harte Automationspfade mit exakter URL-Bildung aber noch nicht sauber genug.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 55 zeigt, dass das Modell gefundene Inhalte oft nicht präzise genug zusammenzieht. Die Schwäche ist besonders sichtbar bei Multilingual Search & Synthesis, wo die sprachübergreifende Recherche gelingt, die deutsche Verdichtung aber deutlich abfällt. Für Pipelines, in denen exakte Faktenkonsolidierung wichtiger ist als die reine Tool-Bedienung, ist das die zentrale Bremse.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Modell auf der Tool-Spur. P2 60 ist nicht stark, aber der Vertrauensbefund ist positiv: Content-Verification-State A, keine Halluzination. Gleichzeitig gilt der globale Halluzinationsbefund als Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Infrastruktur, auch wenn der konkrete Honeypot bestanden wurde.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagendem Abruf prüft, reagiert das Modell produktionsnah. Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. P2 80 und keine Halluzination trotz 404 sind für den Betrieb akzeptabel. Das ist ein wichtiges Mindestkriterium für robuste MCP-Pipelines.

**Souveränitätsprofil**

Lokal betreibbar und insgesamt fleet-kompetent, aber nicht führend. Mit einem Sovereignty Gap von -1.37 Punkten liegt es 1.37 Punkte unter dem Fleet-Ø von 67.84. Für eine lokale, souveräne Tool-Infrastruktur ist das ein guter, aber kein kompromissloser Qualitätsstand.

**Fazit & Empfehlung**

Geeignet für lokale Coding- und Retrieval-Pipelines, in denen das Modell primär Tools korrekt ansteuern, Suchpfade erkennen und Fehler sauber offenlegen soll. Nicht die erste Wahl für Compliance-nahe oder mehrsprachige Synthese-Pipelines, in denen die Verdichtung selbst als verlässliches Endprodukt dienen muss. Empfehlenswert als Tool-Operator mit nachgelagerter Validierung oder zweitem Prüfschritt. Nicht empfehlenswert als alleinige Instanz für faktische Endantworten.