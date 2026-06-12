**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:06:35


Bedingt deploy, weil Devstral 2 keine Halluzination im Benchmark gezeigt hat, aber keine durchgehend validen Tool-Calls liefert und mit 48.50 kombiniert klar unter der Schwelle für vertrauenswürdige Standard-Orchestrierung bleibt.

**Tool-Execution-Profil**

Das Kernproblem liegt nicht im Willen zur Tool-Nutzung, sondern in der Zuverlässigkeit der Ausführung. P1 von 59.17 ist für ein Frontier-Modell mit agentischem Anspruch zu niedrig. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht das Modell nur 35. Das spricht gegen echte Werkzeugintelligenz und eher für ein starres Muster: Wenn eine URL bekannt oder ableitbar ist, funktioniert es oft. Wenn erst der richtige Werkzeugtyp erkannt werden muss, bricht die Qualität ein.

Das zeigt sich im Gegenstück deutlich. Beim URL-Construction-Test, der die korrekte Zieladresse aus Vorwissen ableiten und dann per fetch abrufen lässt, kommt Devstral 2 auf 80. Es kann also deterministische Tool-Pfade brauchbar bedienen. Dynamische Tool-Router wird es damit nicht stabil tragen. Dass der Tool-Call als nicht valide markiert ist und ein Retry nötig war, wirkt hier eher wie ein Protokoll- oder Formatproblem mit operativer Relevanz, nicht wie ein reines Verständnisdefizit. In MCP-Pipelines zählt genau das als Ausfallursache.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 von 40.00 ist der eigentliche Belastungspunkt dieses Runs. Besonders kritisch sind HTTP Fetch & Extract sowie Multilingual Search & Synthesis, beide mit P2 von 0. Das Modell ruft Inhalte nicht konsistent in belastbare, strukturtreue Antworten um. Für Pipelines, in denen aus Tool-Output präzise Fakten, Versionen oder Eigennamen extrahiert werden müssen, ist das zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja, und das ist der wichtigste positive Befund. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, halluziniert Devstral 2 nicht. Das Vertrauenssignal ist damit besser als die reine Verdichtungsqualität.

**Fehlerresilienz**

Solide. Im 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Aufruf misst, kommuniziert Devstral 2 den Fehler statt Seiteninhalt zu erfinden. P2 von 80 ist für Produktion akzeptabel. Ein Modell, das bei Fehlern stoppt und den Defekt offenlegt, lässt sich absichern. Ein Modell, das Ersatzinhalte erfindet, nicht.

**Betriebsprofil**

Total 57.71s pro Run. Einzelaufrufe 4.74s und 4.51s. MCP-Latenz 0.37s. Damit operativ langsam. Kosten pro Run 0.004757. Damit günstig. Preisniveau gut, Leistungsniveau dafür zu schwach.

**Fazit & Empfehlung**

Geeignet für coding-nahe Pipelines mit festen Tool-Pfaden, bekannten URLs und strikter nachgelagerter Validierung. Nicht geeignet als freier Tool-Entscheider in MCP-Umgebungen, nicht für Recherche-Workflows mit Suchschritt und nicht für Extraktionspipelines, in denen die Antwort die Tool-Ergebnisse präzise verdichten muss. Wenn Sie Devstral 2 einsetzen, dann hinter einem Router, der Tool-Wahl und Formatierung stark vorgibt.