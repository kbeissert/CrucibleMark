**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:19:45


Bedingt deploy, weil die Tool-Ausführung stark ist, die Gesamtsynthese aber zu unzuverlässig bleibt und die Tool-Calls im Lauf nicht durchgängig valide waren. Für produktive MCP-Pipelines taugt es als ausführendes Modell eher als als vertrauenswürdige Endverdichtung.

**Tool-Execution-Profil**

Qwen 3.8 27B zeigt echte Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber. Das spricht gegen ein starres Muster und für situationsabhängige Tool-Wahl. Auch bei Multilingual Search & Synthesis und EU License Research greift es konsequent zu externen Quellen.

Schwächer ist die Präzision im nachgelagerten Ausführen. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar, aber nicht stabil genug für deterministische Pipelines. Der Wert ist ordentlich, nicht belastbar. Dass der Run insgesamt als tool_call_valid=false markiert ist, ist der wichtigste operative Vorbehalt: Das Modell plant richtig, produziert aber nicht durchgängig protokollsaubere oder vollständig valide Aufrufe. Für MCP-Orchestrierung heißt das: vor den Tools ein Validator, hinter den Tools ein Kontrollschritt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. Die P2-Leistung von 65.83 passt zum Aufgabenbild: HTTP Fetch & Extract und URL Construction & Fetch sind ordentlich, aber EU License Research fällt mit P2=20 deutlich ab. Das ist kein kleiner Ausreißer, sondern ein Warnsignal für Pipelines, in denen aus Webfunden belastbare Schlussfolgerungen oder Compliance-Aussagen gebaut werden sollen. Das Modell findet Quellen häufiger, als es sie sauber verdichtet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, halluziniert es zwar nicht offen. Trotzdem ist das Vertrauensurteil schwach, weil die Verdichtung fast kollabiert. Anders gesagt: Es erfindet nichts, aber es beweist auch nicht, dass es die Tool-Ergebnisse präzise in belastbare Aussagen übersetzt.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call misst, bleibt Qwen 3.8 27B auf der richtigen Seite der Sicherheitslinie. Es halluziniert keinen Seiteninhalt. Das ist produktionsrelevant positiv. Die Qualität der Fehlerkommunikation ist mit P2=40 jedoch nur begrenzt brauchbar. Das Modell ist also defensiv statt elegant: akzeptabel für Produktion, wenn der Orchestrator Fehlerzustände selbst klar behandelt.

**Betriebsprofil**

Call 1: 3.01s. MCP-Latenz: 2.93s. Call 2: 24.86s. Total: 184.85s.  
Für die gezeigte Leistung langsam. Kosten/Run: local. Finanziell günstig, zeitlich teuer.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche-, Search-Routing- und Vorverarbeitungs-Pipelines, in denen ein zweites System die Ergebnisse validiert, normalisiert oder final formuliert. Nicht geeignet als alleinige Endinstanz für Compliance, Lizenzbewertung, regulatorische Zusammenfassungen oder andere Tool-Pipelines, bei denen die Synthese selbst das Produkt ist. Wer ihm eine Tool-Infrastruktur übergibt, sollte es als guten Beschaffer und ordentlichen Ausführer einsetzen, nicht als letzte vertrauensstiftende Stimme.