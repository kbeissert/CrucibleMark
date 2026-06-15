**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:06:47


Bedingt deploy, weil die Tool-Ausführung stark ist, das Modell valide MCP-Calls produziert, aber die erkannte Halluzination bei nur mäßiger Gesamtsynthese das Vertrauensmodell einer produktiven Tool-Pipeline beschädigt.

**Tool-Execution-Profil**

Das operative Signal ist zunächst gut: P1 liegt bei 90.00, der Tool-Call war valide, und es war kein Retry nötig. Das spricht dafür, dass gemma3:4b das MCP-Protokoll sauber bedient und Aufrufe formal zuverlässig absetzt. Für eine Nano-Klasse ist das ein belastbarer Befund. Es reduziert Integrationsrisiken auf der Transport- und Formatseite.

Nicht beurteilbar ist allerdings, ob das Modell echte Werkzeugintelligenz zeigt oder nur ein stabiles Standardmuster abfährt. Für die Tests Web Search & Tool Selection, also die Entscheidung zwischen Suche und direktem Abruf, sowie URL Construction & Fetch, also die präzise Herleitung einer Ziel-URL vor dem Abruf, liegen keine Daten vor. Damit bleibt offen, ob es in dynamischen Pipelines aktiv das richtige Werkzeug wählt oder nur dann gut funktioniert, wenn die Orchestrierung die Entscheidung bereits vorgibt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Mit P2 von 40.83 liegt die Verdichtungsqualität klar unter dem Niveau, das man für präzise produktive Nachverarbeitung erwartet. Das Modell kann offenbar Ergebnisse einsammeln und formal weiterreichen, aber die eigentliche Transformation in eine verlässliche, knappe Arbeitsantwort ist das schwächere Glied.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu gibt es für EU License Research keine Einzeldaten, aber der Halluzinations-Flag steht auf true. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-basiertes Ergebnis präsentiert, verliert die gesamte Pipeline ihre Auditierbarkeit. Für Compliance-, Legal- oder Policy-Flows ist das ein harter Vorbehalt.

**Fehlerresilienz**

Für den 404-Test, also den Umgang mit einem bewusst scheiternden Tool-Aufruf, liegen keine Daten vor. Deshalb gibt es keinen Nachweis, dass gemma3:4b Fehler transparent meldet, statt Ersatzinhalt zu erfinden. Gerade wegen des gesetzten Halluzinations-Flags muss diese Lücke konservativ gelesen werden. Ohne belegte Fehlerdisziplin ist ein breiter Produktionseinsatz riskant.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments operativ attraktiv. Gleichzeitig liegt das Modell 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist kein Ausfall, aber auch kein Beleg dafür, dass lokale Ausführung hier ohne deutlichen Qualitätskompromiss gelingt.

**Fazit & Empfehlung**

Geeignet ist gemma3:4b für lokal betriebene, eng geführte Pipelines mit klar vorgegebener Tool-Nutzung, niedriger inhaltlicher Kritikalität und nachgelagerter Validierung. Nicht geeignet ist es für autonome Rechercheketten, Compliance-nahe Entscheidungen oder Workflows, in denen die Antwort selbst als vertrauenswürdige Verdichtung der Tool-Ausgaben dienen muss. Wer dieses Modell einsetzt, sollte die Tool-Orchestrierung extern hart steuern und jede inhaltliche Synthese gegen Primärdaten prüfen.