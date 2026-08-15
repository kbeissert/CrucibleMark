**Deployment-Urteil**

> **Erstellt am:** 15.08.2026, 12:31:32


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Combined 71.50 und ungültigem Tool-Call-Signal nicht stabil genug für hochkritische Tool-Pipelines wirkt.

**Tool-Execution-Profil**

Grok 4.6 zeigt klare Kompetenz bei der Werkzeugwahl. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es P1 100. Das spricht gegen starres Musterverhalten und für brauchbare Werkzeugintelligenz in dynamischen Flows. Auch bei Multilingual Search & Synthesis und EU License Research ruft es die nötigen Quellen zuverlässig ab.

Schwächer ist die operative Präzision im letzten Schritt. Beim URL-Construction-Test, der die eigenständige Ableitung der Ziel-URL und den anschließenden Fetch misst, ist die Ausführung brauchbar, aber nicht deterministisch genug. P1 80 ist für Assistenz-Workflows akzeptabel, für feste Produktionsketten mit harten Erwartungen an Zieladressen jedoch knapp. Das globale Signal tool_call_valid=false verschärft diesen Punkt: Die Pipeline darf also nicht davon ausgehen, dass jeder Call protokoll- und parameterseitig sauber ankommt, auch wenn kein Retry nötig war. Das wirkt eher wie ein Validitäts- oder Formatproblem als wie fehlendes Tool-Verständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. P2 54 ist der eigentliche Schwachpunkt dieses Laufs. Stark ist die reine Extraktion aus HTTP Fetch & Extract mit P2 80. Deutlich schwächer ist die Verdichtung dort, wo mehrere Quellen, Einschränkungen oder abgeleitete Aussagen zusammengeführt werden müssen. EU License Research fällt mit P2 20 ab. URL Construction & Fetch bleibt mit P2 40 ebenfalls zu flach für präzise Abschlussantworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil besser als der P2-Wert vermuten lässt. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das Modell driftet also nicht offen in erfundene Aktualität ab. Das Vertrauen leidet hier eher an schwacher Verdichtung als an fabrizierten Fakten.

**Fehlerresilienz**

Akzeptabel für Produktion mit Guardrails. Im 404-Test, der Transparenz bei Tool-Fehlern statt halluziniertem Ersatzinhalt misst, erfindet Grok 4.6 keinen Seiteninhalt. P2 60 zeigt, dass die Kommunikation des Fehlers nicht besonders stark ist, aber sie bleibt ehrlich. Das ist operativ tragbar.

**Betriebsprofil**

Total 206.08s. Call 1 6.73s. Call 2 26.46s. MCP-Latenz 1.16s. Langsam für den erzielten Qualitätsmix. Preis: $2.0/1M Input, $6.0/1M Output. Frontier-typisch, nicht günstig.

**Fazit & Empfehlung**

Geeignet für recherchierende Assistenz-Pipelines, mehrsprachige Suchflüsse und agentische Vorstufen, in denen Tool-Nutzung wichtiger ist als die letzte verdichtete Antwort. Nicht geeignet als unbeaufsichtigter Endpunkt für Compliance-, Lizenz-, Policy- oder andere High-Trust-Pipelines, in denen die finale Synthese exakt aus den Tool-Ergebnissen abgeleitet werden muss. Wenn Sie es einsetzen, dann mit Response-Validator, URL-/Call-Schema-Prüfung und einer zweiten Instanz für Answer-Verification.