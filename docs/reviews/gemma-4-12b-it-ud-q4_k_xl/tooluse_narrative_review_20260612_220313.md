**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:03:13


Bedingt deploy, weil die Tool-Aufrufe verlässlich und protokollkonform sind, die Synthese aber zu oft an Präzision verliert und ein Halluzinationssignal im Gesamtlauf das Vertrauen für sensible Pipelines begrenzt.

**Tool-Execution-Profil**

Das Modell kann einer MCP-gestützten Tool-Infrastruktur grundsätzlich übergeben werden. Die Call-Validität ist gegeben, Retry war nicht nötig. Das spricht gegen ein Formatproblem und für stabiles Protokollverhalten. Bei **Web Search & Tool Selection**, also dem Test, ob ohne Hinweis das richtige Werkzeug erkannt wird, arbeitet es stark und wählt die Suche statt eines vorschnellen Fetchs. Das ist ein Signal für echte Werkzeugwahl, nicht nur für starres Musterfolgen. Beim **URL Construction & Fetch**, also dem Test auf eigenständige URL-Ableitung und anschließenden Abruf, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Das Muster ist klar: gute Entscheidung auf Werkzeug-Ebene, geringere Präzision bei selbst konstruierten Zieladressen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung zeigt, dass das Modell gefundene Inhalte oft nur teilweise sauber komprimiert. Das sieht man an **HTTP Fetch & Extract**, wo strukturierte Fakten aus echtem Seiteninhalt nicht stabil genug verdichtet werden, und an **Multilingual Search & Synthesis**, wo die Recherche funktioniert, die deutsche Zusammenführung aber an Schärfe verliert. Für Pipelines, die exakte Extraktion, Compliance-Zusammenfassungen oder belastbare Entscheidungsgrundlagen erwarten, ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt es im Ergebnisraum und halluziniert dort nicht. Das ist das wichtigere Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als abgerufene Fakten ausgeben kann, beschädigt es die Nachvollziehbarkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Im **Tool Failure Handling (404)**, also dem Test auf transparente Reaktion bei fehlgeschlagenem Abruf, verhält sich das Modell akzeptabel. Es erfindet keinen Seiteninhalt trotz 404. Die eigentliche Schwäche liegt nicht in der Fehlerbehandlung, sondern in der nachgelagerten Verdichtung. Für Produktion ist das ein wesentlicher Unterschied: ein transparenter Fehler ist beherrschbar, erfundener Ersatzinhalt nicht.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Umgebungen attraktiv. Leistungsseitig liegt es jedoch 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist konkurrenzfähig genug für lokale Grundversorgung, aber kein starkes Argument für qualitätskritische Workloads.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Tool-Pipelines mit menschlicher Abnahme, klaren Retrieval-Grenzen und eher operativen Aufgaben wie Suche, Routing und einfache Web-Abrufe. Nicht geeignet für Compliance, Lizenzprüfung, präzise Faktenextraktion oder jede Kette, in der die textliche Verdichtung selbst als verlässliches Endprodukt dienen muss. Wenn Sie es einsetzen, dann als Werkzeugnutzer mit nachgeschalteter Verifikation, nicht als letzte Instanz für Synthese.