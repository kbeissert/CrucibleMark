**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:29


Nicht deploy, weil die Tool-Calls nicht valide sind, ein Retry erforderlich war und der kombinierte Befund mit 33.58 klar unter der Schwelle für vertrauenswürdige MCP-Nutzung liegt.

**Tool-Execution-Profil**

Magistral Medium zeigt kein belastbares Tool-Verhalten für produktive Pipelines. Der P1-Wert von 41.67 ist kein reines Präzisionsproblem, sondern ein Orchestrierungsproblem. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis das passende Recherche-Tool erkannt wird, erreicht das Modell nur 35. Dasselbe gilt für URL Construction & Fetch, also den Test, ob es eine Ziel-URL aus eigenem Wissen korrekt ableiten und dann per Fetch abrufen kann. Diese Symmetrie spricht eher für ein starres Muster als für echte Werkzeugintelligenz. Das Modell unterscheidet nicht sauber zwischen Suchbedarf und direktem Abruf.

Dass tool_call_valid=false und retry_required=true gesetzt sind, verschärft das Urteil. Das wirkt weniger wie ein inhaltliches Missverständnis als wie ein Format- und Protokollproblem im MCP-Ablauf. Für eine Tool-Infrastruktur ist genau das kritisch, weil schon der erste Schritt deterministisch sitzen muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Der P2-Wert von 26.67 zeigt, dass Magistral Medium aus abgerufenen Quellen nur unzuverlässig belastbare Antworten formt. Das Bild ist stark uneinheitlich. HTTP Fetch & Extract gelingt noch brauchbar mit 40, und beim 404-Fall verdichtet es den Fehlerzustand sauber mit 80. Dagegen fällt EU License Research auf 0 und Multilingual Search & Synthesis ebenfalls auf 0. Für Pipelines, die Recherche in belastbare Arbeitsantworten übersetzen sollen, ist diese Streuung zu groß.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, halluziniert das Modell zwar nicht offen, aber es liefert trotzdem keine vertrauenswürdige Verdichtung. P2=0 bei Content-Verification-State B2 heißt praktisch: kein nachweislich erfundener Inhalt, aber auch kein belastbarer, quellengebundener Output. Für Compliance-nahe Tool-Pipelines reicht das nicht.

**Fehlerresilienz**

Hier liegt die klare Stärke. Im 404-Test, der prüft ob ein fehlgeschlagener Tool-Call transparent behandelt wird, reagiert Magistral Medium akzeptabel. P2=80 und keine Halluzination trotz Fehler zeigen, dass es Ausfälle offen kommuniziert statt Seiteninhalt zu erfinden. Das ist produktionsfähig. Es kompensiert aber nicht die schwache Erstwahl und die ungültigen Tool-Calls.

**Souveränitätsprofil**

Open-weights und cloud-verfügbar, aber laut Modellkontext nicht lokal ausführbar. Damit ist es für souveräne On-Prem-Pfade nur eingeschränkt relevant. Leistungseitig liegt es 5.32 Punkte unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet allenfalls für beaufsichtigte Pipelines mit enger Tool-Vorlage, starkem Call-Validation-Layer und klarer Fehlerbehandlung. Nicht geeignet für autonome MCP-Flows, dynamische Tool-Auswahl, Compliance-Recherche oder mehrsprachige Web-Synthese. Wer diesem Modell eine Tool-Infrastruktur übergibt, muss die Werkzeugwahl extern erzwingen und die Ausgabe streng gegen Quellen prüfen.