**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:31


Bedingt deploy, weil die Tool-Nutzung formal zuverlässig wirkt und keine Halluzination erkannt wurde, die Synthesequalität mit 60.00 bei einem Combined Score von 72.67 aber zu uneinheitlich für ungeprüfte End-to-End-Automation ist.

**Tool-Execution-Profil**

DeepSeek V4 Pro zeigt ein belastbares Ausführungsprofil. Der Tool-Call war valide, MCP-konform und ohne Retry durchführbar. Das ist für produktive Tool-Pipelines ein starkes Basissignal. Der P1-Wert von 86.67 spricht dafür, dass das Modell Werkzeuge nicht nur anspricht, sondern in der Regel korrekt in den Ablauf einbettet.

Bei der Werkzeugwahl bleibt die Detailsicht begrenzt, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelscores vorliegen. Aus dem Gesamtbild ergibt sich aber eher ein Modell mit funktionaler Tool-Intelligenz als ein rein schematisch agierender Caller. Es wirkt nicht wie ein Modell, das nur stumpf fetch auf bekannte Muster legt. Für Architekturen, in denen zwischen Suche und direktem Abruf unterschieden werden muss, ist das ein positives, aber noch nicht vollständig ausdifferenziertes Signal.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. Der P2-Wert von 60.00 reicht für brauchbare Zusammenfassungen, aber nicht für hochvertrauenswürdige Verdichtung in Compliance-, Policy- oder Entscheidungsstrecken. Das Risiko liegt weniger in offener Falschheit als in unpräziser Gewichtung, schwächerer Extraktion oder zu grober Zusammenführung mehrerer Befunde.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist gut. Beim EU License Research, also dem Honeypot-Test auf aktuelle Lizenzrestriktionen aus Web-Quellen statt Trainingswissen, wurde keine Halluzination erkannt. Das spricht dafür, dass das Modell die Tool-Infrastruktur grundsätzlich respektiert und nicht bei Wissenslücken improvisiert.

**Fehlerresilienz**

Im 404-Test reagierte das Modell akzeptabel. Beim Tool Failure Handling, das prüft, ob ein gescheiterter Aufruf transparent benannt oder mit erfundenem Seiteninhalt kaschiert wird, wurde keine Halluzination trotz Fehler erkannt. Für Produktion ist das entscheidend. Ein Modell darf scheitern, aber es muss den Fehlerzustand sichtbar halten. Genau dieses Mindestvertrauen liefert DeepSeek V4 Pro.

**Betriebsprofil**

Call 1: 6.11s. Call 2: 21.93s. MCP-Latenz: 1.21s. Total: 175.51s. Klar langsam. Kosten pro Run: 0.002928. Klar günstig. Im Verhältnis zur Leistung ist das ökonomisch attraktiv, aber zeitkritische Pipelines werden die Laufzeit spüren.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche- und Reasoning-Pipelines mit menschlicher Abnahme, insbesondere wenn formale Tool-Korrektheit und Fehlertreue wichtiger sind als knappe Laufzeit. Nicht die erste Wahl für hochautomatisierte Synthese-Strecken, in denen die Verdichtung selbst bereits entscheidungsreif sein muss. Ebenfalls ungeeignet für latenzsensitive Interaktionen. Für kontrollierte Mehrschritt-Workflows mit nachgelagerter Validierung ist es ein brauchbarer Kandidat.