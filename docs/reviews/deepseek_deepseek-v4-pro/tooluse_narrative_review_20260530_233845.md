**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:38:45


Bedingt deploy, weil die Tool-Nutzung formal zuverlässig wirkt und keine Halluzination erkannt wurde, die Synthesequalität mit 60.00 bei einem Combined Score von 72.67 aber zu uneinheitlich für unkontrollierte End-to-End-Pipelines bleibt.

**Tool-Execution-Profil**

DeepSeek V4 Pro arbeitet auf der Tool-Ebene belastbar. Der Tool-Call war valide, MCP-konform, und ein Retry war nicht erforderlich. Das ist für produktive Orchestrierung der wichtigste Basisbefund: Das Modell bricht die Infrastruktur nicht durch Formatfehler oder Protokollverletzungen. Der P1-Wert von 86.67 bestätigt diese operative Stabilität.

Bei der Werkzeugwahl bleibt das Bild dennoch unvollständig. Für Web Search & Tool Selection und URL Construction & Fetch liegen keine Einzelwerte vor. Deshalb lässt sich nicht sauber belegen, ob das Modell situativ das richtige Werkzeug erkennt oder primär einem allgemeinen Tool-Use-Muster folgt. Aus den vorliegenden Zuverlässigkeitssignalen spricht mehr für robuste Ausführung als für nachgewiesene Tool-Intelligenz. Für Architekturen mit freier Tool-Wahl ist das ein Unterschied: valide Calls sind nicht dasselbe wie gute Call-Entscheidungen.

**Synthesetreue**

Wie gut verdichtet es? Nur eingeschränkt überzeugend. Ein P2-Wert von 60.00 ist für ein Frontier-Reasoning-Modell kein starkes Signal. Das Modell scheint Ergebnisse verwertbar zusammenzuführen, aber nicht mit der Präzision und Reduktionsschärfe, die man für Berichts-, Compliance- oder Research-Pipelines ohne harte Nachkontrolle erwarten sollte.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist der Befund positiv. Im EU License Research, also dem Honeypot-Test auf aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen, wurde keine Halluzination erkannt. Das stützt das Vertrauensurteil: Das Modell erfindet in diesem Datensatz keine extern wirkenden Fakten, wenn aktuelle Web-Belege erwartet werden.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Tool Failure Handling mit 404-Fehler, also dem Test auf transparente Reaktion statt erfundenem Seiteninhalt, halluzinierte das Modell keinen Ersatzinhalt. Das ist genau das Verhalten, das man in einer Tool-Pipeline braucht: Fehler offenlegen, nicht verdecken.

**Betriebsprofil**

Call 1: 6.11s. Call 2: 21.93s. MCP-Latenz: 1.21s. Total: 175.51s.  
Direktes Urteil: langsam.  
Kosten pro Run: 0.002928.  
Direktes Urteil: günstig bis sehr günstig relativ zur Frontier-Klasse, aber die Latenz steht nicht im Verhältnis zu einer nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Aufrufe strikt geführt, Ergebnisse nachgelagert validiert und Fehler transparent behandelt werden müssen. Weniger geeignet für autonome Research- oder Compliance-Strecken, in denen das Modell nicht nur Tools korrekt aufrufen, sondern deren Resultate auch präzise, knapp und belastbar verdichten soll. Wenn Sie ein kostengünstiges Thinking-Modell für kontrollierte Tool-Ausführung suchen, ist es verwendbar. Wenn Sie ein Modell suchen, dem Sie auch die letzte inhaltliche Verdichtung der Tool-Ergebnisse anvertrauen, ist Zurückhaltung angebracht.