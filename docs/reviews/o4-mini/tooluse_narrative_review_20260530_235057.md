**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:50:57


Bedingt deploy, weil o4-mini valide Tool-Calls erzeugt, aber mit erkannter Halluzination und nur moderater Gesamtleistung von 62.54 kein uneingeschränkt vertrauenswürdiges Tool-Modell für produktive Faktenpipelines ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke. Mit P1 85 produziert o4-mini überwiegend valide MCP-konforme Aufrufe. Beim Test Web Search & Tool Selection, der prüft ob das Modell ohne Hinweis zwischen Suche und direktem Abruf unterscheidet, wählt es das richtige Werkzeug sicher aus. Das spricht gegen bloßes Schema-Folgen und für echte Werkzeugwahl unter Unsicherheit. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Abruf misst, ist es weniger präzise. Die 75 Punkte zeigen brauchbare, aber nicht vollständig deterministische URL-Bildung. Retry erforderlich wirkt hier eher wie ein Ausführungs- oder Formatproblem als ein grundsätzliches Verständnisdefizit. Das Modell weiß meist, was es tun muss, trifft aber nicht jeden Schritt im ersten Versuch robust genug für harte Automatisierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Mit P2 40.83 ist die eigentliche Verdichtung der Tool-Ausgaben der Schwachpunkt. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo Inhalte zwar gefunden oder angestoßen werden, aber in der Antwort nicht sauber, belastbar und quellentreu zusammengeführt werden. Für Pipelines, in denen das Modell Ergebnisse nur weiterreicht oder grob zusammenfasst, ist das noch nutzbar. Für Compliance, Policy oder Research-Synthesen ist es zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, liegt P2 bei 15 und Halluzination wurde erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als recherchiertes Ergebnis ausgibt, untergräbt es die Vertrauenskette der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Aufruf misst, reagiert o4-mini akzeptabel. P2 60 ist nicht elegant, aber entscheidend ist: Es halluziniert keinen Seiteninhalt trotz Fehler. Für Produktion ist das der richtige Ausfallmodus. Fehler werden eher offengelegt als verdeckt.

**Betriebsprofil**

Total 73.58s pro Run: langsam.  
Call-Latenzen 4.42s und 6.85s, MCP-Latenz 1.00s: die Laufzeit entsteht nicht nur im Tooling.  
Kosten 0.047125 USD pro Run: günstig bis moderat.  
Im Verhältnis zur Leistung ist das Kostenprofil brauchbar, das Zeitprofil für interaktive oder hochvolumige Pipelines jedoch angespannt.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines mit klaren Tool-Grenzen, transparenter Fehlerbehandlung und nachgelagerter Validierung, etwa Recherche-Vorbereitung, Tool-Routing oder URL-/Search-Orchestrierung. Nicht geeignet für Pipelines, in denen die Modellantwort selbst als verlässliche faktische Endaussage gilt, besonders bei Compliance, Lizenzfragen, mehrsprachiger Synthese oder jeder Quelle-muss-stimmen-Anforderung. Wer o4-mini einsetzt, sollte es als Tool-Operator behandeln, nicht als letzte Instanz für inhaltliche Wahrheit.