**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:01:17


Bedingt deploy, weil die Tool-Ausführung oft stark ist, aber invalide Tool-Calls, Retry-Bedarf und erkannte Halluzination das Vertrauen für unbeaufsichtigte Produktionspipelines brechen.

**Tool-Execution-Profil**

Qwen 2.5 Coder 7B zeigt echte Werkzeugorientierung, nicht nur starres Fetch-Muster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, wählt es das passende Tool sicher. Das spricht für funktionale Tool-Intelligenz. Beim URL-Construction-Test, der korrekte URL-Ableitung und anschließenden Abruf misst, arbeitet es brauchbar, aber nicht präzise genug für deterministische Pipelines. Der Abfall von perfekter Tool-Wahl zu nur solider URL-Ausführung zeigt: Die strategische Entscheidung sitzt besser als die operative Protokolltreue.

Kritisch ist der globale Befund, dass der Tool-Call nicht durchgehend valide war und ein Retry nötig wurde. Das wirkt hier eher wie ein Ausführungs- und Formatproblem im MCP-Ablauf als wie ein fehlendes Verständnis, denn die richtigen Werkzeuge werden meist erkannt. Für produktive Tool-Ketten heißt das: starke Kandidatur als assistierendes Modell, schwächer als autonomer Tool-Operator.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung ist der eigentliche Engpass dieses Modells. In HTTP Fetch & Extract, wo präzise Extraktion aus realem Seiteninhalt gefragt ist, und in Multilingual Search & Synthesis verliert es zu viel Genauigkeit. Das Modell kann Ergebnisse holen, verdichtet sie aber oft nicht belastbar genug für nachgelagerte Systeme. Für eine MCP-Pipeline ist das problematisch, weil nicht der Tool-Call, sondern die verbale Zusammenführung die Übergabe an Menschen oder weitere Komponenten verfälscht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, bleibt es im Ergebnisraum und halluziniert nicht. Das ist ein gutes Vertrauenssignal. Trotzdem gilt der Gesamtbefund Halluzination erkannt als Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird nicht nur eine Antwort schwach, sondern die Verlässlichkeit der gesamten Tool-Infrastruktur untergraben.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit fehlschlagenden Tool-Aufrufen misst, erfindet das Modell keinen Ersatzinhalt. Das ist produktionsseitig der richtige Fehlerzustand. Die Transparenz ist aber nur teilweise ausgereift, daher kein starkes Resilienzurteil. Akzeptabel mit Guardrails, nicht robust aus sich selbst heraus.

**Souveränitätsprofil**

Voll lokal betreibbar und operativ attraktiv für souveräne Deployments. Gleichzeitig liegt das Modell 0.75 Punkte unter dem Fleet-Ø von 66.55. Der Abstand ist klein. Die Souveränität kostet hier also kaum Gesamtleistung, wohl aber Zuverlässigkeit in der letzten Meile der Tool-Nutzung.

**Fazit & Empfehlung**

Geeignet für lokale, kostenarme Coding- und Retrieval-Pipelines mit menschlicher Abnahme, klaren Schemas und erzwungener Tool-Validierung. Nicht geeignet für unbeaufsichtigte Compliance-, Research- oder Agentenketten, in denen die sprachliche Verdichtung selbst als verlässliches Arbeitsergebnis gelten muss. Wenn Sie es einsetzen, dann als lokalen Tool-Benutzer mit striktem Retry-Wrapper, strukturierter Ausgabeprüfung und einer zweiten Instanz für Verifikation der Synthese.