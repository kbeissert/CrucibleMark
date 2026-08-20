**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:19:56


Bedingt deploy, weil das Modell trotz gutem Gesamtergebnis von 70.33 keinen durchgängig validen Tool-Call-Verlauf zeigt und damit für MCP-Pipelines nur unter enger Laufzeitkontrolle tragfähig ist.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl-Intelligenz, aber keine Protokollsicherheit auf konstantem Produktionsniveau. Beim Test **Web Search & Tool Selection**, der prüft, ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, wählt es das richtige Werkzeug souverän. Das spricht gegen starres Musterverhalten. Auch beim Test **Multilingual Search & Synthesis** agiert es tool-seitig sicher. Schwächer wird es bei der Ausführung: Beim Test **URL Construction & Fetch**, der korrekte URL-Ableitung plus sauberen Abruf misst, ist die Leistung brauchbar, aber nicht deterministisch. **HTTP Fetch & Extract** bestätigt dieses Bild. Der Abruf klappt oft, die Präzision im Ablauf nicht immer. Kritisch ist der Befund `tool_call_valid: false`. Das ist kein Hinweis auf fehlendes Planen, sondern auf mangelnde MCP-Verlässlichkeit im letzten Meter. Für orchestrierte Tool-Ketten ist genau dieser letzte Meter entscheidend.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Signale liegen in mehreren Aufgaben bei 40, darunter **EU License Research** und **HTTP Fetch & Extract**, also genau dort, wo präzise Verdichtung von abgerufenen Fakten erwartet wird. Dagegen sind **Web Search & Tool Selection**, **URL Construction & Fetch** und **Multilingual Search & Synthesis** in der Zusammenführung klar stärker. Das Muster ist deutlich: gute Rechercheführung, schwankende Verdichtungsdisziplin.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, halluziniert es nicht. Das ist der wichtigste Vertrauensbefund. Das Modell driftet also nicht sichtbar in frei erfundene Compliance-Antworten ab, auch wenn die Verdichtung zu flach bleibt.

**Fehlerresilienz**

Beim Test **Tool Failure Handling (404)**, der transparentes Verhalten bei einem fehlgeschlagenen Abruf misst, erfindet das Modell keinen Ersatzinhalt. Das ist akzeptabel für Produktion. Die Antwortqualität bleibt mit P2 40 jedoch knapp. Es bleibt also eher defensiv als wirklich robust. Für Pipelines ist das besser als kreative Fehlerkompensation.

**Betriebsprofil**

Total 116.58s. Call 1 2.87s. MCP-Latenz 2.18s. Call 2 14.38s. Langsam für den gezeigten Nutzwert. Kosten pro Run: local.

**Fazit & Empfehlung**

Geeignet für überwachte Agenten-Pipelines, in denen Tool-Wahl, Rechercheplanung und mehrsprachige Suche wichtiger sind als strikt deterministische MCP-Ausführung. Nicht geeignet für Compliance-, Registry- oder ETL-Pipelines, in denen jeder Tool-Call formal gültig sein und jede Verdichtung eng am abgerufenen Inhalt bleiben muss. Wer es einsetzt, sollte harte Tool-Call-Validierung, Output-Schema-Prüfung und einen nachgelagerten Verifier verpflichtend machen.