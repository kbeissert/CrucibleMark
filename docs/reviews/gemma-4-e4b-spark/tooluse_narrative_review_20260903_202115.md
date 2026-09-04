**Deployment-Urteil**

> **Erstellt am:** 03.09.2026, 20:21:15


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Halluzinationsbefund und invalidem Tool-Call nicht genügt, um einer produktiven MCP-Pipeline unbeaufsichtigt vertraut zu werden.

**Tool-Execution-Profil**

Gemma 4 E4B versteht grundsätzlich, wann ein externes Werkzeug nötig ist. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählt es das richtige Werkzeug zuverlässig. Das spricht für echte Werkzeugwahl statt bloßem Antwortmuster. Beim Test URL Construction & Fetch, der die Ableitung einer korrekten Ziel-URL aus Eigenwissen prüft, bleibt die Ausführung brauchbar, aber nicht deterministisch genug. Genau dort zeigt sich die Grenze: Das Modell erkennt den Arbeitstyp, verliert aber bei der exakten Parametrisierung an Präzision. Für MCP-Betrieb ist kritischer, dass mindestens ein Tool-Call formal nicht valide war. Das ist kein Planungsproblem, sondern ein Protokollrisiko. Ohne strikte Schema-Validierung und Guardrails produziert das vermeidbare Integrationsfehler.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung zeigt, dass Gemma 4 E4B gefundene Inhalte oft nicht sauber auf Entscheidungsebene komprimiert. Besonders schwach ist Multilingual Search & Synthesis, also die sprachübergreifende Recherche mit deutscher Verdichtung. Auch bei EU License Research und URL Construction & Fetch sinkt die Qualität der Zusammenführung deutlich unter das Niveau der eigentlichen Tool-Nutzung. Das Modell findet also häufiger etwas, als dass es das Gefundene belastbar interpretiert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt es formal im Tool-Pfad und halluziniert dort nicht. Das ist positiv. Der globale Halluzinationsbefund bleibt dennoch ein Sicherheitsrisiko. In einer Tool-Pipeline ist nicht die Stilqualität das Problem, sondern dass erfundene Fakten als abgerufene Fakten erscheinen können. Genau das untergräbt die Vertrauenskette zwischen Modell, Tool und Nutzer.

**Fehlerresilienz**

Beim 404-Test, der die Reaktion auf einen fehlschlagenden Tool-Call misst, reagiert Gemma 4 E4B produktionsnah. Es kommuniziert den Fehler transparent und erfindet keinen Seiteninhalt. Das ist für den Betrieb akzeptabel. Wer Retry- oder Fallback-Logik im Orchestrator hat, kann auf diesem Verhalten aufbauen.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Setups attraktiv. Combined Score 68.92, damit 0.80 Punkte über dem Fleet-Ø von 68.12. Die Leistung ist fleet-kompetitiv, ohne Cloud-Abhängigkeit oder Lizenzblocker.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische Tool-Pipelines mit enger Orchestrator-Kontrolle, insbesondere für Recherche, Vorselektion und robuste Fehlerweitergabe. Nicht geeignet für Compliance-, Policy- oder mehrsprachige Entscheidungsstrecken, in denen die textliche Verdichtung selbst als verlässliches Endprodukt dienen muss. Empfohlen nur mit hartem Tool-Call-Schema, Output-Validierung und einer zweiten Instanz für Verifikation der Synthese.