**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:13:54


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination erkannt wurde, die Synthesetreue aber zu ungleich für belastbare Compliance- oder Recherchepipelines ausfällt.

**Tool-Execution-Profil**

Kimi K2 Thinking wählt Werkzeuge überwiegend intelligent statt rein schematisch. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber und erreicht volle Tool-Execution. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Modellwissen und den anschließenden fetch misst, bleibt es brauchbar, aber nicht deterministisch präzise. Das spricht für echte Werkzeugwahl, aber nicht für fehlerfreie Vorhersagbarkeit in starren Pipelines.

Die Calls waren valide und MCP-konform. Das ist der zentrale Produktionsindikator. Dass ein Retry erforderlich war, wirkt hier eher wie ein Ablauf- oder Formatproblem in einer längeren Thinking-Sequenz als wie ein grundlegendes Verständnisproblem. Für agentische Orchestrierung ist das tolerierbar, für eng getaktete Low-Latency-Pipelines weniger.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. HTTP Fetch & Extract zeigt, dass das Modell strukturierte Inhalte sehr gut in eine präzise Antwort überführen kann. Dagegen fallen EU License Research und Multilingual Search & Synthesis in der Verdichtung deutlich ab. Das Muster ist klar: Wenn die Quelle klar und eng geführt ist, arbeitet Kimi sauber. Wenn mehrere Quellen, Sprachwechsel oder regulatorische Einordnung zusammenkommen, sinkt die Zuverlässigkeit der Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, halluziniert es nicht. Das ist der wichtigere Befund als der schwache P2-Wert. Der Content-Verification-State B2 und P2=40 zeigen aber, dass es die Quelle nicht mit genug Strenge in eine belastbare Schlussfassung überführt. Es bleibt also tendenziell im Tool-Ergebnis, verwertet es aber nicht immer präzise genug.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call statt erfundenem Seiteninhalt prüft, verhält sich das Modell produktionsgerecht. Es halluziniert trotz Fehler keinen Ersatzinhalt. P2=80 ist hier ausreichend. Transparente Fehlerkommunikation ist für produktive Tool-Pipelines akzeptabel.

**Betriebsprofil**

Total 157.28s: langsam. MCP-Latenz 1.60s, aber ein zweiter Modell-Call mit 20.05s und lange Gesamtlaufzeit. Kosten pro Run 0.005985 USD: günstig bis moderat für Frontier-Niveau. Preis passt, Latenz ist der eigentliche operative Nachteil.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit Tool-Auswahl, Web-Recherche und transparentem Fehlermanagement, besonders wenn Kosten wichtiger sind als Antwortzeit. Nicht die erste Wahl für Compliance, Lizenzprüfung, mehrsprachige Evidenzsynthese oder andere Pfade, in denen die Zusammenfassung selbst revisionsfähig sein muss. Deploy nur mit Source-Grounding, Antwortvalidierung und enger Ausgabeprüfung nach dem letzten Tool-Schritt.