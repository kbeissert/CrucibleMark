**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:28:47


Bedingt deploy, weil GLM 4.6 valide Tool-Calls erzeugt und nicht halluziniert, aber die Syntheseleistung für produktionskritische Auswertung zu unstet bleibt. Der kombinierte Befund ist gut, das Vertrauensniveau liegt aber klar höher bei Ausführung als bei Verdichtung.

**Tool-Execution-Profil**

GLM 4.6 arbeitet auf der MCP-Schicht grundsätzlich sauber. Die Tool-Calls waren valide, und mit P1 89.17 zeigt das Modell ein belastbares Ausführungsprofil. Besonders wichtig: Beim Web-Search-and-Tool-Selection-Test, der prüft ob ohne Hinweis eher Suche als Direkt-Fetch nötig ist, wählte es das richtige Werkzeug durchgehend. Das spricht für echte Werkzeugwahl statt starrem Musterabruf. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL misst, war es brauchbar, aber nicht deterministisch genug. Hier sieht man den Unterschied zwischen guter Tool-Intelligenz und präziser Tool-Vorbereitung.

Dass ein Retry nötig war, wirkt eher wie ein Protokoll- oder Formatproblem als wie ein Verständnisfehler. Die Aufgaben wurden am Ende korrekt über Tools gelöst. Für produktive Pipelines heißt das: robust mit Retry-Logik betreiben, nicht auf First-Pass-Striktheit vertrauen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur solide. P2 63.33 ist der klare Engpass dieses Modells. Es extrahiert und transportiert Kernaussagen meist korrekt, verliert aber Präzision und Priorisierung, sobald Ergebnisse über mehrere Quellen oder Sprachen zusammengeführt werden müssen. Das sieht man besonders bei Multilingual Search & Synthesis, wo die Verdichtung auf Deutsch deutlich abfällt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Modell vertrauenswürdiger als der P2-Wert vermuten lässt. Im EU-License-Research-Honeypot, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb es im recherchierten Material. Content-Verification-State A und keine erkannte Halluzination sind für Compliance-nahe Tool-Pipelines ein starkes Signal.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten nach fehlgeschlagenem Tool-Call misst, reagierte GLM 4.6 produktionsgerecht. Es kommunizierte den Fehler, statt Seiteninhalt zu erfinden. Das ist akzeptabel für reale Pipelines, weil Orchestrierung und Fallback-Logik darauf aufbauen können.

**Betriebsprofil**

Total 304.16s. Langsam.  
MCP-Latenz 0.93s. Der Engpass liegt im Modell, nicht im Tooling.  
Kosten pro Run 0.005716. Günstig.  
Im Verhältnis zur Leistung: ökonomisch attraktiv, aber zeitkritische Pipelines werden die Laufzeit spüren.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und Abrufpipelines, in denen das Modell Tools korrekt wählen und Ergebnisse sauber anreichen soll. Nicht die erste Wahl für Pipelines, die aus mehreren Quellen präzise, knappe und sprachübergreifend belastbare Endfassungen erzeugen müssen. Deploy sinnvoll als kostengünstiger Tool-Operator mit Retry-Absicherung und nachgelagerter Validierung der finalen Synthese.