**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:50:17


Nicht deploy für autonome MCP-Pipelines, weil Halluzination erkannt wurde, Tool-Calls nicht durchgängig valide sind und das Gesamtbild mit 56.21 nur dann tragfähig ist, wenn ein harter Guardrail-Layer jede Antwort und jeden Tool-Schritt überprüft.

**Tool-Execution-Profil**

Mistral Small 3.1 kann Tools bedienen, aber nicht verlässlich orchestrieren. Die stärkste Seite ist der direkte Abrufpfad: Beim URL-Construction-Test, der prüft ob das Modell eine Ziel-URL selbst ableitet und dann korrekt per Fetch abruft, liegt es mit P1 80 klar im brauchbaren Bereich. Auch HTTP Fetch & Extract zeigt, dass es strukturierte Inhalte nach erfolgreichem Abruf verarbeiten kann.

Das Kernproblem liegt bei der Werkzeugwahl. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis die Entscheidung zwischen web_search und fetch verlangt, fällt es mit P1 35 deutlich ab. Das spricht nicht für echte Tool-Intelligenz, sondern für ein Muster: Wenn eine URL ableitbar wirkt, arbeitet es ordentlich. Wenn erst entschieden werden muss, welches Werkzeug überhaupt nötig ist, bricht die Steuerung ein. Dass ein Retry erforderlich war, wirkt hier eher wie ein Verständnis- und Orchestrierungsproblem als ein reines Formatproblem. Ein MCP-Controller kann das teilweise abfedern, sollte aber keine selbstständige Tool-Planung erwarten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. Bei HTTP Fetch & Extract erreicht es P2 100 und kann konkrete Inhalte sauber zusammenführen. In Web Search & Tool Selection fällt P2 auf 0, in Multilingual Search & Synthesis auf 40. Das Muster ist klar: Solange der Input sauber und direkt vorliegt, verdichtet es brauchbar. Sobald mehrere Such- und Auswahlentscheidungen vorgeschaltet sind, wird die Synthese fragil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Vorwissen beantwortet werden, liegt P2 bei 15 und Halluzination wurde erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Ein Modell, das erfundene oder aus dem Training rekonstruierte Aussagen als Tool-Ergebnis ausgibt, unterläuft die Vertrauensgrenze der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Call misst, halluziniert das Modell keinen Seiteninhalt. Das ist der zentrale positive Befund. P2 40 zeigt aber, dass die Fehlerkommunikation nur teilweise sauber ist. Für Produktion ist das akzeptabel, sofern der Orchestrator Fehlerzustände selbst sichtbar macht und keine stille Weiterverarbeitung zulässt.

**Souveränitätsprofil**

Lokal betreibbar, kostenseitig attraktiv und für souveräne Stacks operativ interessant. Die gemessene Kompetenz liegt aber 5.32 Punkte unter dem Fleet-Ø von 66.76. Das Modell erfüllt also den Souveränitätsbedarf besser als den Qualitätsbedarf.

**Fazit & Empfehlung**

Geeignet für kostensensitive, lokal betriebene Pipelines mit enger Aufgabenführung: feste URLs, bekannte Tools, niedrige regulatorische Tragweite, Pflicht-Validierung nach jedem Schritt. Nicht geeignet für Compliance-, Research- oder dynamische Retrieval-Pipelines, in denen das Modell selbst das richtige Werkzeug wählen und die Tool-Ausgabe strikt wahrheitsgebunden verdichten muss. Wenn Sie es einsetzen, dann als ausführendes Teilmodell unter einem strengeren Planner und mit externer Faktenprüfung vor jeder Ausgabe.