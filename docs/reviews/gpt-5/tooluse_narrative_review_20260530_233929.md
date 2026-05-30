**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:29


Bedingt deploy, weil GPT-5 valide Tool-Calls produziert und nicht halluziniert, aber die Synthesetreue für produktive Tool-Pipelines zu oft unter dem Ausführungsniveau bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist belastbar. Mit P1 85.83 arbeitet das Modell MCP-konform, erzeugt valide Calls und bleibt über die sechs Aufgaben hinweg klar im operativen Rahmen. Besonders wichtig ist die Werkzeugwahl: Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis zwischen Suche und direktem Fetch unterscheiden lässt, erkennt GPT-5 den Bedarf nach web_search meist korrekt. Beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und dann sauber abrufen lässt, ist es ebenfalls solide, aber nicht deterministisch genug für Pipelines mit harter URL-Präzision.

Das spricht eher für echte Tool-Intelligenz als für ein starres Muster. Die Entscheidungen sind kontextsensitiv, aber nicht fehlerfrei. Dass ein Retry erforderlich war, wirkt hier eher wie ein Protokoll- oder Formatproblem im Ablauf als ein Verständnisfehler der Aufgabe. Inhaltlich kippt das Modell nicht aus der Spur, operativ kostet es aber Orchestrierungsrobustheit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. P2 56.67 ist der klare Engpass. GPT-5 extrahiert und sammelt Informationen brauchbar, verdichtet sie aber in mehreren Aufgaben nicht präzise genug für Architekturen, die knappe, quellennah formulierte Ergebnisobjekte erwarten. Das sieht man besonders bei EU License Research und Tool Failure Handling (404), wo die Ausführung trägt, die Zusammenfassung aber an Präzision verliert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen geholt werden, bleibt GPT-5 im zulässigen Vertrauensrahmen. Content-Verification-State A und kein Halluzinationsbefund sind das stärkste Produktionssignal dieses Runs. Das Modell ist hier also nicht erfinderisch, sondern eher zu interpretativ.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf prüft, halluziniert GPT-5 keinen Ersatzinhalt. Das ist für Produktion entscheidend. P2 40 zeigt aber, dass die Fehlerkommunikation nicht präzise genug verdichtet wird. Akzeptabel ist das trotzdem: Ein offen gemeldeter Tool-Fehler ist beherrschbar, erfundener Seiteninhalt wäre ein Ausschlusskriterium.

**Betriebsprofil**

Call 1: 6.88s. MCP-Latenz: 1.40s. Call 2: 23.18s. Total: 188.78s. Langsam. Kosten pro Run: $0.077128. Für die gezeigte Leistung eher teuer.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Aufruf, Recherche und sichere Fehlerbehandlung wichtiger sind als knappe, streng quellengebundene Endverdichtung. Gut passend für analystische Copilots, moderierte Research-Flows und Human-in-the-loop-Systeme. Nicht die erste Wahl für Compliance-Zusammenfassungen, deterministische Extraktionsketten oder nachgelagerte Systeme, die aus der Modellausgabe direkt strukturierte Entscheidungen ableiten.