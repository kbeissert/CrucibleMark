**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:21:29


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber ein invalides Tool-Call-Signal und erkannte Halluzinationen das Vertrauen in eine produktive MCP-Pipeline begrenzen.

**Tool-Execution-Profil**

Das Modell zeigt mit P1 90.00 klar, dass es Tool-Nutzung grundsätzlich beherrscht. Das ist für ein Reasoning-Modell dieser Klasse positiv, weil es nicht nur plant, sondern Werkzeuge auch praktisch einsetzt. Der kritische Bruch liegt im Protokollsignal: Der Tool-Call war nicht valide. Das ist kein kosmetischer Fehler. In MCP-Pipelines bedeutet ein invalider Call, dass Orchestrierung, Parsing oder Folgeaktionen abbrechen können, obwohl die inhaltliche Absicht richtig war.

Zu den Auswahltests liegt keine aufgeschlüsselte Einzelwertung vor. Deshalb lässt sich nicht belastbar sagen, ob das Modell zwischen Web Search & Tool Selection und URL Construction & Fetch intelligent differenziert oder nur einem festen Muster folgt. Für Produktion ist genau diese Unklarheit relevant. Ein Modell kann hohe Tool-Affinität zeigen und trotzdem bei der konkreten Wahl des passenden Werkzeugs unstet sein. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein bloßes Formatproblem und eher für einen punktuellen Validitätsfehler im Call selbst.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 55.83 ist für produktive Synthese niedrig. Das Modell kann Ergebnisse offenbar zusammenführen, aber nicht mit der Präzision, die man für Compliance-, Research- oder Entscheidungsstrecken braucht. Gerade nach erfolgreicher Tool-Nutzung erwartet man eine saubere, knappe und quellennah gebundene Verdichtung. Diese Bindung wirkt hier nicht stabil genug.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb das Modell unauffällig. Das ist ein gutes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird nicht nur eine Antwort schwach, sondern die gesamte Tool-Infrastruktur unzuverlässig.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call prüft, halluzinierte das Modell keinen Ersatzinhalt. Das ist produktionsreif. Es zeigt, dass das Modell Fehler eines Tools als Fehler behandeln kann, statt sie mit erfundenem Seiteninhalt zu kaschieren. Für robuste Pipelines ist das wichtiger als stilistische Antwortqualität.

**Souveränitätsprofil**

Lokal betreibbar als Open-Weights-Modell und damit für souveräne Deployments attraktiv. Kein Sovereignty Gap ausweisbar, Referenz bleibt n/a-Punkte unter dem Fleet-Ø von 67.84.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Assistenz- und Research-Pipelines mit menschlicher Abnahme, Logging und harter Tool-Call-Validierung vor Ausführung. Nicht geeignet für autonom laufende MCP-Strecken, in denen das Modell Tool-Ergebnisse verbindlich zusammenfasst oder ohne Guardrails Folgeaktionen auslöst. Wer es einsetzt, sollte strikt zwischen Tool-Ausführung und finaler Antwortfreigabe entkoppeln.