**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:48:33


Nicht deploy für vertrauenskritische MCP-Pipelines, weil Grok 4.5 trotz gutem Gesamtscore halluziniert und zugleich keinen durchgehend validen Tool-Call-Pfad zeigt.

**Tool-Execution-Profil**

Bei der Werkzeugwahl zeigt das Modell echte situative Intelligenz. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erkennt es den passenden Zugriffspfad zuverlässig. Das spricht gegen bloßes Musterfolgen. Auch bei Multilingual Search & Synthesis nutzt es Tools aktiv und zielgerichtet.

Schwächer wird es bei der Ausführungsschärfe. Im Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Fetch misst, arbeitet es brauchbar, aber nicht deterministisch genug für harte Produktionspfade. Der globale Befund „Tool-Call valide: false“ ist hier entscheidend. Das Modell kann Tool-Nutzung planen, liefert aber nicht konsistent einen protokollsauberen, verlässlich maschinenverarbeitbaren Ausführungspfad. Positiv ist, dass kein Retry erforderlich war. Das Problem liegt daher eher in der Erstpräzision als in bloßen Formatfehlern nach Korrekturschleifen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. Bei HTTP Fetch & Extract und URL Construction & Fetch verdichtet Grok 4.5 sauber und ausreichend präzise. Auch Web Search & Tool Selection ist stark. Der Gesamtwert für P2 von 60 zeigt aber, dass diese Qualität nicht stabil über alle Aufgabentypen trägt. Besonders bei mehrdeutigen oder compliance-nahen Faktenlagen kippt die Verdichtung von nützlicher Zusammenfassung in unsichere Behauptung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, und das ist der kritische Punkt. Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, liegt P2 bei 15 und eine Halluzination wurde erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell in einer Tool-Pipeline erfundene oder aus Trainingswissen rekonstruierte Aussagen als recherchiertes Ergebnis ausgibt, verliert die gesamte Infrastruktur ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlgeschlagene Tool-Calls misst, bleibt Grok 4.5 auf der akzeptablen Seite. Es halluziniert keinen Seiteninhalt trotz Fehler. Die Fehlerkommunikation ist damit produktionsfähig, auch wenn die inhaltliche Aufbereitung mit P2 60 nur durchschnittlich klar ausfällt. Für Betriebspipelines ist Transparenz hier wichtiger als sprachliche Eleganz.

**Betriebsprofil**

Call 1: 2.33s. MCP-Latenz: 1.40s. Call 2: 12.90s. Total: 99.77s.  
Preis: $2.0 pro 1M Input-Tokens, $6.0 pro 1M Output-Tokens.  
Fazit: eher langsam für den gemessenen Nutzwert, preislich Frontier-üblich, aber nicht günstig im Verhältnis zum Vertrauensrisiko.

**Fazit & Empfehlung**

Geeignet ist Grok 4.5 für assistive Recherche, explorative Analysten-Workflows und menschlich beaufsichtigte Tool-Ketten, in denen Ergebnisse sichtbar geprüft werden. Nicht geeignet ist es für Compliance, Lizenzprüfung, Policy-Auswertung, autonome Retrieval-Synthese oder jede Pipeline, in der Tool-Ergebnisse als belastbare Fakten weitergereicht werden. Wenn Sie es einsetzen, dann nur mit strikter Output-Verifikation, Quellenzwang und nachgelagerter Validierung außerhalb des Modells.