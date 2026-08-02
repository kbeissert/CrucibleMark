**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:22:41


Bedingt deploy, weil die Tool-Ausführung insgesamt belastbar ist, aber die Synthesetreue mit Combined 73.17 und vor allem schwacher Verdichtung nicht ausreicht, um unbeaufsichtigt eine Tool-Infrastruktur zu tragen.  

**Tool-Execution-Profil**

Gemma 4 31B Instruct zeigt echte Werkzeugintelligenz, nicht nur starres Abarbeiten. Beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es P1 100 und erkennt den passenden Zugriffspfad sauber. Das ist ein starkes Signal für dynamische MCP-Pipelines. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL samt anschließendem Fetch misst, liegt es mit P1 80 darunter. Das spricht nicht gegen Tool-Nutzung, aber gegen volle Deterministik bei URL-Bildung. Kritisch ist, dass der Tool-Call insgesamt als nicht valide markiert wurde. Das mindert das Vertrauen in Protokolltreue stärker als die Einzelergebnisse vermuten lassen. Positiv ist, dass kein Retry nötig war. Das Problem wirkt daher eher wie punktuelle Call-Form oder Argumentpräzision als wie grundlegendes Missverständnis des Tooling-Modells.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mäßig. P2 56.67 zeigt ein Modell, das Quellen beschaffen kann, aber den Rücklauf nicht zuverlässig in belastbare, knappe Arbeitsantworten überführt. Das sieht man auch in den Asset-Werten: HTTP Fetch & Extract, Tool Failure Handling (404), URL Construction & Fetch und Multilingual Search & Synthesis bleiben jeweils bei P2 60, EU License Research sogar bei 40. Für Produktionsketten heißt das: Die Retrieval-Stufe trägt eher als die Antwortstufe.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das zentrale Vertrauenssignal. Trotz schwacher Verdichtung bricht das Modell die Tool-Grenze nicht sichtbar auf und erfindet keine vermeintlich recherchierten Compliance-Fakten.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei scheiterndem Tool-Call misst, halluziniert das Modell keinen Seiteninhalt. Das ist für Produktion akzeptabel. P2 60 zeigt, dass die Fehlerkommunikation nicht besonders präzise oder hilfreich ist, aber sie bleibt ehrlich. Für operative Pipelines ist das wesentlich wichtiger als elegante Formulierung.

**Souveränitätsprofil**

Lokal betreibbar mit Apache-2.0-Gewichten und ohne Cloud-Bindung. Das Modell liegt  -1.22 Punkte unter dem Fleet-Ø von 66.87 und bleibt damit souveränitätsseitig konkurrenzfähig, ohne nennenswerten Qualitätsabschlag für On-Prem-Betrieb.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines, in denen Tool-Auswahl, Web-Recherche und Fehlertransparenz wichtiger sind als hochwertige Endverdichtung. Gut einsetzbar als Retrieval- und Orchestrierungskomponente mit nachgelagerter Validierungs- oder Redaktionsstufe. Nicht die erste Wahl für Compliance-, Executive- oder Customer-facing-Pipelines, in denen die ausformulierte Synthese selbst schon produktionsreif sein muss.