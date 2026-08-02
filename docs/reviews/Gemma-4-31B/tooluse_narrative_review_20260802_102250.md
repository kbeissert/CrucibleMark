**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:22:50


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Combined 67.83 und ungültigem Tool-Call-Status nicht verlässlich genug für unbeaufsichtigte High-Trust-Pipelines ausfällt.

**Tool-Execution-Profil**

Gemma 4 31B Instruct zeigt echte Werkzeugintelligenz, nicht nur starres Schema-Verhalten. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis Suche statt direktem Fetch nötig ist, wählt es das richtige Tool durchgehend. Das spricht für brauchbare Planungslogik in dynamischen MCP-Abläufen. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch. Genau dort liegt der operative Vorbehalt: Es versteht den nächsten Schritt meist richtig, produziert aber nicht durchgehend einen protokollsauberen, validen Call. Dass tool_call_valid insgesamt false ist, wiegt schwerer als der hohe P1-Schnitt von 90. Retry war nicht nötig. Das spricht eher gegen ein bloßes Formatproblem und eher für inkonsistente Ausführung im Einzelfall.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 49.17 ist für produktive Tool-Pipelines der schwächste Teil des Profils. In EU License Research und Multilingual Search & Synthesis holt es die Informationen über Tools, komprimiert sie aber zu grob oder lässt entscheidende Präzisierungen aus. Bei HTTP Fetch & Extract ist die Verdichtung solider, aber noch nicht auf dem Niveau, das man für belastbare Extraktionsketten ohne Nachprüfung freigibt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt das Vertrauenssignal grundsätzlich intakt: keine erkannte Halluzination, obwohl der Test genau prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden. Das ist wichtig. Der schwache P2-Wert von 40 zeigt hier also eher mangelhafte Verdichtung als erfundene Fakten. Für Compliance-nahe Workflows ist das deutlich besser als Halluzination, aber noch keine Freigabe für Vollautomation.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, reagiert das Modell produktionsgerecht. Es halluziniert keinen Seiteninhalt und kommuniziert den Fehler mit P2 80 ausreichend klar. Das ist ein belastbares Positivsignal. Fehler werden nicht verdeckt, sondern offengelegt. Für reale MCP-Pipelines ist das wichtiger als elegante Formulierungen.

**Souveränitätsprofil**

Lokal betreibbar mit Apache-2.0-Gewichten und damit für souveräne Umgebungen attraktiv. Zugleich liegt es 1.22 Punkte unter dem Fleet-Ø von 66.87. Das ist nah genug am Durchschnitt, um lokale Deployment-Argumente gelten zu lassen, aber nicht stark genug, um Qualitätsdefizite in der Synthese zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Recherche- und Orchestrierungs-Pipelines, in denen Tool-Wahl und Fehlertransparenz wichtiger sind als perfekte Ergebnisverdichtung. Nicht geeignet für Compliance-, Policy- oder Extraktionsstrecken, in denen die verbale Zusammenfassung selbst das Produkt ist und ohne menschliche Kontrolle weiterverarbeitet wird. Wenn Sie dieses Modell einsetzen, dann als tool-aware Operator mit nachgelagerter Validierung, nicht als letzte autoritative Syntheseschicht.