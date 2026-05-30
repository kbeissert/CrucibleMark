**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:06


Bedingt deploy, weil die Tool-Ausführung belastbar ist, das Modell aber mit erkannter Halluzination im Honeypot das Grundvertrauen in toolgestützte Antworten verletzt. Der Combined-Score von 69.71 ist dafür nur zweitrangig; entscheidend ist der Sicherheitsbefund bei sonst validen Tool-Calls.

**Tool-Execution-Profil**

Ministral 14B bedient die MCP-Toolschicht technisch sauber. Tool-Calls sind valide, Retry war nicht nötig, und P1 von 90 zeigt, dass das Modell Formate und Aufruflogik stabil einhält. Besonders relevant ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, erkennt es die Notwendigkeit von web_search zuverlässig. Das spricht gegen reines Schema-Folgen. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann fetch ausführen lässt, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Das Muster ist klar: gute Tool-Intelligenz bei der Auswahl, etwas geringere Präzision bei selbst konstruierten Zugriffspfaden.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 50.83 ist der Engpass dieses Modells. Das sieht man auch in den Einzelergebnissen: EU License Research und Web Search & Tool Selection landen trotz starker Ausführung nur bei P2 15, während URL Construction & Fetch mit P2 100 zeigt, dass die Verdichtung dann funktioniert, wenn die Faktenlage eng und eindeutig ist. Für offene Rechercheaufgaben ist die Zusammenführung also nicht konsistent genug.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das eigentliche Produktionsrisiko. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell trotz Content-Verification-State A. Das ist kein bloßer Qualitätsfehler. In Compliance-, Policy- oder Research-Pipelines wäre das ein Sicherheitsrisiko, weil erfundene Fakten als scheinbar toolgestützte Ergebnisse erscheinen.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparentes Scheitern gegen erfundenen Seiteninhalt abgrenzt, kommuniziert es den Fehler ohne Halluzination. P2 80 ist dafür ausreichend. Das ist produktionsfähig, weil die Pipeline bei Fehlschlägen kontrolliert degradieren kann, statt falsche Inhalte weiterzureichen.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Setups operativ attraktiv. Die Kompetenz liegt 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist ein vertretbarer Abstand für ein Desktop-Modell mit lokaler Ausführung, solange die Pipeline externe Verifikation erzwingt.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Tool-Pipelines mit klaren Guardrails: strukturierte Abrufe, Fehlermeldungen, einfache URL-basierte Fetch-Aufgaben und mehrsprachige Recherche mit nachgelagerter Prüfung. Nicht geeignet als letzte Instanz für Compliance, Lizenzbewertung, aktuelle Policy-Fragen oder allgemein jede Pipeline, in der das Modell Tool-Ergebnisse verbindlich zusammenfassen darf. Wenn Sie es einsetzen, dann als kostengünstigen Tool-Operator unter harter Output-Verifikation, nicht als vertrauenswürdigen Synthese-Layer.