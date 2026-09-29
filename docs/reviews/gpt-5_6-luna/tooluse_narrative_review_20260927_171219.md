**Deployment-Urteil**

> **Erstellt am:** 27.09.2026, 17:12:19


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Call-Validität nicht durchgängig sitzt und die Synthesetreue im Honeypot zu schwach für vertrauenskritische Pipelines ausfällt.

**Tool-Execution-Profil**

GPT 5.6 Luna zeigt echte Werkzeugintelligenz, nicht nur starres Abrufen. Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis zwischen Suche und direktem Fetch unterscheiden lässt, wählt es das richtige Werkzeug sehr sicher. Das spricht für brauchbare Orchestrierung in offenen MCP-Flows. Beim URL-Construction-Test, der die Ziel-URL aus eigenem Wissen ableiten und dann korrekt abrufen lässt, bleibt es ordentlich, aber weniger präzise. Genau dort sieht man die Grenze: Es erkennt meist die richtige Operationsart, produziert aber nicht in jedem Schritt einen vollständig belastbaren Call. Dass der Tool-Call insgesamt als nicht valide gewertet wurde, ist für Produktion relevanter als der gute P1-Mittelwert. Es ist also kein Verständnisproblem auf Aufgabenebene, sondern ein Protokoll- und Ausführungsrisiko an den Rändern.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht verlässlich genug für strenge Faktenpipelines. In HTTP Fetch & Extract und Multilingual Search & Synthesis verdichtet es Ergebnisse brauchbar und meist strukturiert. Der Gesamtwert bleibt dennoch nur im guten Mittelfeld, weil die Ausgabequalität zwischen Aufgaben sichtbar schwankt. Für analystische Assistenz reicht das oft. Für deterministische Übergaben an nachgelagerte Systeme ist es zu inkonsistent.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das Hauptproblem. Im EU-License-Research-Honeypot, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Modellwissen kommen, fällt die Synthese klar ab. Es halluziniert zwar nicht offen, aber das Vertrauenssignal ist schwach: Das Modell zeigt nicht zuverlässig genug, dass es seine Antwort strikt auf den beschafften Tool-Kontext begrenzt. Für Compliance, Regulatorik und aktuelle Policy-Lagen ist das ein Warnzeichen.

**Fehlerresilienz**

Gut für Produktion. Im 404-Test, der einen fehlschlagenden Tool-Call auf Transparenz statt Ersatzhalluzination prüft, reagiert das Modell sauber. Es erfindet keinen Seiteninhalt und kommuniziert den Ausfall korrekt. Genau dieses Verhalten hält eine Tool-Pipeline stabil, wenn externe Quellen abbrechen.

**Betriebsprofil**

Call 1: 1.97s. MCP-Latenz: 1.88s. Call 2: 5.26s. Total: 54.73s.  
Günstig, aber nicht schnell im End-to-End-Run. Für den Preis attraktiv, für latenzkritische Mehrschritt-Pipelines nur eingeschränkt.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Routing-Pipelines, in denen Tool-Wahl, Fehlertoleranz und Kosten wichtiger sind als harte Faktentreue in der Endverdichtung. Nicht geeignet für Compliance-, Legal- oder Policy-Workflows, in denen das Modell strikt an aktuelle Tool-Belege gebunden bleiben muss. Ich würde es als kosteneffizienten Orchestrator mit nachgelagerter Validierung einsetzen, nicht als letzte vertrauensgebende Instanz.