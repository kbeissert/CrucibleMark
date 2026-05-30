**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:47:38


Bedingt deploy, weil GPT-5 valide Tool-Calls erzeugt und nicht halluziniert, aber die Synthesetreue für produktive Tool-Pipelines zu inkonsistent bleibt. Der Gesamteindruck ist gut, das Vertrauen in die Verdichtung der Tool-Ergebnisse aber nur eingeschränkt belastbar.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die stärkere Seite dieses Modells. Mit P1 85.83 wählt GPT-5 in den meisten Fällen das passende Werkzeug und bleibt MCP-konform. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheidet, zeigt es echte Werkzeugwahl statt reiner Schablonen-Nutzung, aber nicht durchgehend sicher. Beim URL-Construction-Test, der korrekte Ziel-URLs aus Vorwissen ableitet und danach fetch verlangt, arbeitet es brauchbar, jedoch nicht deterministisch genug für fragile Pipelines.

Wichtig ist das Retry-Signal. Da der Tool-Call am Ende valide war, spricht das eher für ein Format- oder Ablaufproblem als für ein Verständnisproblem. Für produktive Umgebungen heißt das: orchestrierbar, aber nicht ohne robustes Retry-Handling und klare Tool-Schemas.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mäßig. P2 56.67 ist für ein Frontier-Generalisten zu schwach, wenn die Pipeline nicht nur richtige Calls, sondern belastbare Ergebniszusammenfassungen braucht. Die Spannweite über die Assets ist auffällig: HTTP Fetch & Extract ist mit 80 solide, Multilingual Search & Synthesis mit 60 noch brauchbar. EU License Research und Tool Failure Handling bleiben mit 40 klar unter Produktionsanspruch, sobald exakte Verdichtung oder strikte Ergebnisbindung nötig ist.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, halluziniert GPT-5 nicht. Das ist das zentrale Vertrauenssignal. Der schwache P2-Wert zeigt also keine erfundenen Inhalte, sondern unpräzise oder unvollständig gebundene Verdichtung.

**Fehlerresilienz**

Beim 404-Test, der das Verhalten nach fehlschlagendem Tool-Call misst, bleibt GPT-5 transparent und erfindet keinen Seiteninhalt. Das ist für Produktion akzeptabel. Der P2-Wert von 40 zeigt aber, dass die Kommunikation im Fehlerfall nicht knapp und sauber genug geführt wird. Als Sicherheitsprofil ist das in Ordnung. Als Operator-Experience ist es verbesserungsbedürftig.

**Betriebsprofil**

6.88s erster Call, 23.18s zweiter Call, 188.78s gesamt. Langsam.  
$0.077128 pro Run. Für Frontier-Klasse günstig bis moderat.  
Im Verhältnis zur Leistung: Tool-Use wirtschaftlich, End-to-End-Laufzeit hoch.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit robuster Orchestrierung, Retry-Logik und nachgelagerter Validierung der Antwortschicht. Besonders sinnvoll dort, wo sichere Tool-Nutzung wichtiger ist als knappe, präzise Verdichtung, etwa bei Recherche-Workflows mit menschlicher Abnahme oder mit zusätzlichem Structured Output Check. Nicht die erste Wahl für Compliance-, Audit- oder vollautomatisierte Entscheidungsstrecken, in denen die Antwort strikt und verlustarm an Tool-Ergebnisse gebunden bleiben muss.