**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:22


Bedingt deploy, weil GPT-5.4 zwar keine Halluzination im Benchmark zeigte, aber keine durchgängig validen Tool-Calls produziert und mit Combined 51.96 zu unsicher für autonome MCP-Pipelines bleibt.

**Tool-Execution-Profil**

Das Tool-Profil ist inkonsistent. Beim Test Web Search & Tool Selection, der prüft, ob das Modell ohne Hinweis erkennt, dass statt fetch eine Suche nötig ist, fällt es deutlich ab. Das spricht gegen belastbare Werkzeugwahl in offenen Situationen. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Weltwissen misst, arbeitet es dagegen solide und kann bekannte Pfade korrekt ansteuern. Das Muster wirkt deshalb nicht wie echte Tool-Intelligenz, sondern wie gute Ausführung, sobald der Zugriffsweg schon implizit feststeht.

Für produktive MCP-Orchestrierung ist das der zentrale Vorbehalt. GPT-5.4 kann Tools bedienen, aber nicht zuverlässig entscheiden, welches Tool zuerst nötig ist. Da ein Retry erforderlich war und der Tool-Call nicht valide blieb, ist das eher ein Protokoll- und Formatproblem mit operativer Wirkung als ein reines Wissensdefizit. In einer Pipeline heißt das: Wrapper, Validierung und erzwungene Tool-Routing-Regeln sind Pflicht.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 46.67 ist für ein Frontier-Generalist-Modell zu schwach. Die guten Einzelwerte bei HTTP Fetch & Extract und Tool Failure Handling (404) zeigen, dass es saubere Tool-Ausgaben ordentlich zusammenfassen kann. Sobald Recherche, Suchauswahl oder mehrsprachige Zusammenführung dazukommen, bricht die Verdichtungsqualität sichtbar ein.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, endet ohne erkannte Halluzination, aber mit P2 20 und Content-Verification-State B2. Das ist kein Vertrauensbruch im harten Sinn, aber auch kein sauberes Grounding. Für Compliance-nahe oder regulatorische Workflows reicht das nicht.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt abgrenzt, reagiert GPT-5.4 akzeptabel. P2 80 und keine Halluzination trotz Fehler bedeuten: Wenn ein Tool scheitert, erfindet das Modell nicht einfach Seiteninhalt. Das ist produktionsfähig und einer der wichtigeren positiven Befunde dieses Laufs.

**Betriebsprofil**

Call 1: 7.97s. Call 2: 4.71s. MCP-Latenz: 0.45s. Total: 78.76s.  
Kosten pro Run: 0.076749.  
Für die gezeigte Leistung: langsam und teuer.

**Fazit & Empfehlung**

Geeignet für überwachte Pipelines mit festen Tool-Pfaden, Antwortvalidierung und klarer Fehlerbehandlung. Nicht geeignet für autonome Rechercheketten, dynamische Tool-Auswahl, mehrsprachige Discovery oder Compliance-nahe Synthese, bei denen das Modell selbst entscheiden muss, wann gesucht, wann gefetcht und wie streng an Tool-Befunden geblieben wird. Wenn GPT-5.4 eingesetzt wird, dann als nachgelagerter Verdichter auf bereits beschafften Daten, nicht als primärer MCP-Agent.