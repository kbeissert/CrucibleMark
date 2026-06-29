**Deployment-Urteil**

> **Erstellt am:** 29.06.2026, 23:18:46


Bedingt deploy, weil das Modell stark in der Tool-Ausführung ist, aber die Synthesetreue für produktive Antwortschichten noch zu unzuverlässig bleibt. Der kombinierte Eindruck ist gut, aber ein invalider Tool-Call verhindert ein uneingeschränktes Vertrauensurteil für autonome MCP-Pipelines.

**Tool-Execution-Profil**

Ornith 1.0 35B zeigt echte Werkzeugintelligenz statt bloßem Musterfolgen. Beim Web Search & Tool Selection-Test erkennt es ohne expliziten Hinweis korrekt, dass erst gesucht und nicht direkt gefetcht werden muss. Das ist ein starkes Signal für dynamische Tool-Pipelines. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar, aber nicht präzise genug für deterministische Pipelines. Genau dort liegt die operative Grenze: gute Strategie, nicht immer saubere Endausführung.

P1 von 89.17 bestätigt das Bild. Das Modell plant Werkzeugnutzung gut und kommt in mehreren Assets zuverlässig zum passenden Tool. Problematisch bleibt, dass der Tool-Call insgesamt nicht durchgehend valide war. Da kein Retry erforderlich war, spricht das eher für einen punktuellen Protokoll- oder Argumentfehler als für ein grundlegendes Verständnisproblem. Für MCP-Orchestrierung ist das tolerierbar, aber nur mit strikter Call-Validierung und Guardrails auf Parameter- und URL-Ebene.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 von 60.00 ist der schwächste Teil des Profils. Das Modell kann Ergebnisse zusammenführen, aber die Verdichtung verliert oft Präzision oder Priorisierung. Besonders auffällig ist das bei EU License Research und Multilingual Search & Synthesis, wo die Ausführung stark war, die abschließende Zusammenfassung aber zu flach blieb. Für Retrieval- oder Search-lastige Workflows reicht das oft. Für Compliance, Policy oder Executive Briefing nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Allerdings ist P2=40 hier ein Warnhinweis: Es erfindet nichts, aber es verdichtet die beschafften Inhalte nicht robust genug für belastbare Freigabeentscheidungen.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation statt erfundenem Ersatzinhalt prüft, reagiert das Modell produktionsgerecht. Es halluziniert keinen Seiteninhalt trotz fehlgeschlagenem Tool-Aufruf. P2=80 ist hier ausreichend. Für reale Tool-Ketten ist das ein belastbares Signal: Bei Ausfällen bleibt die Infrastruktur vertrauenswürdig.

**Souveränitätsprofil**

Lokal betreibbar, kommerziell offen nutzbar und ohne Sovereignty Gap: n/a-Punkte unter dem Fleet-Ø von 66.75. Für eine local_sovereign-Gruppe ist das attraktiv, weil die Tool-Leistung fleet-kompetitiv bleibt, ohne Cloud-Abhängigkeit bei den Gewichten.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines mit Search, Fetch, Fehlerbehandlung und agentischer Vorstrukturierung. Nicht geeignet als ungeprüfte Endinstanz für Compliance-Antworten, mehrsprachige Ergebnisverdichtung oder präzise Summary-Layer mit Entscheidungscharakter. Empfehlung: als Tool-Orchestrator und Recherchearbeiter einsetzen, aber die finale Synthese entweder durch ein stärkeres Verdichtungsmodell absichern oder per schema-strikter Postvalidierung kontrollieren.