**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:29


Bedingt deploy, weil GPT-4o valide Tool-Calls liefert und operativ steuerbar ist, aber die Synthesetreue mit Combined 66.83 nur moderat ausfällt und ein Halluzinationssignal für produktive Tool-Pipelines ein Sicherheitsrisiko bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke. Mit P1 86.67 wählt GPT-4o in der Regel das richtige Werkzeug und bleibt MCP-konform. Besonders relevant ist der Unterschied zwischen Web Search & Tool Selection und URL Construction & Fetch: Beim Test, der ohne expliziten Hinweis prüft, ob statt fetch eine Websuche nötig ist, erkennt das Modell den Werkzeugbedarf sauber und erreicht P1 100. Das spricht gegen starres Musterverhalten und für echte Tool-Selection-Kompetenz. Beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableitet und dann fetch ausführt, ist es brauchbar, aber nicht deterministisch genug für fragile Pipelines; P1 80 zeigt solide, nicht präzise Ausführung. Wichtig für den Betrieb: Tool-Call valide, Retry nicht erforderlich. Das ist ein Verständnis- und Protokollsignal, kein bloßes Formatglück.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 48.33 ist für produktive Pipelines der kritische Wert. GPT-4o holt Informationen meist korrekt herein, verdichtet sie danach aber oft zu grob oder verliert Präzision bei Extraktion und Mehrquellen-Synthese. Das sieht man besonders bei HTTP Fetch & Extract mit P2 35 und bei Multilingual Search & Synthesis mit P2 15. Für Workflows, in denen aus Tool-Output belastbare Endaussagen entstehen müssen, ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Trainingswissen kommen, bleibt GPT-4o formal im Tool-Pfad: Halluzination erkannt False, Content-Verification-State A. Das ist das wichtige Vertrauenssignal. Trotzdem steht global ein Halluzinationsflag im Lauf. Damit ist das Risiko nicht akademisch, sondern operativ: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich GPT-4o produktionsgerecht. Im 404-Test, der prüft, ob ein Fehlschlag transparent kommuniziert wird statt Seiteninhalt zu erfinden, erreicht es P2 80 und halluziniert keinen Ersatzinhalt. Das ist akzeptabel für Produktion, weil der Fehlerzustand sichtbar bleibt und Downstream-Systeme korrekt reagieren können.

**Betriebsprofil**

Total 23.68s. Modell-Calls 0.71s und 2.19s. MCP-Latenz 1.05s. Kosten/Run $0.032734. Schnell genug für interaktive Tool-Flows. Preislich günstig bis moderat. Für die gebotene Syntheseleistung nicht überragend effizient.

**Fazit & Empfehlung**

Geeignet für Pipelines, in denen Tool-Auswahl, Abruf und robuste Fehlerbehandlung wichtiger sind als die finale Verdichtung: Recherche-Orchestrierung, Voraggregation, Agenten mit menschlicher Abnahme, browser- oder suchgetriebene Workflows. Nicht die erste Wahl für Compliance, mehrsprachige Recherche-Synthese oder Extraktionsketten, in denen die Antwort direkt als belastbares Endprodukt dient. Wenn Sie GPT-4o einsetzen, dann mit Response-Validation, Citation-Gating und strikter Trennung zwischen Tool-Rohdaten und freier Zusammenfassung.