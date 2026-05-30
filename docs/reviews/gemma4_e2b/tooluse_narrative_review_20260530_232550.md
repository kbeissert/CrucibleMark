**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:25:50


Bedingt deploybar, weil Gemma 4 2B valide Tool-Calls erzeugt und im MCP-Ablauf zuverlässig bleibt, aber die Synthesetreue mit Combined 67.75 und erkannten Halluzinationen für vertrauenskritische Pipelines nicht ausreicht.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. P1 liegt bei 90. Das Modell wählt Werkzeuge nicht nur schematisch, sondern meist zweckgerecht. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis statt fetch ein Such-Tool nötig ist, erreicht es 100 und zeigt damit echte Werkzeugwahl statt bloßes Formatlernen. Auch im Honeypot EU License Research greift es korrekt zu aktuellen Web-Quellen.

Schwächer ist die Präzision, sobald es selbst Zieladressen konstruieren muss. Beim URL-Construction-Test, der die Ableitung einer korrekten Ziel-URL aus Eigenwissen misst, ist der Call zwar meist brauchbar, aber nicht präzise genug für deterministische Pipelines. P1 von 80 ist dafür akzeptabel, aber kein Freifahrtschein. Positiv: Die Calls bleiben valide, retry war nicht erforderlich. Das spricht für Protokolltreue, nicht nur für inhaltliches Verständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. P2 von 45.83 zeigt, dass Gemma 4 2B gefundene Inhalte oft zu grob zusammenzieht, Details verliert oder unsauber priorisiert. Das Muster zieht sich durch mehrere Assets: EU License Research mit P2 40, Multilingual Search & Synthesis mit P2 40 und besonders URL Construction & Fetch mit P2 15. Für reine Retrieval-Weitergabe ist das noch tragbar. Für präzise Ergebnisverdichtung mit mehreren Faktenquellen ist es zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diese Grenze testet, bleibt das Modell auf der sicheren Seite: Content-Verification-State A, keine Halluzination. Das ist das wichtigste Vertrauenssignal im Datensatz. Trotzdem ist die global erkannte Halluzination ein Sicherheitsrisiko. In einer Tool-Pipeline reicht ein einzelner erfundener Befund, um die Glaubwürdigkeit der gesamten Infrastruktur zu beschädigen.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten nach einem fehlschlagenden Tool-Call misst, reagiert das Modell akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler sichtbar. P2 60 ist kein Qualitätsbeweis, aber operativ ausreichend. Für Produktion ist entscheidend: kein halluzinierter Ersatzinhalt trotz Fehler.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Deployments praktisch nutzbar. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Damit ist das Modell im lokalen Betrieb konkurrenzfähig genug, wenn Infrastrukturkontrolle wichtiger ist als maximale Antwortgüte.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit klaren Tool-Grenzen, einfacher Recherche, robustem Post-Validation-Layer und geringer semantischer Fallhöhe. Nicht geeignet für Compliance, regulatorische Auswertung, präzise mehrquellige Verdichtung oder Workflows, in denen die Modellantwort direkt als verlässliches Endergebnis dient. Als kostengünstiger Tool-Operator ist es brauchbar. Als Synthese-Instanz ist es zu unsicher.