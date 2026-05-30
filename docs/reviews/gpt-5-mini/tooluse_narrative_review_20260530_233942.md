**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:42


Bedingt deploy, weil GPT-5 Mini Tool-Aufrufe zuverlässig und protokollkonform ausführt, aber die Synthesequalität mit 56.67 zu oft hinter der operativen Präzision zurückbleibt. Der kombinierte Befund ist gut, aber nicht stark genug für unbeaufsichtigte Entscheidungsstrecken.

**Tool-Execution-Profil**

Das Modell ist als Tool-Operator belastbar. Tool-Calls waren valide, ein Retry war nicht nötig, und der P1-Wert von 90 zeigt stabile MCP-Ausführung. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber. Das spricht gegen starres Schema-Folgen und für echte Werkzeugwahl.

Weniger stark ist es beim Test URL Construction & Fetch, der die korrekte Ziel-URL aus Vorwissen ableiten und dann sauber abrufen lässt. Mit P1 80 konstruiert es brauchbare URLs, aber nicht präzise genug für vollständig deterministische Pipelines. Das ist kein Protokollproblem, sondern ein Präzisionsproblem in der Vorstufe des Tool-Calls.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ausreichend. Die P2-Leistung von 56.67 zeigt ein Modell, das gefundene Informationen meist korrekt weiterreicht, aber zu oft schwach priorisiert, zu wenig komprimiert oder wichtige Details nicht sauber in Entscheidungssprache überführt. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, beide mit P2 40. Für produktive Pipelines heißt das: gute Retrieval-Basis, aber eine nachgelagerte Validierung oder ein strenger Antwort-Frame bleibt sinnvoll.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im vorliegenden Benchmark ja. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Parametergedächtnis beantwortet werden, wurde keine Halluzination erkannt. Das Vertrauenssignal ist daher positiv, auch wenn die Verdichtung des Materials schwach war.

**Fehlerresilienz**

Akzeptabel für Produktion. Beim Test Tool Failure Handling (404), der transparente Reaktion auf einen fehlschlagenden Abruf misst, hat das Modell keinen Seiteninhalt erfunden. P2 60 ist sprachlich nicht stark, aber operativ zählt hier vor allem das Verhalten: Es bleibt bei dem tatsächlichen Fehlerzustand und ersetzt fehlende Daten nicht durch erfundene Inhalte.

**Betriebsprofil**

Call 1: 3.56s. MCP-Latenz: 0.89s. Call 2: 20.33s. Total: 148.69s. Langsam für die gezeigte Endqualität. Kosten pro Run: 0.011345. Günstig bis moderat bepreist, aber die Laufzeit drückt die Wirtschaftlichkeit.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell Tools auswählen, valide aufrufen und Fehler sauber offenlegen muss: Recherche-Workflows, Assistenzsysteme, kontrollierte Informationsbeschaffung. Nicht die erste Wahl für Compliance-nahe oder managementtaugliche Endausgaben, wenn die Antwort ohne menschliche Nachsicht direkt aus Tool-Ergebnissen verdichtet werden soll. Setze es als verlässlichen Tool-Bediener ein, nicht als letzte Instanz für präzise Synthese.