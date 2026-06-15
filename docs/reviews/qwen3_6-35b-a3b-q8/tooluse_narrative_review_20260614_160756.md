**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:07:56


Bedingt deploy, weil die Tool-Ausführung oft stark ist, das Modell aber mindestens einen invaliden Tool-Call produziert, einen Retry braucht und bei der Synthese nicht stabil genug innerhalb der Tool-Befunde bleibt. Der Combined-Score ist brauchbar, das Vertrauensprofil für produktive Tool-Pipelines aber nicht sauber.

**Tool-Execution-Profil**

Qwen 3.6 35B-A3B zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr zuverlässig. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann per fetch abrufen lässt, ist es ebenfalls solide, aber weniger deterministisch. Das spricht für brauchbare Planungsfähigkeit, nicht für reine Fetch-Routine.

Der kritische Punkt ist die Protokolltreue. Tool-Call valide: false und Retry erforderlich: true deuten weniger auf fehlendes Aufgabenverständnis als auf ein Format- oder Ausführungsproblem im MCP-Ablauf. Für produktive Orchestrierung ist das relevant, weil ein einzelner formaler Fehltritt Kontrolllogik, Timeouts und Folge-Calls auslösen kann. P1 ist insgesamt solide, aber nicht robust genug für unbeaufsichtigte Ketten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. Starke Extraktion bei HTTP Fetch & Extract und URL Construction & Fetch zeigt, dass das Modell konkrete Web-Inhalte sauber übernehmen kann. Dagegen fällt die Verdichtungsqualität bei Web Search & Tool Selection und besonders bei EU License Research deutlich ab. Das Modell kann also Befunde einsammeln, verliert aber bei der finalen Zusammenführung an Präzision.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das Sicherheitsrisiko. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Parametern beantwortet werden, ist die Antwort nicht klar auf belastbare Tool-Befunde verankert. Auch wenn dort kein Halluzinationsflag gesetzt wurde, ist der Verifikationszustand schwach. Da global Halluzination erkannt: true vorliegt, muss man das als Vertrauensbruch gegen die Tool-Infrastruktur werten, nicht als bloßen Qualitätsfehler.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt abgrenzt, verhält sich das Modell produktionsgerecht. Es halluziniert keinen Seiteninhalt und kommuniziert den Fehlschlag ausreichend offen. Das ist für echte Pipelines ein klar positiver Befund.

**Souveränitätsprofil**

Lokal betreibbar: ja. Fleet-Kompetenz: knapp darunter. Das Modell liegt 1.37-Punkte unter dem Fleet-Ø von 67.84. Für souveräne On-Prem-Nutzung ist das ein akzeptabler Abstand, zumal die Ausführung lokal erfolgt. Das Provenienzrisiko der offenen Gewichte aus China bleibt jedoch ein eigener Governance-Punkt.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Pipelines mit menschlicher Nachkontrolle, klaren Retry-Regeln und strikter Tool-Output-Validierung. Gut einsetzbar für Fetch, Extraktion, mehrsprachige Suche und saubere Fehlerbehandlung. Nicht geeignet für Compliance-nahe oder vollautonome MCP-Ketten, in denen das Modell Ergebnisse verbindlich zusammenfasst und Tool-Befunde strikt einhalten muss. Als ausführendes Teilmodell brauchbar. Als vertrauenswürdige Endinstanz für toolgestützte Wahrheit nicht ausreichend.