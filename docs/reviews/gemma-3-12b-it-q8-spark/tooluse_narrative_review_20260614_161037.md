**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:10:37


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber ein invalider Tool-Call und ein erkannter Halluzinationsbefund das Vertrauen für unüberwachte MCP-Pipelines begrenzen. Der kombinierte Score ist nur moderat und passt zum Bild: brauchbar unter Guardrails, nicht frei laufend.

**Tool-Execution-Profil**

Mit P1 90.00 zeigt Gemma 3 12B IT grundsätzlich, dass es Tool-Nutzung versteht und operative Schritte ausführen kann. Das reicht aber nicht für ein uneingeschränktes Infrastruktur-Urteil, weil der Tool-Call im Lauf nicht valide war. Für MCP heißt das: Das Modell produziert nicht durchgehend protokollfeste Aufrufe, obwohl es die Aufgabe offenbar meist richtig einordnet.

Bei den Einzeltests zur Werkzeugwahl fehlen Messwerte, daher lässt sich nicht sauber belegen, ob es im Test “Web Search & Tool Selection”, der die Wahl zwischen Suche und direktem Fetch prüft, echte Tool-Intelligenz gezeigt hat oder nur einem Standardmuster folgt. Dasselbe gilt für “URL Construction & Fetch”, das die präzise Herleitung einer Ziel-URL prüft. Ohne diese Daten bleibt der starke P1-Wert nützlich, aber nicht hinreichend belastbar für dynamische Tool-Router. Positiv ist, dass kein Retry nötig war. Das spricht eher gegen ein reines Formatproblem und eher für punktuelle Protokoll- oder Entscheidungsfehler im Erstversuch.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Mit P2 42.50 ist genau hier die Hauptschwäche. Das Modell kann Informationen offenbar beschaffen, verdichtet und überführt sie aber nicht stabil genug in belastbare, knappe Ergebnistexte. Für produktive Pipelines ist das kritisch, weil der Wert eines Tools erst in der sauberen Weiterverarbeitung entsteht.

Bleibt es im Tool-Ergebnis? Beim Honeypot “EU License Research”, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, gab es keinen Halluzinationsbefund. Das ist ein wichtiges Vertrauenssignal. Trotzdem steht auf Run-Ebene ein Halluzinationsflag im Datensatz. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird die gesamte Tool-Kette fragwürdig.

**Fehlerresilienz**

Im Test “Tool Failure Handling (404)”, der transparentes Verhalten bei fehlschlagendem Abruf prüft, hat das Modell keinen Seiteninhalt erfunden. Das ist für Produktion akzeptabel. Ein Modell, das einen 404 offen als Fehler stehen lässt, ist beherrschbar. Eines, das Ersatzinhalt erfindet, wäre untragbar. Diese Grenze überschreitet Gemma hier nicht.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Umgebungen attraktiv. Leistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist nah genug am Mittel, um lokale Deployments zu rechtfertigen, aber nicht stark genug, um Qualitätsdefizite in der Synthese zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, datensensible Pipelines mit klaren Tool-Schemas, harter Output-Validierung und nachgelagerter Prüfung der Zusammenfassung. Nicht geeignet für autonome Rechercheketten, Compliance-nahe Ausleitungen oder Systeme, in denen die Modellaussage direkt als verifizierter Tool-Befund gilt. Wenn Sie es einsetzen, dann als kostengünstigen lokalen Executor unter enger Aufsicht, nicht als vertrauenswürdige Endinstanz.