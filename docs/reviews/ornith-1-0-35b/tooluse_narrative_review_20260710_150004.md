**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:00:04


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgängig valide sind und die Synthesetreue mit Combined 73.83 nur für überwachte Pipelines trägt. Halluzination wurde nicht erkannt, das hält das Modell im produktiven Gespräch.

**Tool-Execution-Profil**

Ornith 1.0 35B zeigt echte Werkzeugintelligenz statt eines starren Fetch-Musters. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die Entscheidung sauber und erreicht P1 100. Das ist ein gutes Signal für MCP-gestützte Orchestrierung, in der der erste Schritt oft die eigentliche Fehlerquelle ist. Beim URL-Construction-Test, der die präzise Ableitung einer Ziel-URL aus Weltwissen misst, fällt es auf P1 80 zurück. Das spricht für brauchbare, aber nicht deterministische Ausführung, sobald das Modell selbst eine Adresse konstruieren muss. Kritisch bleibt der globale Befund tool_call_valid=false. Die Pipeline bekommt also ein Modell, das meist das richtige Werkzeug versteht, aber nicht bei jedem Aufruf protokollsauber liefert. Retry war nicht nötig, daher liegt das Problem eher in Call-Form oder Parametrierung als im Aufgabenverständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. P2 60 zeigt, dass Ornith Ergebnisse meist korrekt zusammenzieht, aber nicht verlässlich genug auf Detailtreue und Priorisierung achtet. Das sieht man auch an EU License Research mit P2 40 und Multilingual Search & Synthesis mit P2 40. Gerade dort verliert es Präzision bei Compliance-nahen und sprachübergreifenden Zusammenfassungen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Trotzdem ist P2 40 ein Warnhinweis: Es erfindet nichts, aber es verdichtet die beschafften Inhalte nicht belastbar genug für juristisch oder regulatorisch sensible Ketten.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem scheiternden Tool-Call prüft, reagiert Ornith produktionsgerecht. P2 80 bei gleichzeitig keiner Halluzination trotz Fehler zeigt, dass es Ausfälle offen kommuniziert statt Seiteninhalt zu erfinden. Das ist für robuste Tool-Pipelines akzeptabel und deutlich wichtiger als sprachliche Eleganz.

**Souveränitätsprofil**

Lokal betreibbar, kommerziell offen lizenziert und damit operativ attraktiv für souveräne Setups. Zugleich bleibt es fleet-kompetitiv: Der Sovereignty Gap liegt bei -0.75 Punkten unter dem Fleet-Ø von 66.55. Für ein lokal laufendes Workstation-MoE ist das ein starker Wert.

**Fazit & Empfehlung**

Geeignet für agentische Recherche-, Routing- und Retrieval-Pipelines mit Human-in-the-Loop oder nachgelagerter Validierung. Besonders sinnvoll ist es dort, wo lokaler Betrieb, offene Gewichte und robuste Fehlerkommunikation wichtiger sind als perfekte Verdichtung. Nicht geeignet ist es als unbeaufsichtigter Synthese-Endpunkt für Compliance, Recht, mehrsprachige Executive Summaries oder andere Workflows, in denen die Antwort die Tool-Ergebnisse präzise und vollständig repräsentieren muss.