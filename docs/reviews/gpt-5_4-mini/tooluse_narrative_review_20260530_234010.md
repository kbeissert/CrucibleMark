**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:10


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Tool-Calls valide sind und keine Halluzination erkannt wurde, die Synthesequalität mit Combined 71.08 aber zu ungleich für vertrauensarme Produktionspfade ausfällt.

**Tool-Execution-Profil**

GPT-5.4 Mini zeigt ein starkes operatives Tool-Profil. Es wählt Werkzeuge nicht rein schematisch, sondern erkennbar aufgabenbezogen: Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis eher Suche als direkter Fetch nötig ist, arbeitet es mit P1=100 sicher. Das spricht für echte Werkzeugwahl statt starrem Fetch-Reflex. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es mit P1=80 brauchbar, aber nicht deterministisch genug für Pfade, in denen die URL-Konstruktion selbst geschäftskritisch ist. Tool-Calls sind insgesamt valide und MCP-konform. Der erforderliche Retry wirkt daher eher wie ein Format- oder Ablaufproblem im ersten Versuch, nicht wie ein Verständnisfehler über das passende Werkzeug.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2=56.67 zeigt, dass das Modell gefundene Inhalte nicht konsistent in präzise, belastbare Ergebnistexte überführt. Die Spannweite ist hoch: HTTP Fetch & Extract gelingt mit P2=100 sehr gut, sobald sauberer Quelltext vorliegt. EU License Research fällt mit P2=20 deutlich ab. Für Produktionssysteme heißt das: Es kann Fakten aus Tools ziehen, verliert aber bei verdichtender Einordnung schneller Präzision als seine P1-Leistung erwarten lässt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Grundsätzlich ja, mit Vorbehalt. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist das entscheidende Vertrauenssignal. Der Content-Verification-State B2 und die sehr schwache P2 zeigen aber, dass es eher defensiv oder unvollständig zusammenfasst als robust quellennah zu argumentieren.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt misst, halluziniert das Modell nicht. P2=60 ist kein Starkwert, aber die Priorität stimmt: Es bleibt bei der Fehlersituation und erfindet keinen Ersatzinhalt. Für orchestrierte Pipelines ist das deutlich wichtiger als stilistische Vollständigkeit.

**Betriebsprofil**

Call 1: 2.50s. MCP-Latenz: 1.35s. Call 2: 3.28s. Total: 42.81s. Kosten pro Run: 0.018911 USD. Operative Bewertung: eher langsam im End-to-End-Lauf, aber günstig. Preis-Leistung ist solide, wenn die Pipeline Synthese nachgelagert absichert.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell primär Tools auswählt, valide Aufrufe erzeugt und Rohresultate an nachgelagerte Validatoren oder regelbasierte Verdichtung übergibt. Weniger geeignet für Compliance-, Policy- oder Research-Flows, in denen die erste modellseitige Zusammenfassung selbst als belastbares Arbeitsergebnis dienen muss. Deploy als Tool-Operator, nicht als letzte Instanz für inhaltliche Verdichtung.