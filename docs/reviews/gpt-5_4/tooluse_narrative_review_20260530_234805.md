**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:48:05


Bedingt deploy, weil die Halluzinationssicherheit im Fehlerfall brauchbar ist, aber die Tool-Calls nicht durchgängig valide sind und die Gesamtleistung mit 51.96 für eine produktive MCP-Pipeline zu inkonsistent ausfällt.

**Tool-Execution-Profil**

GPT-5.4 zeigt kein verlässliches Werkzeugurteil, sondern ein uneinheitliches Muster. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, fällt es mit P1 35 deutlich ab. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Weltwissen misst, arbeitet es dagegen mit P1 80 solide. Das spricht nicht für stabile Tool-Intelligenz, sondern dafür, dass bekannte Fetch-Pfade besser funktionieren als offene Auswahlentscheidungen.

Die schwache Validität der Tool-Calls ist für Produktion der eigentliche Blocker. Retry erforderlich bei zugleich ungültigem Tool-Call deutet hier eher auf ein Protokoll- oder Formatproblem im MCP-Ablauf als auf reines Wissensversagen. Für eine Tool-Pipeline heißt das: Orchestrierung, Validierung und gegebenenfalls Call-Rewriting müssen außerhalb des Modells abgesichert werden.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. P2 46.67 ist für ein Frontier-Generalistenmodell zu niedrig, und die Schwächen sind breit sichtbar: EU License Research 20, Web Search & Tool Selection 20, Multilingual Search & Synthesis 20. Wo die Quelle klar und lokal vorliegt, etwa bei HTTP Fetch & Extract mit 80, kann es Ergebnisse ordentlich komprimieren. Sobald mehrere Quellen, Suchschritte oder Sprachwechsel ins Spiel kommen, verliert es Präzision und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen gegen altes Weltwissen absichert, halluziniert es nicht. Das ist das positive Kernsignal. Der Content-Verification-State B2 und P2 20 zeigen aber, dass es zwar nicht frei erfindet, die verifizierte Web-Lage jedoch nur schwach in eine belastbare Antwort überführt.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, reagiert das Modell produktionsgerecht. P2 80 und keine Halluzination trotz Fehler sprechen dafür, dass es Fehlschläge offen kommuniziert statt Seiteninhalt zu erfinden. Das ist für produktive Systeme akzeptabel und deutlich wichtiger als formale Eleganz.

**Betriebsprofil**

Call 1: 7.97s. Call 2: 4.71s. MCP-Latenz: 0.45s. Total: 78.76s.  
Kosten pro Run: 0.076749.  
Für die gezeigte Leistung: langsam und teuer.

**Fazit & Empfehlung**

Geeignet für überwachte Pipelines mit enger Tool-Governance, klaren Fetch-Pfaden und harter Antwortvalidierung nach dem Modell. Nicht geeignet für autonome Rechercheketten, Compliance-nahe Web-Recherche oder mehrsprachige Such- und Syntheseaufgaben, bei denen das Modell selbst das passende Tool wählen und Ergebnisse belastbar verdichten muss. Wenn Sie GPT-5.4 einsetzen, dann als assistierten Ausführer innerhalb eines stark abgesicherten Orchestrators, nicht als eigenständig vertrauenswürdige Tool-Instanz.