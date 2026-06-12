**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:43:25


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, die Synthesequalität aber zu oft vom Tool-Befund in unsaubere Verdichtung kippt und ein Halluzinationssignal im Gesamtlauf ein Produktionsrisiko markiert.

**Tool-Execution-Profil**

In der Werkzeugschicht ist das Modell klar brauchbar. Es produziert valide Tool-Calls, bleibt MCP-protokollkonform und benötigt keinen Retry. Das ist für eine Tool-Pipeline die wichtigste Grundvoraussetzung. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis search statt fetch gewählt wird, zeigt es echte Werkzeugintelligenz und nicht nur starres Call-Muster. Der Wert von 100 in P1 spricht dafür, dass es den Informationsbedarf korrekt erkennt. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL prüft, arbeitet es funktional, aber nicht deterministisch genug für hochpräzise Fetch-Pipelines. P1 80 heißt: brauchbar für robuste Orchestrierung, nicht ideal für fragile Endpunkte oder Compliance-Scraper mit harter URL-Abhängigkeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt produktionsreif. P2 von 55 ist der eigentliche Engpass. Das Modell holt Informationen meist korrekt herein, verdichtet sie dann aber uneinheitlich. Besonders sichtbar wird das bei Web Search & Tool Selection mit P2 35 und bei Multilingual Search & Synthesis mit P2 15. Für Pipelines, die aus Tool-Output belastbare Kurzanalysen, Entscheidungsnotizen oder deutschsprachige Zusammenfassungen erzeugen sollen, ist das zu schwankend.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, verhält es sich sauber. Content-Verification-State A und keine Halluzination sind ein starkes Vertrauenssignal. Gleichzeitig bleibt das globale Halluzinationsflag ein Sicherheitsbefund. In Produktion zählt nicht, ob Halluzination selten ist, sondern ob sie überhaupt als Tool-Ergebnis erscheinen kann.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call misst, reagiert das Modell akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler nachvollziehbar. P2 80 ist hier das richtige Profil für Produktion. Ein gescheiterter Aufruf bleibt als gescheiterter Aufruf erkennbar. Das schützt die Pipeline vor stillen Falschbefunden.

**Souveränitätsprofil**

Lokal betreibbar und insgesamt fleet-kompetitiv. Der Combined-Score liegt 1.37 Punkte unter dem Fleet-Ø von 67.62. Für eine lokal souveräne Option ist das ein solides Ergebnis. Die Laufzeit ist jedoch nicht leichtgewichtig: 58.71s total bei 1.17s erstem Call, 7.79s zweitem Call und 0.82s MCP-Latenz.

**Fazit & Empfehlung**

Geeignet für lokal betriebene MCP-Pipelines, in denen Tool-Auswahl, strukturierte Ausführung und sauberes Fehlerverhalten wichtiger sind als hochwertige sprachliche Verdichtung. Gut passend für Retrieval, technische Recherche, Code-nahe Agenten und operator-geprüfte Workflows. Nicht die richtige Wahl für Compliance-Memos, mehrsprachige Synthese, Executive Summaries oder jede Pipeline, in der die Endantwort ohne nachgelagerte Validierung direkt konsumiert wird.