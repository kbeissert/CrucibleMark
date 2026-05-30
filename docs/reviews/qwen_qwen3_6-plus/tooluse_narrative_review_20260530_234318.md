**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:43:18


Nicht deploy. Die Basis für einen Produktionseinsatz fehlt, weil bei Combined 0.00 weder valide Tool-Calls noch belastbare Ausführungs- und Synthesedaten vorliegen.

**Tool-Execution-Profil**

Für qwen3.6-plus gibt es in diesem Lauf keine verwertbare Evidenz, dass es MCP-konforme Tool-Aufrufe zuverlässig erzeugt. Das wichtigste Signal ist hier nicht ein schlechter P1-Wert, sondern das Fehlen eines validen Tool-Calls bei gleichzeitig n/a über alle Tool-Assets. Damit lässt sich weder bestätigen, dass das Modell zwischen Web Search & Tool Selection, also der Wahl zwischen Suche und direktem Abruf, intelligent unterscheidet, noch dass es beim URL Construction & Fetch die Ziel-URL präzise genug konstruiert und anschließend korrekt abruft. Produktionstechnisch ist das ein Blocker. Ein Generalist in der Frontier-Klasse muss Tool-Nutzung nicht nur sprachlich andeuten, sondern formal korrekt ausführen. Da retry_required=false ist, sieht das nicht nach einem einmaligen Formatfehler mit erfolgreicher Korrektur aus, sondern nach fehlender messbarer Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es hier keine belastbare Aussage. Sämtliche P2-Werte stehen auf n/a, einschließlich HTTP Fetch & Extract und Multilingual Search & Synthesis. Für Architekten heißt das: Die Fähigkeit, Tool-Output in präzise, knappe und überprüfbare Antworten zu überführen, ist in diesem Lauf nicht nachgewiesen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Vertrauensbefund ist vorsichtig positiv. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das ist wichtig. Es ist aber nur ein Negativsignal gegen offenkundige Erfindung, kein Positivbeleg für echte Tool-Bindung, weil auch hier keine inhaltliche Verifikation vorliegt.

**Fehlerresilienz**

Im 404-Test, der prüft, ob das Modell bei einem gescheiterten Tool-Aufruf transparent bleibt statt Ersatzinhalt zu erfinden, wurde keine Halluzination erkannt. Das ist für Produktion akzeptabel. Ein Modell, das bei Fehlern nicht improvisiert, schützt die Pipeline vor stillen Falschdaten. Mehr lässt sich aus n/a-Daten jedoch nicht ableiten: Transparenz bei Fehlern ist vorhanden, erfolgreiche Wiederaufnahme oder alternative Beschaffung ist nicht belegt.

**Betriebsprofil**

Latenz: n/a. Kosten/Run: local. Leistungsbezug: nicht bewertbar, weil keine belastbaren Ausführungsdaten vorliegen.

**Fazit & Empfehlung**

qwen3.6-plus ist in diesem Teststand kein Kandidat für MCP-gestützte Produktionspipelines, in denen das Modell selbständig Tools wählen, korrekt aufrufen und Ergebnisse verdichten muss. Ein Einsatz wäre allenfalls in streng überwachten Setups vertretbar, in denen ein externer Orchestrator die Tool-Schritte vollständig vorgibt und Antworten zusätzlich validiert. Für dynamische Recherche-, Compliance-, Retrieval- oder Web-Automation-Pipelines ist die Evidenz zu dünn. Vor einer Freigabe braucht das Modell einen vollständigen Re-Run mit validierten Tool-Calls und verifizierter Synthese.