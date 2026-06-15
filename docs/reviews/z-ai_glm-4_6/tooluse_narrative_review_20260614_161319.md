**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:13:19


Bedingt deploy, weil GLM 4.6 valide Tool-Calls erzeugt und nicht halluziniert, aber die Synthesequalität mit Combined 75.92 nur dann tragfähig ist, wenn nachgelagerte Validierung die Verdichtung kontrolliert.

**Tool-Execution-Profil**

In der Werkzeugausführung wirkt das Modell kompetent. Der Tool-Call war valide, Halluzination wurde nicht erkannt, und in **Web Search & Tool Selection**, das ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, traf es die richtige Entscheidung sicher. Das spricht gegen starres Musterverhalten und für echte Tool-Wahl im Kontext. Schwächer ist es bei **URL Construction & Fetch**, das die korrekte Ziel-URL aus Eigenwissen ableitet und dann abruft: brauchbar, aber nicht deterministisch genug für Pipelines, die exakte Endpunkte ohne Korrekturschritt erwarten. Dass ein Retry erforderlich war, wirkt hier eher wie ein Protokoll- oder Formatproblem als ein Verständnisfehler. Die Ausführungskompetenz ist hoch, aber nicht sauber genug für Zero-Touch-Orchestrierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 von 63.33 ist der eigentliche Grenzwert dieses Modells. In **HTTP Fetch & Extract**, das strukturierte Fakten aus echtem Seiteninhalt zieht, arbeitet es solide. In **Multilingual Search & Synthesis**, das sprachübergreifende Recherche und deutsche Verdichtung prüft, fällt die Qualität jedoch klar ab. Das Modell findet die Quellen, komprimiert sie aber nicht konsistent präzise genug für belastbare Entscheidungsoutputs.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Modell grundsätzlich im Arbeitsmodus der Pipeline. P2 60 ist nicht stark, aber der Vertrauensbefund ist positiv: Content-Verification-State A, keine Halluzination. Für Compliance-nahe Retrieval-Strecken ist das wichtiger als sprachliche Eleganz.

**Fehlerresilienz**

Beim **Tool Failure Handling (404)**, das die Reaktion auf fehlschlagende Abrufe prüft, kommuniziert GLM 4.6 transparent statt Seiteninhalt zu erfinden. P2 80 bei ausbleibender Halluzination ist für Produktion akzeptabel. Das Modell bricht Vertrauen also nicht genau dort, wo viele Tool-Modelle riskant werden.

**Betriebsprofil**

Call 1: 16.36s. Call 2: 33.40s. MCP-Latenz: 0.93s. Total: 304.16s.  
Kosten pro Run: $0.005716.  
Urteil: langsam, aber sehr günstig im Verhältnis zur gezeigten Tool-Ausführung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Web-Recherche, Abruf, Fehlerbehandlung und nachgelagerter Prüfung der Antwortverdichtung. Nicht geeignet für vollautomatisierte Entscheidungsstrecken, in denen die Endantwort selbst bereits die verlässliche Wahrheitsschicht sein muss, besonders bei mehrsprachiger Synthese oder URL-genauer Retrieval-Logik. Zusätzlich bleibt der Produktionseinsatz wegen der eingeschränkten kommerziellen Nutzung und des hohen Provenienzrisikos nur in eng kontrollierten Umgebungen vertretbar.