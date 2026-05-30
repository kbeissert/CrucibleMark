**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:43:59


Bedingt deploy, weil GLM-5 Turbo valide Tool-Calls erzeugt und nicht halluziniert, aber die Synthesetreue mit Combined 78.67 nur dann ausreicht, wenn nachgelagerte Validierung die inhaltliche Verdichtung absichert.

**Tool-Execution-Profil**

Im Tool-Use ist das Modell belastbar. P1 90 zeigt, dass es MCP-konform arbeitet, valide Calls erzeugt und keinen Retry brauchte. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den richtigen Werkzeugtyp sicher und erreicht P1 100. Das spricht gegen ein starres Muster und für echte Werkzeugwahl im Kontext.

Weniger präzise ist es beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL eigenständig ableitet und dann korrekt per Fetch abruft. Mit P1 80 ist das brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen direkt produktive URLs generieren sollen. Für dynamische Recherchepfade ist das akzeptabel. Für streng kontrollierte Fetch-Ketten sollte die URL-Bildung extern vorgegeben werden.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht verlässlich präzise genug für sensible Ausgabeschichten. P2 70 wird durch starke Fehlerkommunikation gestützt, aber die Einzelergebnisse zeigen klare Schwankung: HTTP Fetch & Extract liegt bei 60, Multilingual Search & Synthesis ebenfalls bei 60. Das Modell holt Informationen also oft korrekt ein, verdichtet sie danach aber nur mittelstabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Grundsätzlich ja, mit einem wichtigen Vorbehalt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert es nicht und bleibt damit vertrauenswürdig im Sicherheitskern. Dass P2 dort nur 40 beträgt, ist kein Halluzinationsproblem, sondern ein Verdichtungsproblem: Es nutzt die Quelle, transportiert sie aber nicht sauber genug in die Antwort.

**Fehlerresilienz**

Gut für Produktion. Im Test Tool Failure Handling (404), der misst, ob das Modell bei einem scheiternden Tool-Call transparent bleibt statt Seiteninhalt zu erfinden, erreicht es P2 100. Es kommuniziert Fehler offen und produziert keinen Ersatzinhalt. Genau dieses Verhalten ist in Tool-Pipelines akzeptabel.

**Betriebsprofil**

Call 1: 2.92s. Call 2: 25.56s. MCP-Latenz: 0.80s. Total: 175.71s.  
Kosten pro Run: $0.015480.  
Kosten: günstig. Latenz: stark schwankend und im Gesamtlauf lang im Verhältnis zur nur guten Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell recherchiert, passende Tools auswählt und bei Fehlern transparent bleibt. Gut passend für Such-, Routing- und operator-assistierte Workflows. Nicht die erste Wahl für Compliance-, Regulatorik- oder Executive-Summary-Pipelines, in denen die Antwort selbst bereits die endgültige, präzise Verdichtung sein muss. Wenn Sie GLM-5 Turbo einsetzen, dann als tool-fähigen Beschaffer von Informationen, nicht als letzte Instanz für inhaltliche Verdichtung.