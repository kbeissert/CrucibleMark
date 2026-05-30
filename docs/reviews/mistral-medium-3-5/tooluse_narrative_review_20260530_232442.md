**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:42


Bedingt deploy, weil die Tool-Ausführung stark ist und die Calls valide sind, aber die erkannte Halluzination bei nur mittelmäßiger Synthesetreue das Vertrauen in unbeaufsichtigte Endausgaben begrenzt.

**Tool-Execution-Profil**

Mistral Medium 3.5 arbeitet auf der Ausführungsebene belastbar. P1 von 89.17 ist für eine MCP-gestützte Pipeline ein klares Signal, dass das Modell Tools tatsächlich benutzt statt sie nur sprachlich zu simulieren. Der Befund „Tool-Call valide: true“ spricht für Protokolltreue und gegen strukturelle Probleme im Call-Format.

Bei der Werkzeugwahl bleibt das Bild jedoch unvollständig, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelwerte vorliegen. Daher lässt sich nicht sauber belegen, ob das Modell zwischen Suche und direktem Fetch intelligent unterscheidet oder vor allem einem stabilen Standardmuster folgt. Der Retry-Bedarf wirkt in diesem Kontext eher wie ein Orchestrierungs- oder Formatproblem als wie ein prinzipielles Missverständnis der Aufgabe. Ein Modell mit echtem Tool-Unverständnis erreicht in der Regel nicht gleichzeitig valide Calls und ein so hohes P1-Niveau.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 von 55.00 zeigt, dass die zweite Hälfte der Arbeit, also Extraktion, Verdichtung und saubere Rückführung der Tool-Ergebnisse in eine präzise Antwort, deutlich hinter der Ausführung zurückbleibt. Für produktive Pipelines ist das relevant, weil nicht der Call selbst, sondern die textliche Rückgabe an Nutzer oder Folgekomponenten den Schaden verursacht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, hat das Modell nicht halluziniert. Das ist ein gutes Vertrauenssignal. Der globale Halluzinationsfund bleibt trotzdem ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als angebliche Tool-Ergebnisse ausgibt, untergräbt es die Verlässlichkeit der gesamten Tool-Infrastruktur.

**Fehlerresilienz**

Im 404-Test, der transparentes Fehlermanagement statt erfundenen Ersatzinhalt prüft, hat Mistral Medium 3.5 keinen Seiteninhalt halluziniert. Das ist für Produktion akzeptabel. Es zeigt, dass das Modell bei eindeutigem Tool-Scheitern nicht reflexhaft Lücken mit plausibel klingendem Text füllt.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Gleichzeitig liegt es mit einem Sovereignty Gap von -5.32 Punkten 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist konkurrenzfähig, aber nicht führend.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen Tool-Nutzung, lokale Betreibbarkeit und transparente Fehlerkommunikation wichtiger sind als perfekte Endverdichtung. Gut einsetzbar als Recherche- und Ausführungsmodell mit nachgelagerter Validierung oder einem strengeren Response-Guardrail. Nicht die erste Wahl für Compliance-, Policy- oder Executive-Summary-Pipelines, in denen jede synthetisierte Aussage unmittelbar belastbar sein muss.