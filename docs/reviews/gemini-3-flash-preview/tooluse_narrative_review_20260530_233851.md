**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:38:51


Bedingt deploy, weil die Tool-Ausführung verlässlich genug für produktive MCP-Pipelines ist, die Synthesetreue aber nicht stabil genug wirkt, um unbeaufsichtigt als letzte Wahrheitsschicht zu dienen. Mit validem Tool-Call, ohne Halluzinationsbefund und ohne Retry ist die Basis operativ tragfähig.

**Tool-Execution-Profil**

Gemini 3 Flash Preview arbeitet im MCP-Rahmen sauber. Die Calls sind valide, protokollkonform und brauchten keinen zweiten Anlauf wegen Format- oder Verständnisfehlern. Das ist für produktive Tool-Infrastruktur der wichtigste Grundvertrauenstest.

Bei der Werkzeugwahl zeigt das Modell brauchbare, aber keine ausgeprägt agentische Intelligenz. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es nur solide Sicherheit. Es erkennt den Bedarf nach Suche oft, aber nicht mit der Konsequenz, die dynamische Pipelines verlangen. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus vorhandenem Wissen misst, konstruiert es die Adresse brauchbar und führt fetch korrekt aus, aber nicht mit der Präzision eines deterministischen Retrieval-Modells. Das Profil wirkt deshalb nicht starr regelbasiert, aber auch nicht robust genug für komplexe Tool-Orchestrierung ohne Leitplanken.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mäßig. Die P2-Leistung bleibt mit 56.67 klar hinter der Tool-Ausführung zurück. Besonders sichtbar ist das bei Web Search & Tool Selection und Multilingual Search & Synthesis, wo Recherche gelingt, die Verdichtung aber an Selektionsschärfe und Priorisierung verliert. Für Pipelines, in denen das Modell Befunde nur weiterreicht oder knapp zusammenfasst, ist das akzeptabel. Für Compliance, Policy oder Executive Briefings ist es zu weich.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen geholt werden, bleibt das Modell im Ergebnisraum der Tools. Content-Verification-State A, kein Halluzinationssignal. Das ist das stärkste Vertrauenssignal dieses Laufs.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, erfindet Gemini 3 Flash Preview keinen Seiteninhalt. Es kommuniziert den Fehler sichtbar statt Ersatzfakten zu liefern. Das ist für Produktion akzeptabel. Die Synthese bleibt dabei eher knapp als diagnostisch tief, aber sie verletzt nicht die Tool-Wahrheit.

**Betriebsprofil**

1.61s erster Call, 1.25s MCP-Latenz, 6.95s zweiter Call, 58.85s total. Schnell im Einzelaufruf, aber der Gesamtrun ist nicht kurz. Kosten pro Run: $0.007878. Günstig für Full-Fleet-Betrieb, gemessen an der gezeigten Tool-Zuverlässigkeit.

**Fazit & Empfehlung**

Geeignet für kosten- und latenzsensible MCP-Pipelines, in denen das Modell Tools sicher ausführt, Fehler offenlegt und Ergebnisse knapp verdichtet. Nicht geeignet als autonome Endinstanz für hochwertige Synthese, mehrsprachige Rechercheverdichtung oder werkzeuggetriebene Entscheidungsunterlagen. Deploy mit Guardrails: strukturierte Output-Schemata, nachgelagerte Verifikation und enge Prompt-Führung bei Tool-Wahl.