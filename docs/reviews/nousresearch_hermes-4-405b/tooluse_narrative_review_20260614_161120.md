**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:11:20


Bedingt deploy, weil Hermes 4 405B die Tool-Infrastruktur zuverlässig bedient und keine Halluzination im Lauf gezeigt hat, aber die Verdichtung der Tool-Ergebnisse für produktionskritische Synthese zu ungenau bleibt.

**Tool-Execution-Profil**

Das Modell ist stark auf der Ausführungsseite. Die Tool-Calls waren valide, MCP-konform und ohne Retry lauffähig. Das ist für eine Pipeline wichtiger als sprachliche Eleganz. Beim Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erkennt Hermes 4 405B die richtige Werkzeugklasse sicher. Das spricht gegen ein starres Abrufmuster und für echte Werkzeugwahl. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Modellwissen plus anschließendem Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug für fragile Endpunkte. Das Muster ist klar: gute Auswahl des Werkzeugtyps, etwas schwächere Präzision bei selbst abgeleiteten Zieladressen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 von 60 zeigt ein Modell, das gefundene Informationen oft korrekt weiterträgt, aber in mehreren Aufgaben zu grob zusammenfasst. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo die Recherche funktioniert, die Verdichtung jedoch wichtige Einschränkungen und Nuancen nicht zuverlässig konserviert. Für Search-then-answer reicht das oft. Für Compliance, Policy oder exakte Entscheidungsunterlagen reicht es nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, und das ist der wichtigere Vertrauensbefund. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, lag keine Halluzination vor. Trotz schwacher Synthese blieb das Modell also im beschafften Evidenzraum. Das ist ein tragfähiges Signal für Tool-Vertrauen.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call statt erfundenem Seiteninhalt misst, kommuniziert Hermes 4 405B den Fehler sauber und halluziniert keinen Ersatzinhalt. Genau dieses Verhalten schützt nachgelagerte Systeme vor stillen Faktenfehlern.

**Betriebsprofil**

Total 38.22s pro Run. Tool-Aufruf 1.21s, MCP-Latenz 0.94s, zweiter Modellaufruf 4.22s. Damit operativ eher langsam. Kosten pro Run 0.006770. Damit für ein 405B-Modell günstig bis sehr gut vertretbar.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen saubere Tool-Nutzung, robuste Fehlerbehandlung und offene Gewichte wichtiger sind als präzise Ergebnisverdichtung. Gute Passform für Recherche-Orchestrierung, Retrieval mit menschlicher Nachsicht und agentische Vorstufen. Nicht die erste Wahl für Compliance-Ausgaben, mehrsprachige Executive Summaries oder jede Pipeline, in der die Antwort direkt als belastbare Endfassung verwendet wird. Hier sollte ein strenger Verifier oder ein zweites Synthese-Modell nachgeschaltet werden.