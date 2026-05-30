**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:06


Bedingt deploy, weil die Tool-Ausführung stark ist und valide MCP-Calls produziert, die erkannte Halluzination bei nur mittlerer Synthesetreue das Vertrauen in unbeaufsichtigte Antwortstrecken aber begrenzt. Der Combined-Score von 71.62 stützt Einsatzfähigkeit, nicht Vollvertrauen.

**Tool-Execution-Profil**

Mistral Medium 3.5 arbeitet auf der Ausführungsebene belastbar. P1 89.17 spricht für korrekte Tool-Nutzung, und der valide Tool-Call zeigt, dass das Modell das MCP-Protokoll grundsätzlich sauber bedient. Für produktive Pipelines ist das der wichtigste positive Befund. Weniger gut abgesichert ist, ob diese Stärke aus echter Werkzeugwahl oder aus stabilem Befolgen eines erwarteten Musters kommt, weil die Einzelwerte für Web Search & Tool Selection sowie URL Construction & Fetch fehlen. Damit bleibt offen, wie sicher das Modell in dynamischen Tool-Umgebungen zwischen Suche und direktem Fetch unterscheidet. Dass ein Retry erforderlich war, wirkt hier eher wie ein Format- oder Orchestrierungsproblem als ein Verständnisfehler. Gegen ein inhaltliches Scheitern spricht, dass der Tool-Call am Ende valide war.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. P2 55.00 ist für ein Server-Modell zu niedrig, wenn aus Tool-Rohdaten belastbare Entscheidungsantworten entstehen sollen. Das Modell kann also Informationen beschaffen, aber die Verdichtung in eine präzise, knappe und belastbare Schlussantwort bleibt der schwächere Teil der Kette.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb es auf der sicheren Seite: keine Halluzination erkannt. Das ist ein gutes Vertrauenssignal. Der globale Halluzinationsbefund bleibt trotzdem ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call statt erfundenem Seiteninhalt prüft, halluzinierte das Modell nicht. Das ist produktionsfähig. Ein Modell darf an einem fehlenden Tool scheitern, solange es den Fehler offen meldet und keinen Ersatzinhalt erfindet. Genau dieses Verhalten zeigt Mistral Medium 3.5 hier.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Im Ergebnis liegt es 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist nah genug am Flottenniveau, um Local-first-Architekturen ernsthaft zu rechtfertigen.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klarer Tool-Führung, Antwortvalidierung und nachgelagerter Kontrolle. Besonders sinnvoll in souveränen Recherche-, Extraktions- und Agent-Workflows, bei denen Tool-Aufrufe wichtiger sind als elegante Endsynthese. Nicht die richtige Wahl für unbeaufsichtigte Endnutzerantworten, Compliance-Ausgaben ohne Verifikation oder Pipelines, in denen die Modellantwort selbst als letzte Wahrheit gilt.