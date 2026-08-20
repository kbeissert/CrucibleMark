**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:23:00


Bedingt deploy, weil die Tool-Nutzung meist stark ist, aber die Tool-Calls nicht durchgängig valide sind und die Synthesetreue für produktionskritische Pipelines zu oft nachlässt. Das Gesamtbild ist gut, aber nicht vertrauensstabil genug für unbeaufsichtigte End-to-End-Orchestrierung.

**Tool-Execution-Profil**

Gemini 3.5 Flash zeigt echte Werkzeugwahl-Kompetenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erkennt das Modell die passende Strategie sicher. Das spricht für brauchbare Orchestrierungslogik in dynamischen MCP-Setups.

Schwächer ist die Ausführungsschicht. Beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL und den anschließenden Fetch misst, arbeitet es brauchbar, aber nicht präzise genug für deterministische Pipelines. Dazu passt, dass der Tool-Call global nicht durchgängig valide war. Das ist kein Totalausfall, aber ein Integrationsrisiko: Das Modell plant oft richtig, produziert die Ausführung dann jedoch nicht immer protokollsicher.

**Synthesetreue**

Wie gut verdichtet es? Nur mittel. Die P2-Leistung zeigt, dass Gemini 3.5 Flash Tool-Ergebnisse oft korrekt zusammenzieht, aber bei verdichteter Ausgabe wichtige Präzision verliert. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo die Recherche gelingt, die abschließende Verdichtung aber zu grob bleibt. Für operative Assistenten ist das akzeptabel. Für Compliance-, Policy- oder Decision-Support-Flows ist es zu unscharf.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb das Modell formal auf der sicheren Seite. Es halluziniert nicht. Das ist der entscheidende Vertrauensanker. Gleichzeitig ist das schwache Syntheseergebnis ein Warnsignal: kein Sicherheitsbruch, aber zu wenig belastbare Verdichtung für regulatorische Aussagen.

**Fehlerresilienz**

Beim 404-Test, der misst, ob ein gescheiterter Tool-Aufruf transparent behandelt oder mit erfundenem Seiteninhalt überdeckt wird, reagiert Gemini 3.5 Flash akzeptabel. Es halluziniert trotz Fehler keinen Ersatzinhalt. Die Fehlerkommunikation ist damit produktionstauglich, auch wenn sie nicht besonders stark verdichtet oder proaktiv umsteuert.

**Betriebsprofil**

Total 46.06s pro Run. Einzelaufrufe 1.31s und 5.25s. MCP-Latenz 1.12s. Schnell in Einzelschritten, aber lang im Gesamtlauf. Preis: $1.5/1M Input, $9.0/1M Output. Für ein Frontier-Modell nicht billig. Gemessen an der Leistung nur dann vertretbar, wenn Tool-Auswahl wichtiger ist als hochpräzise Endsynthese.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit menschlicher Abnahme, für Recherche-Orchestrierung, Routing, mehrstufige Web-Nutzung und robuste Fehlerbehandlung ohne Halluzinationsrisiko. Nicht die erste Wahl für unbeaufsichtigte Compliance-Workflows, Lizenzbewertungen, mehrsprachige Executive Summaries oder andere Ketten, in denen die Endverdichtung als belastbare Arbeitsgrundlage dienen muss. Wenn Sie es einsetzen, dann mit strikter Output-Validierung nach dem Tool-Layer.