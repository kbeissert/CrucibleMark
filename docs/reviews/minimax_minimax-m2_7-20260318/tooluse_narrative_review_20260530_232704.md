**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:04


Bedingt deploy, weil die Tool-Aufrufe nicht durchgängig valide sind, ein Retry nötig war und die Gesamtleistung mit 50.96 klar unter einer belastbaren Produktionsschwelle für MCP-Tool-Pipelines bleibt.

**Tool-Execution-Profil**

MiniMax M2.7 zeigt kein stabiles Werkzeugurteil. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis zwischen web_search und fetch unterschieden wird, fällt es mit P1 35 deutlich ab. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Abruf misst, arbeitet es dagegen mit P1 80 solide. Das spricht nicht für echte Tool-Intelligenz, sondern für ein engeres Erfolgsmuster: Wenn die Fetch-Richtung einmal feststeht, liefert es brauchbar. Wenn die Werkzeugwahl offen ist, irrt es sichtbar. Dass der Tool-Call insgesamt als nicht valide gewertet wurde und ein Retry nötig war, deutet eher auf ein Protokoll- oder Formatproblem im MCP-Ablauf als auf reines Wissensdefizit. Für produktive Orchestrierung ist das trotzdem kritisch, weil fehlerhafte Call-Strukturen den gesamten Lauf blockieren.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. P2 43.33 passt zu einem Profil, das extrahierte Fakten nicht verlässlich in eine präzise, entscheidbare Antwort überführt. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo die Verdichtung aus den abgerufenen Quellen zu dünn bleibt. Wo der Input klar und eng ist, etwa bei HTTP Fetch & Extract, kann es Ergebnisse noch sauber zusammenziehen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der genau das Abgleiten in Trainingswissen prüfen soll, zeigt keinen Halluzinationsbefund, aber auch kein gutes Vertrauenssignal. P2 20 bei Content-Verification-State B1 heißt: Es erfindet nichts offen, bleibt aber nicht sauber genug an den verifizierbaren Web-Inhalten. Für Compliance-nahe Recherche ist das zu unsicher.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten nach einem fehlschlagenden Tool-Call misst, halluziniert MiniMax M2.7 keinen Ersatzinhalt. Das ist der wichtigste Punkt. P2 60 zeigt akzeptable Fehlerkommunikation, auch wenn die Antwort nicht besonders stark weiterführt. Für Produktion ist dieses Verhalten brauchbar, weil das Modell einen Fehlzustand nicht in erfundene Fakten umwandelt.

**Betriebsprofil**

Call 1: 3.92s. Call 2: 6.71s. MCP-Latenz: 0.20s. Total: 65.05s.  
Kosten pro Run: $0.0048.  
Direktaussage: günstig, aber für die erzielte Leistung zu langsam und zu inkonsistent.

**Fazit & Empfehlung**

Geeignet für einfache Fetch-gebundene Pipelines mit enger Aufgabenführung, klarer URL oder vordefinierter Tool-Reihenfolge. Nicht geeignet für dynamische MCP-Setups, in denen das Modell selbst das richtige Werkzeug wählen, Suchschritte einleiten oder mehrsprachige Recherche belastbar verdichten muss. Wenn es eingesetzt wird, dann nur hinter harter Tool-Gating-Logik, Response-Validation und Retry-Handling außerhalb des Modells.