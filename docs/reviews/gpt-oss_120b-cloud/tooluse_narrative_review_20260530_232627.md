**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:27


Bedingt deploy, weil die Tool-Ausführung tragfähig ist, die Verdichtung der Tool-Ergebnisse aber zu oft vom belastbaren Produktionsniveau abweicht. Der kombinierte Eindruck ist damit nur moderat, obwohl die Calls selbst valide sind.

**Tool-Execution-Profil**

Bei der Werkzeugnutzung arbeitet GPT OSS 120B Cloud kontrolliert und MCP-konform. Die Tool-Calls sind valide, ein Retry war nicht nötig. Das ist für eine Tool-Pipeline die erste Hürde, und die nimmt das Modell sauber.

Wichtiger ist die Werkzeugwahl selbst. Beim Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis search statt fetch gewählt wird, erkennt das Modell den richtigen Zugriffspfad sicher. Das spricht gegen starres Schema-Folgen und für echte Werkzeugintelligenz. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Weltwissen und den anschließenden Fetch prüft, bleibt es brauchbar, aber nicht deterministisch genug für fragilen Produktionsverkehr. Das Muster ist klar: Es entscheidet meist richtig, ist aber bei selbst konstruierten Zugriffspfaden weniger präzise als bei Such-gestützten Flows.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 liegt insgesamt deutlich unter dem Niveau, das man für belastbare Antwortschichten über Tools erwartet. Einzelne Aufgaben wie HTTP Fetch & Extract und URL Construction & Fetch gelingen noch ordentlich, aber EU License Research fällt bei der eigentlichen Verdichtung auf null zurück. Das ist kein Stilproblem, sondern ein Verlässlichkeitsproblem in der letzten Meile zwischen Tool-Output und Nutzerantwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil kritisch. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, verfehlt das Modell die inhaltliche Verifikation trotz fehlender formaler Halluzinationsmarkierung. Zusätzlich ist global eine Halluzination erkannt. In einer MCP-Pipeline ist das ein Sicherheitsrisiko: Sobald ein Modell erfundene oder nicht ausreichend belegte Fakten als Tool-basiert ausgibt, verliert die gesamte Infrastruktur ihren Nachweischarakter.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem gescheiterten Tool-Call misst, bleibt das Modell transparent und erfindet keinen Seiteninhalt. P2=20 zeigt, dass die Fehlerkommunikation nicht gut verdichtet ist, aber der entscheidende Punkt stimmt: kein halluzinierter Ersatzinhalt. Das ist für Produktion akzeptabel.

**Betriebsprofil**

Call 1: 3.37s. MCP-Latenz: 1.24s. Call 2: 7.52s. Total: 72.82s.  
Kosten pro Run: $0.002596.  
Aussage: günstig, aber für die gelieferte Synthesequalität zu langsam im End-to-End-Verhalten.

**Fazit & Empfehlung**

Geeignet für Pipelines, in denen das Modell primär Tools auswählt, Aufrufe ausführt und Rohresultate mit enger Nachkontrolle weiterreicht. Nicht geeignet als eigenverantwortliche Antwortschicht für Compliance, Lizenzprüfung, Web-Recherche mit Belegpflicht oder andere Flows, in denen die sprachliche Verdichtung selbst als vertrauenswürdiges Endprodukt gelten muss. Wenn Sie es einsetzen, dann mit strikter Ergebnisverifikation, Quellenausgabe und möglichst geringer Freiheit in der finalen Synthese.