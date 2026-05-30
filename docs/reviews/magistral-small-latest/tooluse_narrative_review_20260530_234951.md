**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:49:51


Nicht deploy, weil das Modell trotz Tool-Kontext halluziniert, keine durchgehend validen Tool-Calls liefert und mit Combined 48.21 die Vertrauensschwelle für produktive MCP-Pipelines verfehlt.

**Tool-Execution-Profil**

Magistral Small kann einzelne Tool-Schritte ausführen, aber es zeigt keine verlässliche Werkzeugwahl. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, fällt es mit P1 35 deutlich ab. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und anschließendes Fetch prüft, erreicht es dagegen P1 80. Das spricht nicht für robuste Tool-Intelligenz, sondern eher für ein festes Muster: Wenn eine Zieladresse direkt konstruierbar ist, funktioniert der Ablauf brauchbar. Wenn erst erkannt werden muss, welches Tool überhaupt nötig ist, bricht die Kette. Dass der Tool-Call insgesamt nicht valide war und ein Retry erforderlich wurde, wirkt hier eher wie ein Verständnis- und Orchestrierungsproblem als ein bloßer Formatfehler. Für MCP-Setups mit dynamischer Tool-Auswahl ist das zu instabil.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 33.33 ist der eigentliche Produktionsbefund: Das Modell extrahiert Inhalte punktuell ordentlich, etwa bei HTTP Fetch & Extract, verliert aber bei mehrstufiger Recherche, bei Suchaufgaben und besonders in multilingualer Synthese die Bindung an das vorliegende Material. Für Pipelines, in denen das Modell Tool-Output präzise zusammenführen soll, fehlt Konsistenz.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, liefert es P2 0 bei erkanntem Halluzinationsbefund. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Ein Modell, das erfundene oder vortrainierte Aussagen als Ergebnis einer Tool-Recherche ausgibt, unterläuft die Kontrollfunktion der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem scheiternden Tool-Aufruf misst, halluziniert Magistral Small keinen Seiteninhalt. Das ist der wichtigste positive Befund. Die Fehlerkommunikation bleibt mit P2 40 nur teilweise klar, aber sie ist für Produktion grundsätzlich akzeptabel, weil das Modell den Ausfall nicht mit erfundenem Ersatz kaschiert.

**Souveränitätsprofil**

Local sovereign ist hier kein Ausgleich für die Ausführungsrisiken. Das Modell liegt 5.32 Punkte unter dem Fleet-Ø von 66.76. Für einen souveränen Stack ist das nur dann tragbar, wenn Tool-Use nicht vertrauenskritisch ist und starke externe Validierung vorgeschaltet wird.

**Fazit & Empfehlung**

Geeignet höchstens für eng geführte Pipelines mit fixer URL-Struktur, klaren Tool-Pfaden und nachgelagerter Ergebnisprüfung. Nicht geeignet für Compliance-Recherche, offene Web-Recherche, mehrsprachige Retrieval-Aufgaben oder allgemein für MCP-Umgebungen, in denen das Modell selbst Tool-Wahl und Synthese verantwortet. Sobald das System entscheiden muss, welches Werkzeug zu nutzen ist und ob eine Aussage wirklich aus dem Tool stammt, ist Magistral Small kein belastbarer Produktionskandidat.