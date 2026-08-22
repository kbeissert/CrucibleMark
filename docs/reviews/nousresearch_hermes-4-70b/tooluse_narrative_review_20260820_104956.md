**Deployment-Urteil**

> **Erstellt am:** 20.08.2026, 10:49:56


Bedingt deploy, weil die Tool-Ausführung stark ist, aber ein ungültiger Tool-Call und erkannte Halluzination das Vertrauen in produktive MCP-Pipelines begrenzen. Der Gesamteindruck ist gut, aber nicht robust genug für unbeaufsichtigte High-Trust-Strecken.

**Tool-Execution-Profil**

Hermes 4 70B zeigt klare Tool-Intelligenz bei der Auswahl des richtigen Werkzeugs. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis statt fetch eine Suche nötig ist, erkennt das Modell den richtigen Zugriffspfad zuverlässig. Das spricht gegen starres Musterverhalten und für echte Situationsanpassung. Auch bei EU License Research und Multilingual Search & Synthesis greift es operativ sicher zu.

Schwächer ist die Protokollpräzision. Der Status „Tool-Call valide: false“ und das Ergebnis im Test URL Construction & Fetch zeigen, dass die Ableitung einer Ziel-URL aus Eigenwissen nicht deterministisch genug ist. Für MCP-Pipelines heißt das: Die Werkzeugwahl ist meist richtig, aber die konkrete Ausführung bleibt fehleranfällig, wenn der Pfad nicht schon durch die Tooling-Schicht abgesichert ist. Positiv ist, dass kein Retry erforderlich war. Das Problem liegt also eher in der Erstpräzision als in wiederholtem Formatversagen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Qualität ist mit 41.67 der klare Schwachpunkt dieses Modells. Besonders auffällig ist Multilingual Search & Synthesis: Die Recherche gelingt, aber die Verdichtung auf Deutsch bricht stark ein. Hermes kann also Informationen beschaffen, verliert aber bei der Zusammenführung an Präzision und Priorisierung. Für Architekturen, in denen das Modell nicht nur findet, sondern belastbar zusammenfassen muss, ist das ein reales Produktionsrisiko.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt Hermes auf der Tool-Spur und halluziniert dort nicht. Das ist ein wichtiges Vertrauenssignal. Gleichzeitig gilt der globale Halluzinationsbefund als Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Werkzeugergebnis ausgibt, beschädigt es die Vertrauenskette der gesamten Tool-Infrastruktur.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Test Tool Failure Handling (404), der transparentes Verhalten bei fehlschlagendem Fetch prüft, kommuniziert Hermes den Fehler sauber und erfindet keinen Ersatzinhalt. Genau dieses Verhalten ist in produktiven Pipelines erforderlich, weil Orchestrierung nur mit ehrlichen Fehlerzuständen zuverlässig reagieren kann.

**Souveränitätsprofil**

Lokal betreibbar und fleet-kompetitiv. Der Combined-Score liegt bei 75.50, der Sovereignty Gap damit n/a-Punkte unter dem Fleet-Ø von 67.19.

**Fazit & Empfehlung**

Geeignet für lokal betriebene MCP-Pipelines, in denen das Modell primär Werkzeuge auswählt, Suchpfade eröffnet und Ergebnisse mit nachgelagerter Validierung weiterreicht. Nicht geeignet als alleinige Synthese- und Vertrauensinstanz für Compliance, mehrsprachige Rechercheverdichtung oder deterministische Fetch-Strecken mit fragiler URL-Konstruktion. Empfehlenswert ist Hermes 4 70B als orchestrierendes Frontmodell mit strikter Tool-Schema-Validierung, Output-Checks und einem zweiten Prüfschritt für finale Antworten.