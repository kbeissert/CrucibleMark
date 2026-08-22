**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:49:21


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die erkannte Halluzination bei zugleich nicht validem Tool-Call das Vertrauen für kritische Produktionspipelines bricht.

**Tool-Execution-Profil**

Kimi K2.5 zeigt klare Orchestrierungsstärke. Es wählt im Test Web Search & Tool Selection, der ohne expliziten Hinweis die richtige Entscheidung zwischen Suche und Fetch verlangt, das passende Werkzeug sicher aus. Das spricht gegen starres Musterverhalten und für echte Werkzeugwahl im Ablauf. Auch bei Multilingual Search & Synthesis und EU License Research liegt P1 bei 100, also bei der Auslösung der richtigen Recherchekette.

Schwächer ist die zweite Hälfte der Ausführung: Der Tool-Call war insgesamt nicht valide. Das passt zum Ergebnis aus URL Construction & Fetch, wo das Modell die Ziel-URL aus eigenem Wissen brauchbar, aber nicht präzise genug für deterministische Pipelines konstruiert. Für MCP-Umgebungen heißt das: Planung und Tool-Auswahl sind belastbar, die Protokoll- und Parameterpräzision nicht durchgehend. Retry war nicht erforderlich. Das wirkt daher weniger wie ein Formatkollaps, sondern eher wie ein punktuelles Ausführungsproblem in der letzten Meile.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 65.83 ist für ein Frontier-Modell mit agentischem Schwerpunkt zu niedrig, um als verlässliche Verdichtungsinstanz zu gelten. Positiv sind HTTP Fetch & Extract sowie Tool Failure Handling (404), wo extrahierte Inhalte sauber zusammengeführt werden. Negativ fällt EU License Research stark ab, und auch bei URL Construction & Fetch bleibt die Synthese zu unpräzise.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht konsistent. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, halluziniert das Modell und erreicht nur P2=35. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder aus dem Training rekonstruierte Fakten als Ergebnis einer Tool-Pipeline ausgibt, unterläuft es die Verifizierbarkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Bei Tool Failure Handling (404), das den Umgang mit einem fehlschlagenden Aufruf misst, reagiert Kimi K2.5 produktionsnah. Es kommuniziert den Fehler transparent und halluziniert keinen Ersatzinhalt. Das ist für reale Pipelines akzeptabel und spricht dafür, dass Ausfälle nicht automatisch in falsche Antworten umschlagen.

**Betriebsprofil**

Call 1: 4.10s. Call 2: 44.47s. MCP-Latenz: 0.91s. Total pro Run: 296.87s. Langsam für den erzielten Nutzwert. Kosten: local.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Routing-Pipelines, in denen Tool-Auswahl wichtiger ist als die finale Faktensynthese und in denen nachgelagerte Validatoren jede Aussage prüfen. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere High-Trust-Pipelines, in denen Tool-Ergebnisse strikt belegt bleiben müssen. Wer Kimi K2.5 einsetzt, sollte es als Orchestrator mit harter Output-Kontrolle verwenden, nicht als letzte wahrheitsstiftende Instanz.