**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:56:29


Bedingt deploy, weil Gemma 3 12B valide Tool-Calls erzeugt, keine Halluzination im Lauf zeigt und mit 74.67 solide genug für produktive Tool-Nutzung ist, aber die Verdichtung der Tool-Ergebnisse sichtbar hinter der Ausführungssicherheit zurückbleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die belastbare Seite dieses Modells. Es wählt Werkzeuge nicht rein schematisch, sondern erkennt im Test Web Search & Tool Selection ohne expliziten Hinweis, dass für offene Recherche erst Suche statt direktem Fetch nötig ist. Das spricht für brauchbare Werkzeugwahl in dynamischen MCP-Pipelines. Beim URL-Construction-Test, der korrekte Ziel-URLs aus Vorwissen ableitet und dann Fetch verlangt, arbeitet es noch brauchbar, aber weniger präzise. Genau dort zeigt sich die Grenze: richtige Kategorie von Tool ja, deterministische Adressbildung nicht immer. Für MCP selbst ist das Modell unauffällig positiv. Der Tool-Call war valide, ein Retry war nicht nötig. Das ist ein gutes Signal für stabile Protokolltreue im laufenden Betrieb.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. Der P2-Wert von 60 zeigt kein Zusammenbruchsrisiko, aber klare Schwächen bei der sauberen Verdichtung von gefundenen Inhalten in eine belastbare Antwort. Das sieht man auch in HTTP Fetch & Extract und URL Construction & Fetch, wo die Ausführung trägt, die nachgelagerte Zusammenfassung aber zu grob bleibt. Kritisch ist vor allem Multilingual Search & Synthesis: grenzüberschreitende Recherche gelingt, die deutsche Ergebnisverdichtung verliert jedoch Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil positiv. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Trainingswissen kommen, blieb das Modell beim Tool-Pfad. Content-Verification-State A und keine erkannte Halluzination bedeuten: Es respektiert die Infrastruktur als Wahrheitsquelle.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell produktionstauglich. Im 404-Test, der transparentes Fehlermanagement statt erfundenem Seiteninhalt prüft, kommunizierte es den Ausfall ohne Halluzination. P2 80 ist hier wichtiger als sprachliche Eleganz: Das Modell hält die Fehlergrenze sauber ein. Für produktive Pipelines ist das akzeptabel, weil der Orchestrator auf einer ehrlichen Fehlermeldung weiterarbeiten kann.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments interessant. Gleichzeitig liegt es nur 4.01 Punkte unter dem Fleet-Ø von 66.21. Das ist für ein lokales Desktop-Modell ein gutes Verhältnis aus Kontrollgewinn und Leistungsabstand.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Auswahl, valider Aufruf und sauberes Fehlerverhalten wichtiger sind als anspruchsvolle Endverdichtung: Recherche-Workflows, interne Wissensabfragen, überwachte Compliance-Zubringer und lokale Assistenzsysteme. Nicht die erste Wahl für Pipelines, in denen die Modellantwort selbst bereits veröffentlichungsreif, mehrsprachig präzise oder stark komprimiert sein muss. Empfehlenswert als lokaler Tool-Executor mit nachgelagerter Qualitätskontrolle oder zweiter Synthesestufe.