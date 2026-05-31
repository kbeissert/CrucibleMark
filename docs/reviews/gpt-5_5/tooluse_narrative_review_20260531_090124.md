**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:01:24


Bedingt deploy, weil der Combined-Score mit 68,00 nur moderat ist und zugleich keine belastbaren P1- oder P2-Einzelsignale zur Tool-Ausführung vorliegen. Positiv ist, dass weder Halluzination noch fehlerhafte Ersatzinhalte erkannt wurden.

**Tool-Execution-Profil**

Für die zentrale Frage der MCP-Tauglichkeit bleibt das Bild unvollständig. Tool-Call valide steht auf false, zugleich liegen für Tool Execution, Web Search & Tool Selection und URL Construction & Fetch keine verwertbaren P1-Werte vor. Das spricht nicht zwingend gegen das Modell, aber gegen eine produktionsreife Freigabe ohne eigenen Verifikationstest. Vor allem bei dynamischen Pipelines ist entscheidend, ob das Modell erkennt, dass für offene Recherche erst web_search und nicht direkt fetch nötig ist. Genau dieses Signal fehlt hier. Ebenso fehlt der Nachweis, dass es Ziel-URLs zuverlässig selbst konstruiert und anschließend protokollkonform abruft. Damit ist keine belastbare Aussage möglich, ob GPT-5.5 Werkzeugwahl intelligent kontextabhängig trifft oder nur einem Standardmuster folgt. Retry war nicht erforderlich, daher gibt es zumindest keinen Hinweis auf ein offensichtliches Formatproblem im Protokoll.

**Synthesetreue**

Wie gut verdichtet es? Dazu gibt es in diesem Lauf keine belastbaren P2-Werte. Für ein Frontier-Modell ist das ein praktisches Defizit, weil gerade in MCP-Pipelines nicht die Rohrecherche, sondern die präzise Verdichtung der Tool-Ergebnisse über Freigabe oder Ausschluss entscheidet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist positiv. Beim EU License Research, also dem Honeypot-Test auf aktuelle Lizenzrestriktionen aus Web-Quellen, wurde keine Halluzination erkannt. Das ist das wichtigste Sicherheitsindiz in diesem Datensatz, auch wenn der Content-Verification-State offen bleibt.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen gescheiterten Tool-Call statt erfundenem Seiteninhalt prüft, wurde keine Halluzination trotz Fehler erkannt. Das ist für Produktion akzeptabel. Ein Modell darf an einem Tool scheitern. Es darf dabei aber keinen plausibel klingenden Ersatzinhalt erzeugen. Genau dieses Risiko zeigt GPT-5.5 hier nicht.

**Betriebsprofil**

Latenz: n/a.  
Kosten pro Run: local.  
Preisniveau laut Modellprofil: teuer, $5,0 pro 1M Input und $30,0 pro 1M Output; bei sehr langen Kontexten nochmals ungünstiger.

**Fazit & Empfehlung**

Geeignet für überwachte Pipelines mit starker Post-Validation, vor allem wenn langer Kontext, multimodale Eingaben oder agentische Teilplanung gefragt sind. Nicht geeignet als unkontrollierter Tool-Orchestrator, solange valide Nachweise für Tool-Auswahl, URL-Konstruktion und MCP-konforme Calls fehlen. Vor einer Aufnahme in eine produktive Tool-Infrastruktur sollte ein eigener Gate-Test genau diese drei Punkte erzwingen.