**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:23:54


Bedingt deploy, weil die Tool-Ausführung verlässlich bleibt und keine Halluzination erkannt wurde, die Synthesequalität mit 60.00 und ein Combined Score von 72.67 aber nicht für unkontrollierte End-to-End-Automation reichen.

**Tool-Execution-Profil**

DeepSeek V4 Pro arbeitet auf der Tool-Seite belastbar. P1 mit 86.67 ist für eine MCP-gestützte Pipeline klar brauchbar. Der Tool-Call war valide, ein Retry war nicht nötig, und es gab keinen Hinweis auf Protokollbruch oder fragile Formatierung. Das ist für produktive Verkettung wichtiger als reine Antwortqualität.

Bei der Werkzeugwahl bleibt das Bild nur teilweise abgesichert, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelwerte vorliegen. Aus dem Gesamtsignal lässt sich aber ableiten, dass das Modell nicht bloß starr einem Fetch-Muster folgt. Wäre die Tool-Seite mechanisch oder fehleranfällig, läge P1 nicht in diesem Bereich. Für dynamische Pipelines ist das ein gutes Zeichen, aber kein Beweis für saubere Tool-Intelligenz unter allen Routing-Fällen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht präzise genug für hochwertige Ergebnisverdichtung ohne Nachkontrolle. P2 mit 60.00 zeigt, dass DeepSeek V4 Pro Inhalte aus Tools grundsätzlich zusammenführt, dabei aber nicht konstant die Schärfe liefert, die man für Compliance, Policy oder faktenkritische Entscheidungsvorlagen erwartet. Für Recherche-Zusammenfassungen ist das nutzbar. Für verdichtete Single-Answer-Ausgaben mit hoher Verbindlichkeit ist es zu uneinheitlich.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist positiv. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist der entscheidende Sicherheitsbefund: Das Modell hat die Tool-Infrastruktur nicht durch erfundene Aktualität unterlaufen.

**Fehlerresilienz**

Im 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt misst, blieb das Modell sauber. Es hat trotz fehlgeschlagenem Tool-Call keinen Seiteninhalt erfunden. Das ist produktionsreif. Ein Tool-Fehler bleibt damit als Fehler sichtbar und wird nicht in scheinbar valide Antworttexte umgeschrieben.

**Betriebsprofil**

Call 1: 6.11s. Call 2: 21.93s. MCP-Latenz: 1.21s. Total: 175.51s.  
Direkte Aussage: langsam.  
Kosten pro Run: 0.002928 USD.  
Direkte Aussage: günstig bis sehr günstig für ein Frontier-Reasoning-Modell, gemessen an der gezeigten Tool-Stabilität.

**Fazit & Empfehlung**

Geeignet für recherchierende, mehrstufige Pipelines mit Human-in-the-Loop, für Agenten mit Fehlertransparenz und für kostensensitive Tool-Orchestrierung, bei der robuste Calls wichtiger sind als exzellente Verdichtung. Nicht geeignet als letzte Instanz für faktenkritische Synthesen, knappe Executive Summaries oder vollautomatische Compliance-Antworten ohne nachgelagerte Prüfung. Wenn Ihre Infrastruktur verlässliche Tool-Nutzung braucht und die finale Textverdichtung separat abgesichert ist, kann dieses Modell in Produktion funktionieren.