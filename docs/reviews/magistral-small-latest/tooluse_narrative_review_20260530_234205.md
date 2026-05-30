**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:05


Nicht deploy, weil das Modell trotz Tool-Kontext halluziniert, keine durchgängig validen Tool-Calls erzeugt und mit einem Combined-Score von 48.21 die Vertrauensschwelle für produktive MCP-Pipelines verfehlt.

**Tool-Execution-Profil**

Magistral Small zeigt kein verlässliches Werkzeugurteil. Beim Web-Search-and-Tool-Selection-Test, der prüft ob das Modell ohne Hinweis zwischen Suche und direktem Abruf unterscheidet, fällt es mit P1 35 klar ab. Beim URL-Construction-and-Fetch-Test, der die Ableitung einer Ziel-URL aus Vorwissen misst, arbeitet es mit P1 80 deutlich besser. Das spricht nicht für robuste Tool-Intelligenz, sondern für ein engeres Muster: Wenn eine Zieladresse direkt konstruierbar ist, funktioniert der Ablauf oft; wenn zuerst das richtige Werkzeug gewählt werden muss, bricht die Qualität ein.

Der invalide Tool-Call und der erforderliche Retry deuten eher auf ein Protokoll- und Ausführungsproblem als auf reines Antwortformat hin. Für MCP-Betrieb ist das kritisch, weil der Orchestrator dann zusätzlichen Korrekturaufwand tragen muss. Positiv ist nur, dass HTTP Fetch & Extract mit P1 75 solide zeigt, dass das Modell vorhandene Inhalte grundsätzlich verarbeiten kann.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung von 33.33 zeigt, dass das Modell gefundene Inhalte nur unzuverlässig in belastbare Antworten überführt. Das sieht man auch an den Ausreißern: HTTP Fetch & Extract gelingt mit P2 80, aber EU License Research und Multilingual Search & Synthesis fallen auf P2 0. Es extrahiert punktuell, verdichtet aber nicht stabil über Aufgabenklassen hinweg.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Beim EU-License-Research-Honeypot, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, erreicht das Modell P2 0 bei erkanntem Halluzinationsbefund. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Ein Modell, das erfundene oder unbestätigte Fakten als Werkzeugergebnis ausgibt, beschädigt das Vertrauen in die gesamte Tool-Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf gescheiterte Abrufe misst, halluziniert Magistral Small keinen Seiteninhalt. Das ist der wichtigste positive Befund. Die Kommunikation bleibt aber nur teilweise brauchbar, was sich in P2 40 zeigt. Für Produktion ist das akzeptabel, solange der Orchestrator Fehlerzustände strikt behandelt und keine stillschweigende Weiterverarbeitung zulässt.

**Souveränitätsprofil**

Lokal souverän einsetzbar, aber nicht fleet-kompetitiv. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Für lokale Bereitstellung ist das Profil nur dann interessant, wenn Datenhoheit wichtiger ist als Tool-Zuverlässigkeit.

**Fazit & Empfehlung**

Geeignet höchstens für interne Assistenz-Pipelines mit hartem Guardrailing, strikt erzwungener Tool-Validierung und menschlicher Freigabe vor jeder externen Wirkung. Nicht geeignet für Compliance-, Research-, Retrieval- oder mehrsprachige MCP-Pipelines, in denen das Modell Werkzeuge selbst wählen, Ergebnisse belastbar verdichten oder aktuelle Web-Fakten korrekt wiedergeben muss. Für produktive Tool-Infrastruktur fehlt vor allem eines: Vertrauenstreue gegenüber den tatsächlich abgerufenen Quellen.