**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:02:01


Bedingt deploy, weil die Tool-Ausführung stark ist, die Gesamtnote mit 73.54 im produktiven Bereich liegt, aber die Tool-Calls nicht durchgehend valide waren und die Synthesequalität mit P2 60.00 zu oft hinter der Beschaffung zurückbleibt.

**Tool-Execution-Profil**

Ornith 1.0 35B (FP8) zeigt echte Werkzeugintelligenz. Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es P1 95. Das spricht gegen ein starres Muster und für brauchbare Situationsdiagnose. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, fällt es auf P1 80 zurück. Das ist noch produktionsfähig, aber nicht präzise genug für Pipelines, in denen URLs deterministisch konstruiert werden müssen.

Über die sechs Aufgaben hinweg ist das Ausführungsprofil insgesamt robust. EU License Research und Multilingual Search & Synthesis liegen bei P1 100. HTTP Fetch & Extract sowie Tool Failure Handling (404) liegen jeweils bei P1 80. Kritisch bleibt der Meta-Befund: Tool-Call valide ist false. Das bedeutet nicht, dass das Modell Tool-Nutzung grundsätzlich nicht beherrscht, aber dass die Protokolltreue nicht sauber genug ist, um ohne Guardrails direkt an eine MCP-Infrastruktur gehängt zu werden.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich, nicht verlässlich stark. P2 60.00 ist das klare Warnsignal dieses Laufs. Besonders schwach ist EU License Research mit P2 20, obwohl die Beschaffung selbst gelang. Das Muster ist konsistent: Ornith findet Quellen oft besser, als es sie anschließend verdichtet. Für produktive Agenten heißt das, dass die Retrieval-Schicht brauchbar ist, die Antwortschicht aber eng geführt oder nachvalidiert werden muss.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diese Disziplin prüft, wurde keine Halluzination erkannt. Das ist wichtig. Das Modell hat also nicht frei erfunden, sondern eher schlecht zusammengezogen. Vertrauensbruch liegt hier nicht vor, aber Verarbeitungsverlust sehr wohl.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, reagiert Ornith akzeptabel. P2 80 und keine Halluzination trotz Fehler zeigen, dass es Fehlschläge offen behandelt statt Seiteninhalt zu erfinden. Für Produktion ist das die Mindestanforderung, und die erfüllt es.

**Betriebsprofil**

Call 1: 5.02s. MCP-Latenz: 0.98s. Call 2: 41.08s. Total: 282.54s. Langsam. Kosten/Run: local. Günstig im Betrieb, aber die Laufzeit ist im Verhältnis zur nur guten Gesamtleistung hoch.

**Fazit & Empfehlung**

Geeignet für lokale, agentische Recherche- und Tooling-Pipelines, in denen Beschaffung, Suche und Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Sinnvoll für Entwickler-Workflows, interne Wissenssuche und mehrstufige Tool-Orchestrierung mit nachgelagerter Prüfung. Nicht die richtige Wahl für Compliance-, Policy- oder Executive-Summary-Pipelines, in denen die letzte Antwort ohne menschliche oder regelbasierte Kontrolle direkt weiterverwendet wird. Deploy nur mit strikter Tool-Call-Validierung, Output-Scoring und einer zweiten Instanz für die finale Synthese.