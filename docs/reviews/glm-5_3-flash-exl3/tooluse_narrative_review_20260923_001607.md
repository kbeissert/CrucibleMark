**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:16:07


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgehend valide sind und die Synthese bei wissenssensitiven Recherchen nicht zuverlässig genug im Tool-Befund bleibt.

**Tool-Execution-Profil**

GLM-5.3-Flash (EXL3) zeigt echte Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, wählt es das richtige Tool sicher. Das spricht gegen ein starres Fetch-First-Muster. Auch bei Multilingual Search & Synthesis und EU License Research greift es operativ sauber auf externe Quellen zu.

Die Schwäche liegt nicht in der Planungslogik, sondern in der Präzision einzelner Aufrufe. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den korrekten Abruf misst, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Der Befund „Tool-Call valide: false“ ist deshalb relevant. Für MCP-gestützte Flows mit toleranter Validierung ist das handhabbar. Für streng schema- und routingkritische Ketten ist es ein Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht stark genug für High-Trust-Ausgaben. Die Extraktion aus echtem Web-Content gelingt sehr gut, ebenso die Verdichtung nach Fehlerfällen und bei HTTP Fetch & Extract. Schwächer wird es bei Rechercheaufgaben mit Interpretationsanteil. EU License Research und Multilingual Search & Synthesis zeigen, dass es Ergebnisse zusammenführt, aber nicht immer trennscharf priorisiert. Das ist der Hauptgrund, warum P2 hinter der Tool-Execution zurückbleibt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht sauber genug. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Modellwissen kommen, fällt die Vertrauensseite deutlich ab. Es halluziniert zwar nicht offen, aber der niedrige Synthese-Befund bedeutet: Es antwortet nicht verlässlich eng am recherchierten Material. Für Compliance-, Policy- oder Lizenz-Pipelines ist das ein Warnsignal.

**Fehlerresilienz**

Hier ist das Modell produktionsreif. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, kommuniziert es den Fehler korrekt und erfindet keinen Seiteninhalt. Genau dieses Verhalten braucht eine Tool-Pipeline. Ein fehlender Abruf bleibt als fehlender Abruf sichtbar.

**Souveränitätsprofil**

Lokal betreibbar und insgesamt fleet-kompetent. Der Sovereignty Gap liegt bei -0.89 Punkten unter dem Fleet-Ø von 68.17. Das ist ein sehr kleiner Abstand und stützt den Einsatz dort, wo lokale Gewichte, Datenhoheit und MIT-Lizenz wichtiger sind als letzte Prozentpunkte in der Synthesedisziplin.

**Fazit & Empfehlung**

Geeignet für agentische MCP-Pipelines mit Suche, Fetch, Orchestrierung und robuster Fehlerbehandlung. Besonders passend für lokale, souveräne Deployments, in denen Tool-Nutzung wichtiger ist als perfekte narrative Verdichtung. Nicht die erste Wahl für Compliance, Lizenzbewertung, regulatorische Recherche oder andere Pipelines, in denen die Antwort strikt am Tool-Beleg kleben muss und URL- sowie Call-Validität deterministisch sein sollen.