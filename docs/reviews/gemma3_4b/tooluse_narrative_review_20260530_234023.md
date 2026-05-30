**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:23


Bedingt deploy, weil Gemma 3 4B valide Tool-Calls erzeugt und bei der Tool-Ausführung stark ist, aber mit erkannter Halluzination bei nur moderater Gesamteignung kein vertrauenswürdiger Endpunkt für faktenkritische MCP-Pipelines ist.

**Tool-Execution-Profil**

Bei der Ausführung arbeitet das Modell überraschend diszipliniert. Der Tool-Call war valide, ein Retry war nicht nötig, und P1 von 90 zeigt, dass es MCP-konforme Aufrufe stabil produziert. Besonders relevant ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es korrekt, dass erst web_search nötig ist. Das spricht gegen reines Musterfolgen. Beim Test URL Construction & Fetch, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen lässt, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Fetch-Ketten. Insgesamt zeigt das Modell echte Tool-Intelligenz bei der Auswahl, aber geringere Präzision, sobald es selbst Zieladressen konstruieren muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 40.83 ist der klare Schwachpunkt. Die niedrigen Werte in EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis zeigen, dass das Modell abgerufene Inhalte nicht zuverlässig in belastbare, präzise Antworten überführt. Es kann also das richtige Werkzeug nutzen und trotzdem im letzten Schritt ungenau werden.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Parametergedächtnis kommen, halluziniert das Modell trotz Content-Verification-State A. Das ist kein bloßer Qualitätsfehler, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Recherche ausgibt, verliert die gesamte Tool-Infrastruktur ihren Vertrauensvorteil.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Aufruf misst, bleibt Gemma 3 4B auf der sicheren Seite. Es halluziniert keinen Seiteninhalt trotz Fehler. P2 von 40 ist nicht stark, aber das entscheidende Produktionssignal ist positiv: Das Modell kommuniziert den Ausfall statt Ersatzfakten zu erfinden. Das ist für produktive Systeme akzeptabel.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Setups operativ attraktiv. Gleichzeitig liegt es mit einem Sovereignty Gap von -5.32 Punkten unter dem Fleet-Ø von 66.76. Das heißt: gute lokale Einsetzbarkeit, aber keine voll konkurrenzfähige Gesamtleistung gegenüber dem Fleet-Mittel.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische Pipelines mit klarer Tool-Führung, einfacher Recherche, Vorfilterung und Fehlerrobustheit. Nicht geeignet für Compliance-, Policy-, Lizenz-, oder andere faktenkritische Workflows, in denen die Antwort strikt an Tool-Belege gebunden bleiben muss. Wenn Sie es einsetzen, dann nur mit harter Quellenausgabe, nachgelagerter Validierung und ohne Freigabe für autonome Endsynthese.