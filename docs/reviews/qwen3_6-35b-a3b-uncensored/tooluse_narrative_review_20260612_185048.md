**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:50:48


Bedingt deploy, weil die Tool-Aufrufe meist valide sind und die Ausführung stark wirkt, das Modell aber bei der inhaltlichen Rückbindung an Tool-Ergebnisse ein reales Halluzinationsrisiko trägt. Der Combined-Score von 59.58 ist dafür nur tragfähig, wenn die Pipeline externe Verifikation erzwingt.

**Tool-Execution-Profil**

In der Werkzeugnutzung zeigt das Modell echte Handlungsfähigkeit. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es mit P1 95 meist korrekt, dass erst gesucht werden muss. Das spricht gegen starres Schema-Verhalten. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen und anschließenden Fetch misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Pipelines.

Tool-Calls sind insgesamt valide. MCP-Protokolltreue ist damit grundsätzlich gegeben. Dass ein Retry erforderlich war, wirkt hier eher wie ein Stabilitätsproblem im Ablauf als wie fehlendes Tool-Verständnis. Das Muster ist: richtige Werkzeugwahl, dann nicht immer saubere Erstlandung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 40.83 ist der Kernschaden dieses Modells. Es kann Quellen abrufen und technische Schritte ausführen, verdichtet die Ergebnisse aber oft unpräzise oder mit schwacher Disziplin. Das sieht man besonders an EU License Research mit P2 15 und Multilingual Search & Synthesis mit P2 15. Dagegen ist HTTP Fetch & Extract mit P2 80 ein Hinweis, dass es bei enger, strukturiert vorliegender Evidenz deutlich verlässlicher arbeitet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde eine Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Fakten als Tool-Ergebnis ausgibt, untergräbt es die Vertrauenskette der gesamten MCP-Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call misst, halluziniert das Modell keinen Ersatzinhalt. P2 60 ist nicht elegant, aber produktionsfähig. Es signalisiert Fehler akzeptabel statt eine nicht existente Seite zu erfinden. Das ist ein wichtiger positiver Befund.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistungsseitig liegt es mit einem Sovereignty Gap von -1.37 Punkten knapp unter dem Fleet-Ø von 67.62. Das ist konkurrenzfähig genug, wenn lokale Kontrolle wichtiger ist als maximale Synthesetreue.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Tool-Pipelines mit enger Aufgabenschablone, strukturierten Quellen und nachgelagerter Validierung, etwa Fetch-Extraktion, Suchschritt-Orchestrierung und robuste Assistenzflüsse. Nicht geeignet für Compliance-, Policy- oder Forschungs-Pipelines, in denen das Modell Tool-Ergebnisse frei zusammenfassen und als belastbare Fakten ausgeben darf. Wer dieses Modell einsetzt, sollte Antwortsynthese hart gegen Quelltext prüfen und ungeprüfte Freitext-Zusammenfassungen nicht freischalten.