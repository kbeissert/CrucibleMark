**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:48:45


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination erkannt wurde, die Synthesetreue aber für produktive Wissensverdichtung zu schwankend bleibt.

**Tool-Execution-Profil**

Grok 4 Fast (Non-Reasoning) kann man eine MCP-Toolkette grundsätzlich anvertrauen. Die Calls waren valide, protokollkonform und ohne Retry lauffähig. Das ist die wichtigste Eintrittsbedingung für Produktion, und die erfüllt das Modell.

Bei der Werkzeugwahl zeigt es echte Situationsanpassung statt reiner Schablonenbefolgung. Im Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis statt fetch ein Suchtool gewählt wird, traf es die Entscheidung sauber. Das spricht für belastbare Tool-Intelligenz in offenen Pipelines. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es etwas weniger präzise. Die Ausführung ist brauchbar, aber nicht deterministisch genug für fragile Pfade mit strikt erwarteten Zieladressen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist der klare Engpass dieses Modells. Solide Werte in Tool Failure Handling (404), Web Search & Tool Selection und URL Construction & Fetch zeigen, dass es einfache bis mittlere Tool-Ergebnisse sauber zusammenführen kann. Problematisch sind EU License Research und vor allem Multilingual Search & Synthesis. Dort verliert es Verdichtungsschärfe, lässt wichtige Einschränkungen liegen oder verallgemeinert zu grob. Für reine Retrieval-Antworten reicht das oft. Für Compliance, Policy oder mehrsprachige Research-Synthesen nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja, und das ist der entscheidende Vertrauenspunkt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das Modell ist also nicht erfinderisch, aber gelegentlich zu grob in der Auswertung. Das ist ein Qualitätsproblem, kein Vertrauensbruch.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, kommunizierte das Modell den Fehler, statt Seiteninhalt zu erfinden. Genau dieses Verhalten braucht eine robuste Pipeline: sichtbarer Ausfall statt stiller Fiktion.

**Betriebsprofil**

Calls: 2.00s und 1.99s. MCP-Latenz: 1.12s. Total: 30.67s. Schnell im Modellaufruf, aber der End-to-End-Run ist nicht kurz. Kosten pro Run: 0.018736. Günstig bis moderat für Frontier-Einsatz, gemessen an der Leistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klaren Tool-Grenzen, Web-Recherche, operativer Assistenz und fehlertoleranten Retrieval-Workflows, in denen der Primärwert aus korrekter Tool-Nutzung kommt. Nicht die richtige Wahl für Pipelines, die aus mehreren Quellen präzise, mehrsprachige oder compliance-nahe Synthesen erzeugen müssen. Wenn Sie deployen, dann mit enger Ausgabevalidierung, Source-Grounding und vorzugsweise einem nachgelagerten Prüfschritt für Schlussfassung und Verdichtung.