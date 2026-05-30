**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:14


Bedingt deploy, weil Claude Opus 4.7 zuverlässig valide Tool-Calls produziert und nicht halluziniert, aber die Syntheseleistung mit Combined 80.67 und P2 76.67 nicht durchgehend präzise genug für jede wissenskritische Pipeline ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist produktionsreif. Tool-Calls waren valide, MCP-konform und ohne Retry lauffähig. Das ist der Kernbefund. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erkennt das Modell den Werkzeugbedarf sicher und erreicht P1 100. Das spricht für echte Werkzeugwahl statt starrem Ablauf.

Weniger stark ist es beim URL-Construction-Test, der prüft ob das Modell eine Ziel-URL aus eigenem Wissen ableitet und dann korrekt fetched. Mit P1 80 arbeitet es brauchbar, aber nicht deterministisch genug für Flows, in denen URL-Bildung ohne Vorvalidierung direkt produktiv gehen soll. Das Muster ist klar: Bei offener Tool-Entscheidung ist es stark, bei präziser Ableitung eines konkreten Endpunkts anfälliger.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht konstant scharf genug. HTTP Fetch & Extract und Tool Failure Handling (404) liegen bei P2 100, also klare und genaue Verdichtung aus vorhandenem Material. Dagegen fällt Multilingual Search & Synthesis mit P2 40 deutlich ab. Auch EU License Research bleibt mit P2 60 hinter dem zurück, was man für Compliance-nahe Ausgaben erwartet. Das Modell kann Tool-Resultate gut strukturieren, verliert aber bei sprachübergreifender oder regulatorisch sensibler Verdichtung an Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Punkt testet, bleibt das Modell innerhalb der abgerufenen Quellen. Halluzination wurde nicht erkannt, der Verifikationsstatus ist A. Das Vertrauenssignal ist gut: Es erfindet keine aktuellen Lizenzrestriktionen aus dem Training. Die Schwäche liegt hier in der Verdichtung, nicht in der Quellenbindung.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, reagiert Claude Opus 4.7 vorbildlich. P2 100, keine Halluzination trotz Fehler. Für Produktion ist das akzeptabel und wichtig: Das Modell meldet den Ausfall, statt Seiteninhalt zu erfinden und damit den Tool-Layer zu unterlaufen.

**Betriebsprofil**

Total 112.66s. Einzelcalls 2.45s und 15.04s. MCP-Latenz 1.29s. Für die gelieferte Qualität langsam. Kosten pro Run 0.191580 USD. Für Frontier-Einsatz klar teuer.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Recherche, Tool-Orchestrierung und transparentem Fehlerverhalten, besonders wenn ein nachgelagerter Validator die finale Antwort prüft. Nicht die erste Wahl für Compliance-nahe Synthesen, mehrsprachige Recherche oder deterministische URL-Ableitung ohne Guardrails. Deployen, wenn Tool-Treue und Planungsstärke wichtiger sind als knappe Laufzeit und maximal präzise Endverdichtung.