**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:00:35


Bedingt deploy, weil es zuverlässig valide Tool-Calls produziert und nicht halluziniert, aber die Synthesetreue für produktionskritische Verdichtung noch zu ungleichmäßig ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist für ein Nano-Modell klar brauchbar. Das Modell erzeugt valide MCP-konforme Aufrufe und liegt in Tool Execution auf starkem Niveau. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis prüft, ob web_search statt fetch nötig ist, erkennt es den richtigen Werkzeugtyp sehr sicher. Das spricht gegen bloßes Schema-Folgen und für echte Werkzeugwahl im gegebenen Kontext.

Weniger robust ist es beim URL-Construction-Test, der prüft, ob das Modell die Ziel-URL aus eigenem Wissen ableitet und dann korrekt fetched. Dort ist die Ausführung brauchbar, aber nicht präzise genug für vollständig deterministische Flows. Das Muster ist klar: starke Auswahl des Werkzeugtyps, schwächere Präzision bei der konkreten Parametrisierung. Dass ein Retry nötig war, wirkt hier eher wie ein Format- oder Ausführungsproblem als ein Verständnisfehler. Das ist operativ beherrschbar, aber in engen Tool-Loops relevant.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht verlässlich scharf genug. Die P2-Leistung zeigt brauchbare Verdichtung bei HTTP Fetch & Extract, Tool Failure Handling (404) und URL Construction & Fetch, fällt aber bei EU License Research und besonders bei Multilingual Search & Synthesis deutlich ab. Für Pipelines, in denen das Modell Ergebnisse nur knapp zusammenfassen soll, reicht das. Für Compliance, Research-Exports oder mehrsprachige Ergebnisfusion ist es zu inkonsistent.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Vertrauenssignal intakt: keine Halluzination, Content-Verification-State A. Das Modell ist also nicht der Typ, der bei fehlender Sicherheit stillschweigend Weltwissen als Tool-Befund ausgibt. Das ist für Produktionsvertrauen wichtiger als die nur mittlere Verdichtungsqualität.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der misst, ob ein fehlschlagender Tool-Call transparent kommuniziert oder Ersatzinhalt erfunden wird, bleibt das Modell sauber. Es halluziniert keinen Seiteninhalt trotz Fehler und behandelt den Ausfall nachvollziehbar. Genau dieses Verhalten schützt Tool-Pipelines vor stillen Faktenfehlern.

**Souveränitätsprofil**

Voll lokal betreibbar, Apache-2.0-lizenziert und damit souverän gut integrierbar. Leistungsseitig liegt es nur 0.75 Punkte unter dem Fleet-Ø von 66.55. Für einen lokal laufenden 4B-Dense-Generalisten ist das ein belastbares Ergebnis.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit klaren Tools, moderatem Syntheseanspruch und hoher Priorität auf Datenhoheit. Gut einsetzbar für Recherche-Orchestrierung, Web-Zugriff, Fehlertransparenz und einfache Extraktionsjobs. Nicht die richtige Wahl für Pipelines, in denen die Endantwort selbst hochpräzise, mehrsprachig konsolidiert oder compliance-nah formuliert werden muss. Als Tool-Operator ja. Als letzte redaktionelle Instanz eher nein.