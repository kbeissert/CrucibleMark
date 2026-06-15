**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:17:07


Nicht deploy für produktive MCP-Pipelines, weil das Modell trotz brauchbarer Teiltreffer bei der Tool-Ausführung erfundene Inhalte als toolgestützte Ergebnisse ausgibt. Der kombinierte Befund ist schwach, der Tool-Call war nicht durchgehend valide, und ein Retry war erforderlich.

**Tool-Execution-Profil**

Magistral Small zeigt keine verlässliche Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der prüft ob das Modell ohne Hinweis erkennt, dass erst gesucht und nicht direkt gefetcht werden muss, fällt es klar ab. Das spricht gegen situationsabhängige Tool-Wahl und eher für ein starres Muster. Dagegen ist es beim URL-Construction-Test, der die Ableitung einer Ziel-URL und den anschließenden Fetch misst, deutlich sicherer. Es kann also bekannte oder stark implizite Pfade ausführen, erkennt aber den vorgelagerten Recherchebedarf nicht stabil.

Der erforderliche Retry wirkt deshalb nicht wie ein reines Formatproblem. Zusammen mit dem invaliden Tool-Call deutet er eher auf Verständnisprobleme in der Orchestrierung hin: Das Modell kann einzelne Schritte ausführen, entscheidet aber nicht robust, welcher Schritt als Nächstes korrekt ist.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung ist mit 33.33 der eigentliche Engpass. Positiv ist nur HTTP Fetch & Extract, wo strukturierte Fakten aus echtem Seiteninhalt brauchbar übernommen werden. Sobald mehrere Quellen, Sprachwechsel oder Rechercheentscheidungen dazukommen, bricht die Verdichtung sichtbar ein. Besonders EU License Research und Multilingual Search & Synthesis liefern faktisch keine belastbare Zusammenfassung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, liefert das Modell P2=0 bei erkannter Halluzination. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wer einer Tool-Pipeline aktuelle Compliance- oder Policy-Fragen anvertraut, verliert mit diesem Verhalten die Beweiskette zwischen Quelle und Antwort.

**Fehlerresilienz**

Beim 404-Test, der die Reaktion auf einen fehlschlagenden Tool-Call misst, halluziniert Magistral Small keinen Seiteninhalt. Das ist der wichtigste Punkt dieser Sektion und für Produktion grundsätzlich akzeptabel. Die Transparenz bleibt jedoch nur teilweise brauchbar, weil die Synthesequalität auch hier begrenzt ist. Das Modell scheitert also eher an sauberer Einordnung als an gefährlicher Erfindung.

**Souveränitätsprofil**

Souveränitätsseitig ist das Angebot attraktiv, aber leistungsschwach. Das Modell liegt 1.37 Punkte unter dem Fleet-Ø von 67.84. Für local_sovereign ist das kein Ausreißer nach unten, aber auch kein Grund, Produktionsrisiken bei der Verifikation zu akzeptieren.

**Fazit & Empfehlung**

Geeignet ist Magistral Small höchstens für interne Assistenzpfade mit menschlicher Abnahme, bei denen Tools vor allem zum Abruf einzelner bekannter Seiten dienen und Fehlantworten keine Folgekosten erzeugen. Nicht geeignet ist es für Compliance, regulatorische Recherche, dynamische Web-Recherche, mehrsprachige Beschaffung oder jede Pipeline, in der Tool-Ausgaben als vertrauenswürdige Grundlage gelten müssen. Wer dem Modell Infrastruktur übergibt, muss derzeit damit rechnen, dass es den Tool-Frame verlässt.