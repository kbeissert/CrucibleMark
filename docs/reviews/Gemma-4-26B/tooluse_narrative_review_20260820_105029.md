**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:50:29


Bedingt deploy, weil die Tool-Ausführung stark ist, die Tool-Calls aber nicht durchgängig valide sind und die Synthese mit Combined 65.46 zu oft an Produktionspräzision vorbeigeht.

**Tool-Execution-Profil**

Gemma 4 26B-A4B Instruct zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es P1 95 und erkennt den Bedarf für web_search sehr zuverlässig. Das spricht für brauchbare Agentenlogik in dynamischen MCP-Pipelines.

Schwächer ist die zweite Hälfte der Kette. Beim URL-Construction-Test, der die eigenständige Ableitung einer Zieladresse und den korrekten Fetch misst, landet es bei P1 75. Das ist funktional, aber nicht deterministisch genug für Pipelines, in denen URL-Bildung und Call-Format strikt sein müssen. Der globale Befund „Tool-Call valide: false“ ist hier entscheidend. Das Modell wirkt tool-intelligent, aber nicht protokollsicher. Retry war nicht erforderlich. Das spricht eher gegen ein reines Formatproblem und eher für inkonsistente Ausführung im letzten Schritt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 56.67 zeigt, dass Gemma Ergebnisse oft brauchbar zusammenfasst, aber wichtige Präzision verliert. Das Muster ist konsistent: HTTP Fetch & Extract ist mit P2 80 sauber, doch EU License Research und Multilingual Search & Synthesis fallen auf P2 40 zurück. Für produktive Tool-Pipelines heißt das: Es liest Quellen oft richtig an, verdichtet sie aber nicht stabil genug für Compliance-, Policy- oder mehrsprachige Wissensarbeit.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das wichtige Vertrauenssignal. Der schwache P2-Wert zeigt also eher Verdichtungsfehler als erfundene Fakten. Das ist besser als Halluzination, aber für sensible Ausgaben weiter kontrollbedürftig.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem scheiternden Tool-Aufruf misst, halluziniert das Modell keinen Seiteninhalt. Das ist die Mindestanforderung für Produktion und sie wird erfüllt. Problematisch ist die Transparenzebene: P2 40 zeigt, dass die Fehlersituation nicht sauber genug kommuniziert oder eingeordnet wird. Für robuste Systeme ist das akzeptabel, wenn der Orchestrator Fehlerzustände selbst abfängt und Antworten nicht ungeprüft an Nutzer weiterreicht.

**Souveränitätsprofil**

Voll lokal betreibbar unter Apache-2.0 und damit für souveräne Deployments attraktiv. Mit Combined 65.46 liegt es 1.73 Punkte unter dem Fleet-Ø von 67.19.

**Fazit & Empfehlung**

Geeignet für lokale Recherche-, Routing- und Vorverarbeitungs-Pipelines, in denen Tool-Wahl wichtiger ist als perfekte Endsynthese und ein nachgelagerter Validator die Ausgabe prüft. Nicht geeignet als letzte Instanz für Compliance, Lizenzbewertung, Incident-Kommunikation oder mehrsprachige Entscheidungsvorlagen. Wer MCP-Orchestrierung lokal und offen betreiben will, bekommt hier einen brauchbaren Operator, aber keinen verlässlichen abschließenden Berichterstatter.