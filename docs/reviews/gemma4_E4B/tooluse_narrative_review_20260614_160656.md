**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:06:56


Bedingt deploy, weil das Modell valide Tool-Calls erzeugt, keine Halluzination erkannt wurde und der Gesamteindruck mit 74.67 solide ist, die Synthesequalität mit P2 60.00 für entscheidungsrelevante Ausgaben aber zu inkonsistent bleibt.

**Tool-Execution-Profil**

Die stärkste Eigenschaft dieses Modells ist die operative Tool-Nutzung. P1 90.00, valider Tool-Call und kein erforderlicher Retry sprechen dafür, dass es MCP-konform arbeitet und Aufrufe formal sauber übergibt. Das ist für eine Tool-Pipeline die erste Eintrittshürde, und die nimmt gemma4:E4B.

Was fehlt, ist Sicht auf die eigentliche Werkzeugwahl. Für den Web-Search-and-Tool-Selection-Test, der prüft ob das Modell zwischen Suche und direktem Fetch unterscheiden kann, liegen keine Daten vor. Ebenso fehlen Daten aus dem URL-Construction-and-Fetch-Test, der die Präzision selbst abgeleiteter Ziel-URLs misst. Deshalb lässt sich nicht belastbar sagen, ob das Modell situativ das richtige Werkzeug wählt oder primär einem festen Muster folgt. Für statische Pipelines mit vorgegebener Tool-Reihenfolge ist das akzeptabel. Für dynamische Orchestrierung bleibt ein offenes Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 60.00 zeigt, dass die Verdichtung funktional sein kann, aber nicht konstant präzise genug für Antworten, die mehrere Tool-Ergebnisse priorisieren, gegeneinander abwägen oder in belastbare Handlungsanweisungen übersetzen müssen. Für einfache Extraktion und kurze Zusammenfassungen reicht das eher aus als für Analysten-Outputs.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu gibt es aus dem Honeypot EU License Research keine Detaildaten. Positiv ist nur das globale Signal: keine erkannte Halluzination. Das stützt ein vorsichtiges Vertrauensurteil, ersetzt aber keinen echten Compliance-Nachweis. Für regulatorische oder lizenzbezogene Pipelines ist diese Lücke relevant.

**Fehlerresilienz**

Zum 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Aufruf prüft, liegen keine Daten vor. Deshalb ist die wichtigste Produktionsfrage offen: bricht das Modell sauber mit einer nachvollziehbaren Fehlermeldung ab, oder kompensiert es einen Fehler mit plausibel klingendem Ersatzinhalt? Solange das nicht getestet ist, sollte man es nicht ohne Guardrails in autonome Retrieval-Ketten setzen. Ein hartes Fehler-Handling außerhalb des Modells bleibt Pflicht.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Mit einem Sovereignty Gap von -1.37 Punkten unter dem Fleet-Ø von 67.84 bleibt es dabei nahezu fleet-kompetitiv. Für ein Nano-Generalistenmodell ist das ein gutes Verhältnis aus Kontrollierbarkeit und Nutzwert.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne MCP-Pipelines mit klar vorgegebenen Tools, enger Aufgabenstruktur und nachgelagerter Validierung. Gut einsetzbar für Extraktion, einfache Rechercheketten und assistive Operator-Workflows. Nicht die richtige Wahl für autonome Tool-Auswahl, compliance-nahe Recherche oder Synthesen, aus denen direkt operative Entscheidungen abgeleitet werden. Dafür fehlt vor allem belastbare Evidenz bei Werkzeugwahl, Fehlerverhalten und vertrauensharter Verdichtung.