**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:18:17


Bedingt deploy, weil das Modell keine Halluzination im Benchmark gezeigt hat, aber mit ungültigen Tool-Calls, Retry-Bedarf und einem schwachen Combined-Score von 51.96 keine verlässliche Erstpass-Ausführung für MCP-Pipelines liefert.

**Tool-Execution-Profil**

Die Tool-Ausführung ist inkonsistent. Bei **HTTP Fetch & Extract**, also der strukturierten Extraktion aus realem Fetch-Content, arbeitet GPT-5.4 solide. Auch beim **URL-Construction-Test**, der korrekte URL-Ableitung und anschließenden Fetch misst, erreicht es ein brauchbares Niveau. Das spricht dafür, dass das Modell deterministische Abrufe ausführen kann, wenn der Pfad relativ klar ist.

Das Gegenbild zeigt **Web Search & Tool Selection**, also die Aufgabe, ohne expliziten Hinweis zwischen Suche und direktem Fetch zu unterscheiden. Dort fällt es deutlich ab. Das ist kein kleiner Formfehler, sondern ein Hinweis auf schwache Werkzeugwahl in offenen Situationen. Das Modell folgt eher einem vorhandenen Abrufmuster, statt die passende Tool-Klasse robust zu erkennen. Dass `tool_call_valid=false` und `retry_required=true` gesetzt sind, verstärkt diesen Befund. Der Retry wirkt hier nicht wie ein reines Ausgabeformatproblem, sondern wie ein Verständnisproblem an der Schnittstelle zwischen Anfrage, Tool-Selektion und MCP-konformer Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung von 46.67 passt zum Asset-Bild: starke Verdichtung bei klaren Fetch-Aufgaben, aber schwache Synthese bei Recherche, Werkzeugwahl und mehrsprachiger Zusammenführung. Vor allem **Multilingual Search & Synthesis**, also grenzüberschreitende Recherche mit deutscher Ausgabe, zeigt, dass das Modell Ergebnisse nicht stabil genug in eine entscheidungsfeste Antwort überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht zuverlässig genug für Compliance-nahe Recherche. Beim **EU License Research**-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, liegt P2 nur bei 20 bei Verification-State B2. Zwar wurde keine Halluzination markiert, aber das Vertrauenssignal ist trotzdem schwach: Das Modell erfindet nicht, hält sich aber auch nicht sauber genug an den evidenzbasierten Arbeitsmodus.

**Fehlerresilienz**

Beim **Tool Failure Handling (404)**, also dem Test auf transparente Reaktion bei fehlschlagendem Tool-Call, verhält sich GPT-5.4 produktionsgerecht. Es halluziniert keinen Seiteninhalt trotz Fehler und kommuniziert den Ausfall ausreichend offen. Das ist ein klar positives Signal für sichere Fehlerpfade.

**Betriebsprofil**

Total: 78.76s. Call 1: 7.97s. Call 2: 4.71s. MCP-Latenz: 0.45s.  
Kosten pro Run: $0.076749.  
Für die gezeigte Leistung: langsam und teuer.

**Fazit & Empfehlung**

Geeignet für überwachte Pipelines mit klar vorgegebenen Fetch-Schritten, guter Retry-Logik und nachgelagerter Validierung der Antwort gegen Tool-Belege. Nicht geeignet für autonome MCP-Orchestrierung, offene Recherchepfade, Compliance-nahe Web-Recherche oder mehrsprachige Such- und Syntheseaufgaben. Wenn Sie dem Modell eine Tool-Infrastruktur übergeben, dann nur in einem eng geführten Rahmen mit externer Kontrolle der Tool-Wahl.