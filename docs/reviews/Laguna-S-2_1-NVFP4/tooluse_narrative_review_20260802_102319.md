**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:23:19


Bedingt deployen, nur für überwachte Tool-Pipelines ohne vertrauenskritische Synthese, weil zwar die Tool-Ausführung oft gelingt, aber Halluzination erkannt wurde, Tool-Calls nicht durchgängig valide sind und das Gesamtbild mit 62.62 nur moderat ausfällt.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz, aber keine verlässliche Protokolldisziplin. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis zwischen Suche und direktem Fetch unterschieden wird, trifft es die richtige Werkzeugwahl sehr sicher. Das spricht gegen ein starres Schema. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es brauchbar, aber weniger präzise. Diese Differenz ist wichtig: Das Modell erkennt oft, welches Tool grundsätzlich nötig ist, produziert aber nicht stabil genug die Form, die eine deterministische MCP-Pipeline braucht. Dass der Tool-Call insgesamt als nicht valide markiert ist, verschiebt die Bewertung klar in Richtung Integrationsrisiko. Positiv ist nur, dass kein Retry erforderlich war. Das Problem liegt daher eher im Erstverständnis oder in der Call-Form als in bloßer Formatnervosität.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung ist mit 33.33 der limitierende Faktor dieses Modells. Besonders bei HTTP Fetch & Extract, also strukturierter Faktenextraktion aus realem Seiteninhalt, und bei Multilingual Search & Synthesis bricht die Verdichtungsqualität ein. Das Modell kann Informationen beschaffen, aber es hält sie in der Antwort nicht sauber zusammen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene oder vorab gelernte Fakten als Ergebnis einer Tool-Recherche ausgibt, verliert die gesamte Tool-Infrastruktur ihren Vertrauensanker.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der den Umgang mit einem fehlschlagenden Abruf prüft, reagiert das Modell akzeptabel. Es kommuniziert den Fehler transparent und erfindet keinen Seiteninhalt. Für Produktion ist genau dieses Verhalten entscheidend. Ein fehlgeschlagenes Tool darf die Antwort verschlechtern, aber nicht in Fiktion kippen.

**Betriebsprofil**

Total 561.38s pro Run. Langsam.  
Call 1: 35.92s. MCP-Latenz: 1.11s. Call 2: 56.54s.  
Kosten/Run: local. Günstig im Betrieb, aber die Laufzeit ist im Verhältnis zur gezeigten Syntheseleistung schwach.

**Fazit & Empfehlung**

Geeignet für agentische Vorstufen, in denen Tool-Auswahl, Web-Recherche und robuste Fehlerkommunikation wichtiger sind als belastbare Endverdichtung. Nicht geeignet für Compliance-, Lizenz-, Research- oder Executive-Summary-Pipelines, in denen die Antwort strikt an Tool-Belege gebunden bleiben muss. Wenn Sie es einsetzen, dann als beschaffendes Zwischenmodell mit harter nachgelagerter Validierung und ohne Freigabe für finale Nutzerantworten.