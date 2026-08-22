**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:49:45


Nicht deploy für autonome MCP-Pipelines, weil die Tool-Calls nicht valide sind und der kombinierte Nutzwert mit 20.33 trotz fehlender Halluzinationen klar zu schwach ausfällt.

**Tool-Execution-Profil**

Mistral Small 4 zeigt in diesem Lauf kein verlässliches Tool-Verhalten. Der Kernbefund ist nicht ein einzelner Fehlgriff, sondern ein systematisches Ausbleiben brauchbarer Ausführung. Bei EU License Research funktioniert der Ablauf noch, aber in allen operativen Tool-Disziplinen fällt das Modell aus: HTTP Fetch & Extract, Tool Failure Handling (404), Web Search & Tool Selection, URL Construction & Fetch und Multilingual Search & Synthesis stehen bei P1 jeweils auf 0.

Das ist vor allem bei der Werkzeugwahl kritisch. Beim Web-Search-Test, der ohne expliziten Hinweis prüft, ob statt fetch ein Suchtool gebraucht wird, erkennt das Modell die passende Strategie nicht. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann korrekt abrufen soll, liefert es ebenfalls keine nutzbare Ausführung. Das wirkt nicht wie flexible Tool-Intelligenz, sondern wie ein fragiles Muster, das nur unter sehr enger Aufgabenführung trägt. Ein Retry war nicht nötig. Das spricht eher gegen ein bloßes Formatproblem und eher für schwaches operatives Verständnis der Tool-Infrastruktur.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Mit P2 39.17 formuliert das Modell zwar lesbare Zusammenfassungen, verliert aber bei extraktionsnahen Aufgaben Präzision und Vollständigkeit. Für Pipelines, in denen Jahreszahlen, Bezeichnungen oder Statusangaben exakt aus Tool-Output übernommen werden müssen, reicht das nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, bleibt es hinreichend diszipliniert. P2 60 ist nicht stark, aber der wichtigere Punkt ist: keine erkannte Halluzination. Das Vertrauenssignal ist damit besser als die eigentliche Arbeitsleistung.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Abruf prüft, erfindet das Modell keinen Seiteninhalt. Das ist der Mindeststandard für Produktion und hier erfüllt. Die Antwortqualität bleibt mit P2 20 schwach. Das Modell kommuniziert den Fehler also eher unzureichend als gefährlich. Für überwachte Workflows ist das akzeptabel, für autonome Fehlerbehandlung noch nicht.

**Souveränitätsprofil**

Lokal betreibbar unter Apache 2.0 und damit souveränitätsfreundlich. Fleet-kompetitiv ist es in diesem Benchmark jedoch nicht. Der Sovereignty Gap ist n/a Punkte unter dem Fleet-Ø von 67.19, weil kein vergleichbarer kombinierter Souveränitätsabstand ausgewiesen wurde. Praktisch zählt hier: lokal ja, produktionsreif für Tool-Orchestrierung nein.

**Fazit & Empfehlung**

Geeignet ist Mistral Small 4 für lokale, souveräne Assistenzfälle mit menschlicher Kontrolle, etwa Vorstrukturierung, einfache Zusammenfassungen oder UI-nahe Copilot-Aufgaben ohne harten Tool-Zwang. Nicht geeignet ist es für MCP-Pipelines, die selbstständig Tools auswählen, URLs konstruieren, Fetch-Aufrufe valide ausführen und fremde Tool-Ergebnisse präzise weiterreichen müssen. Wenn Sie diesem Modell eine Tool-Infrastruktur übergeben, brauchen Sie eine strikte äußere Orchestrierung, Validierung jeder Tool-Transition und idealerweise ein anderes Modell für den eigentlichen Tool-Use.