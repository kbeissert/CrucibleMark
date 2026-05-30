**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:51


Nicht deploy für MCP-gestützte Tool-Pipelines, weil der kombinierte Befund schwach ist, der Tool-Call nicht valide war und ein Retry nötig wurde.

**Tool-Execution-Profil**

Llama 4 Scout 17B zeigt kein belastbares Tool-Verhalten. P1 bleibt über alle sechs Assets bei 35 und damit auf einem flachen Niveau. Das spricht nicht für adaptive Werkzeugwahl, sondern eher für ein starres oder formatunsicheres Muster. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erkennt das Modell den Werkzeugtyp nicht robust genug. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus eigenem Wissen und den anschließenden Abruf misst, erreicht es denselben Wert. Das ist kein Zeichen selektiver Stärke, sondern gleichförmiger Mittelmäßigkeit.

Wichtiger als der absolute Score ist hier das Protokollsignal: Der Tool-Call war nicht valide und ein Retry war erforderlich. In diesem Profil wirkt das eher wie ein Format- und Ausführungsproblem als ein reines Verständnisproblem. Für produktive MCP-Pipelines ist das kritisch, weil Orchestratoren auf deterministische, schema-konforme Aufrufe angewiesen sind.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Außerhalb des Honeypots ist die Verdichtung brauchbar, aber nicht präzise. In HTTP Fetch & Extract, Web Search & Tool Selection, URL Construction & Fetch und Multilingual Search & Synthesis liegt P2 jeweils bei 40. Das reicht für einfache Zusammenfassungen und das Zusammenziehen von Web-Treffern, aber nicht für Pipelines, in denen Details aus Tool-Output verlustarm in strukturierte Entscheidungen überführt werden müssen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier fällt das Modell durch. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, liegt P2 bei 0. Zwar wurde keine Halluzination markiert, aber der Vertrauensbefund ist trotzdem negativ: Das Modell bleibt nicht verlässlich am beschafften Evidenzmaterial. Für Compliance-, Policy- und Research-Pipelines ist das ein Ausschlusskriterium.

**Fehlerresilienz**

Bei Tool Failure Handling (404), dem Test auf transparente Reaktion nach fehlgeschlagenem Abruf, verhält sich das Modell akzeptabel. P2 liegt bei 40, und es halluziniert keinen Seiteninhalt trotz 404-Fehler. Das ist produktionstauglicher als die Tool-Ausführung selbst: Es scheitert offen, statt Ersatzfakten zu erfinden.

**Souveränitätsprofil**

Lokal betreibbar in der Gruppe local_sovereign, aber nicht fleet-kompetitiv. Der Befund liegt 5.32 Punkte unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet allenfalls für lokale, kostenarme Assistenzpfade mit enger Guardrail-Schicht, in denen Tool-Aufrufe extern validiert, retried und Ergebnisse nachgeprüft werden. Nicht geeignet für autonome MCP-Pipelines, Compliance-Recherche, dynamische Tool-Auswahl oder Workflows, in denen das Modell Web-Evidenz sauber abrufen und treu verdichten muss. Der VL-Charakter relativiert das Text-only-Ergebnis etwas, ändert aber nichts am Produktionsurteil für sprachbasierte Tool-Infrastruktur.