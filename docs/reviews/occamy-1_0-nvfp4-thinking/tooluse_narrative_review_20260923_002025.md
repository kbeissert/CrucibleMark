**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:20:25


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgehend valide sind und die Synthese bei einem Halluzinationsbefund nicht zuverlässig genug für unbeaufsichtigte Produktionspipelines bleibt.

**Tool-Execution-Profil**

Occamy zeigt klare Werkzeugintelligenz statt bloßem Schema-F. Beim Web Search & Tool Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung konsistent. Das spricht für brauchbare Planungslogik in MCP-gestützten Abläufen. Auch EU License Research läuft auf P1-Seite sauber, was wichtig ist, weil das Modell dort aktiv aktuelle Web-Quellen einholen muss.

Schwächer wird es bei Präzisionsarbeit nach der Entscheidung. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen und den anschließenden Fetch prüft, ist die Ausführung nur ordentlich, nicht deterministisch. Genau dort liegt das Produktionsrisiko: Das Modell weiß oft, welches Tool gebraucht wird, aber der konkrete Call ist nicht stabil genug. Der Befund „Tool-Call valide: false“ ist deshalb schwerer als der gute P1-Gesamteindruck. Immerhin war kein Retry nötig. Das wirkt eher wie ein Ausführungs- und Präzisionsproblem als wie ein Protokollverständnisfehler.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist mit 42.50 der klare Schwachpunkt. Besonders auffällig ist Multilingual Search & Synthesis: Das Modell findet Informationen über Sprachgrenzen hinweg, verdichtet sie aber unpräzise und verliert Relevanz. Auch bei URL Construction & Fetch bricht die Qualität in der Zusammenführung der abgerufenen Inhalte deutlich ein. Für Pipelines, die exakte Extraktion, Compliance-Zitate oder verlässliche Ergebnisverdichtung brauchen, ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es formal im sicheren Bereich: keine Halluzination, also kein Ausweichen auf altes Trainingswissen trotz aktueller Lizenzfrage. Das ist der wichtigste Vertrauensanker. Der globale Halluzinationsbefund bleibt trotzdem ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgeben kann, beschädigt es das Vertrauen in die gesamte Tool-Infrastruktur.

**Fehlerresilienz**

Bei Tool Failure Handling (404), das transparente Reaktion auf einen fehlgeschlagenen Abruf prüft, verhält sich Occamy produktionsgerecht. Es halluziniert keinen Seiteninhalt und kommuniziert den Fehlschlag nachvollziehbar. Genau dieses Verhalten ist in robusten Pipelines akzeptabel, weil der Orchestrator dann sauber eskalieren oder neu planen kann.

**Souveränitätsprofil**

Lokal betreibbar, open-weight und damit für souveräne Deployments attraktiv. Combined 70.00, also 1.83 Punkte über dem Fleet-Ø von 68.17. Die Kompetenz ist damit fleet-tauglich, aber nicht ohne Guardrails.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Agenten-Pipelines mit starker externer Validierung, klaren Tool-Schemas und nachgelagerter Ergebnisprüfung. Gut einsetzbar für Recherche-Orchestrierung, Such- und Fetch-Ketten sowie fehlertolerante Assistenzabläufe. Nicht geeignet für High-Trust-Pipelines ohne menschliche oder programmatische Kontrolle, insbesondere bei Compliance, mehrsprachiger Verdichtung und allen Workflows, in denen die Synthese selbst als verlässliches Endprodukt gelten muss.