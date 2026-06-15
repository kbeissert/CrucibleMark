**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:12:12


Bedingt deploy, weil die Tool-Nutzung inhaltlich oft tragfähig ist, aber die Calls nicht durchgehend valide sind und ein Retry erforderlich war. Der Combined-Score von 69.54 reicht für produktive Nebenpfade, nicht für hochgradig deterministische Kernorchestrierung.

**Tool-Execution-Profil**

Qwen 3.7 Max zeigt solides Ausführungsverhalten, sobald der richtige Zugriffspfad feststeht. Bei HTTP Fetch & Extract sowie Tool Failure Handling (404), also bei klar vorgegebenem Tool-Pfad, arbeitet es robust. Auch beim URL-Construction-Test, der prüft ob das Modell die Ziel-URL selbst herleiten und dann korrekt abrufen kann, ist die Leistung brauchbar.

Der Schwachpunkt liegt bei der Werkzeugwahl. Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden lässt, fällt P1 mit 35 deutlich ab. Das spricht gegen verlässliche Tool-Intelligenz in offenen Umgebungen. Das Modell folgt hier eher einem naheliegenden Abrufmuster, statt den Informationszugang situativ korrekt zu wählen. Für MCP-Pipelines heißt das: gut mit enger Tool-Governance, schwach bei freier Orchestrierung.

Dass ein Retry nötig war, wirkt hier eher wie ein Protokoll- oder Formatproblem als ein reines Verständnisversagen. Inhaltlich trifft das Modell häufig die richtige Arbeitsrichtung, aber nicht stabil genug in der ersten, formal gültigen Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur moderat. P2 von 63.33 zeigt, dass die Zusammenfassungen meist nützlich sind, aber nicht konstant präzise verdichten. Das sieht man auch an EU License Research und Multilingual Search & Synthesis: starke Beschaffung, aber nur mittelstarke Endverdichtung. Für Architekturen, in denen das Modell Tool-Ausgaben in knappe Entscheidungsgrundlagen überführen soll, braucht es nachgelagerte Validierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser. Beim Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb das Modell im verifizierten Inhaltsraum. Keine Halluzination, Content-Verification-State A. Das ist für Compliance-nahe Recherchen ein klar positives Signal.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Abruf prüft, reagiert Qwen 3.7 Max produktionsgerecht. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler offen. Genau dieses Verhalten ist in Tool-Pipelines akzeptabel, weil der Orchestrator den Fehler gezielt behandeln kann.

**Betriebsprofil**

Langsam. 13.90s im ersten Call, 37.13s im zweiten, 311.11s total.  
Günstig bis moderat. 0.015659 USD pro Run.  
Im Verhältnis zur Leistung ist das Kostenprofil vertretbar, das Latenzprofil aber klar der begrenzende Faktor.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit enger Tool-Führung, klaren Tool-Gates und Retry-Logik, etwa Rechercheketten, dokumentenzentrierte Extraktion und mehrsprachige Web-Aufgaben. Nicht geeignet als frei agierender Tool-Planer, der selbstständig zwischen Suche, Abruf und Synthese wählen muss. Wer das Modell einsetzt, sollte Tool-Selection extern absichern und Antworten mit strukturellen Checks gegen die tatsächlichen Tool-Ergebnisse binden.