**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:14:43


Bedingt deploy, weil es Tools zuverlässig und protokollkonform nutzt, aber die Synthesetreue für produktive Wissenspipelines zu schwach und mit Halluzinationsbefund sicherheitsrelevant ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Die Calls waren valide, retry war nicht nötig, und der P1-Wert zeigt, dass Gemma 3 12B IT in einer MCP-Pipeline grundsätzlich steuerbar ist. Beim Test Web Search & Tool Selection, der prüft ob das Modell ohne Hinweis zwischen Suche und Direktabruf unterscheidet, wählt es das richtige Werkzeug sicher. Das spricht gegen bloßes Schema-Folgen und für brauchbare Werkzeugwahl im Kontext. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Integrationen. Das Muster ist klar: Es versteht, welches Tool gebraucht wird, ist aber weniger präzise, wenn es die Eingabeparameter selbst konstruieren muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert ist der eigentliche Bremsklotz dieses Modells. Besonders bei HTTP Fetch & Extract, also der präzisen Extraktion konkreter Fakten aus abgerufenen Inhalten, fällt die Verdichtung sichtbar ab. Auch EU License Research bleibt in der Zusammenführung zu grob. Für Pipelines, in denen exakte Jahreszahlen, Eigennamen, Versionen oder Compliance-Details aus Tool-Output übernommen werden müssen, ist das zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell formal im akzeptablen Bereich und halluziniert dort nicht. Das Vertrauensurteil ist trotzdem nur begrenzt positiv: Content-Verification-State B2 und P2 40 zeigen, dass es zwar nicht frei erfindet, aber den verifizierten Inhalt nicht robust genug in belastbare Antwortform überführt. Da insgesamt Halluzination erkannt wurde, ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko für jede Pipeline, die Tool-Output als autoritativ behandelt.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparente Reaktion auf fehlschlagende Tool-Calls misst, kommuniziert das Modell den Fehler, statt Seiteninhalt zu erfinden. P2 60 ist nicht elegant, aber operativ ausreichend. Entscheidend ist: kein halluzinierter Ersatzinhalt trotz Fehler.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Mit einem Combined Score von 69.42 liegt es 1.37 Punkte über dem Fleet-Ø von 67.62 und bleibt damit trotz lokaler Ausführung fleet-kompetitiv.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit klaren Tool-Grenzen, transparenter Fehlerbehandlung und menschlicher oder nachgelagerter Validierung der Antworttexte. Gut einsetzbar für Recherche-Orchestrierung, Suchschritte und einfache Fetch-Workflows. Nicht geeignet für Compliance, Vertragsauswertung, präzise Faktenextraktion oder andere Pfade, in denen die verbale Verdichtung selbst als verlässliches Endprodukt dienen muss. Wer Tool-Use braucht, aber der finalen Antwort nicht blind vertrauen darf, kann es einsetzen. Wer belastbare Tool-Synthese braucht, sollte es nicht als letzte Instanz verwenden.