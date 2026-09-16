**Deployment-Urteil**

> **Erstellt am:** 15.09.2026, 08:22:10


Bedingt deploy, weil die Tool-Ausführung insgesamt tragfähig ist, aber die Tool-Calls nicht durchgängig valide waren und die Synthesequalität für vertrauenskritische Pipelines zu ungleich ausfällt.

**Tool-Execution-Profil**

Swift Qwen 3.8 27B zeigt echte Werkzeugwahl statt reinem Standardmuster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, erkennt es den Bedarf für web_search sauber und erreicht volle Ausführungssicherheit. Das spricht für brauchbare Planungslogik in dynamischen MCP-Pipelines.

Schwächer ist die Präzision im Anschluss. Beim URL-Construction-Test, der prüft, ob das Modell die Ziel-URL selbst ableitet und dann fetch korrekt nutzt, bleibt es brauchbar, aber nicht deterministisch genug für strikt automatisierte Flows. Das passt zum globalen Befund: P1 ist stark, aber `tool_call_valid=false` zeigt, dass Protokolltreue und Call-Genauigkeit nicht in jedem Lauf sauber sitzen. Für produktive Tool-Ketten heißt das: gute Intent-Erkennung, aber Absicherung auf Executor-Seite bleibt Pflicht.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. Die P2-Leistung liegt sichtbar unter der Ausführungsleistung. Bei EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis bricht die Verdichtung ein. Das Modell beschafft Informationen oft erfolgreich, formuliert sie danach aber zu grob, lässt relevante Einschränkungen liegen oder priorisiert nicht sauber genug für Architekten-Entscheidungen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, und das ist der wichtigere Vertrauenspunkt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen beantwortet werden, zeigt es zwar nur schwache Nutzwert-Synthese, aber keine erkannte Halluzination. Das ist kein Qualitätssieg, aber ein Vertrauenssignal: Es erfindet nicht offen aktuelle Compliance-Fakten.

**Fehlerresilienz**

Hier ist das Modell produktionsfähig. Im 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call statt erfundenem Seiteninhalt misst, kommuniziert es den Fehler sauber und halluziniert keinen Ersatzinhalt. Genau dieses Verhalten braucht eine Tool-Pipeline: sichtbarer Ausfall statt stiller Fiktion.

**Betriebsprofil**

Total 202.69s pro Run. Call 1: 4.21s. Call 2: 28.14s. MCP-Latenz: 1.43s. Lokal betrieben, also infrastrukturell günstig. Gemessen an der nur guten Gesamtleistung ist das langsam.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen Tool-Auswahl, Recherche-Anstoß und robuste Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Gut einsetzbar als beschaffende oder vorbereitende Agentenstufe mit nachgelagerter Validierung. Nicht die richtige Wahl für Compliance-, Policy- oder Executive-Summary-Pipelines, in denen die Antwort selbst präzise, belastbar und ohne Interpretationsspielraum verdichtet werden muss.