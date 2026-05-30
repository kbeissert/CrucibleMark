**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:51:22


Nicht deploy. Die Datenlage ist für einen Produktionseinsatz unzureichend, und bei Combined 0.00 sowie ungültigem Tool-Call fehlt jede belastbare Grundlage, diesem Modell eine MCP-gestützte Tool-Infrastruktur zu übergeben.

**Tool-Execution-Profil**

Das zentrale Problem ist nicht eine schwache Einzeldisziplin, sondern fehlende Nachweisbarkeit über die gesamte Tool-Kette. Tool-Call valide steht auf false. Gleichzeitig liegen für Tool Execution, Web Search & Tool Selection und URL Construction & Fetch keine verwertbaren P1-Signale vor. Damit ist offen, ob das Modell Werkzeuge intelligent auswählt oder nur auf starre Muster reagiert.

Gerade bei einem Frontier-Generalisten wäre zu erwarten, dass er ohne explizite Anleitung erkennt, wann eine Websuche statt eines direkten Fetch nötig ist, und dass er bekannte Ziel-URLs präzise konstruiert. Diese Fähigkeit ist hier nicht belegt. Für MCP-Pipelines zählt Protokolltreue mehr als Eloquenz. Ohne valide Calls bleibt das Modell auf Infrastrukturebene nicht vertrauensfähig. Positiv ist nur, dass kein Retry erforderlich war. Das spricht eher gegen ein reines Formatproblem und eher für eine grundsätzliche Lücke im auswertbaren Tool-Verhalten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es keine belastbare Aussage. Für Synthesis Quality liegen durchgehend n/a-Werte vor, auch bei HTTP Fetch & Extract und Multilingual Search & Synthesis, also genau dort, wo präzise Verdichtung aus Tool-Output sichtbar werden müsste. Für produktive Pipelines heißt das: Die eigentliche Antwortqualität nach erfolgreichem Tool-Einsatz ist nicht evaluiert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus parametriertem Vorwissen beantwortet werden, zeigt zumindest kein Halluzinationssignal. Das ist ein wichtiges Vertrauensindiz, aber kein Freifahrtschein. Ohne Content-Verifikation und ohne nutzbare P2-Werte bleibt nur die Aussage, dass kein klarer Sicherheitsverstoß beobachtet wurde.

**Fehlerresilienz**

Im 404-Test, der transparenten Umgang mit scheiternden Tool-Aufrufen gegen erfundenen Ersatzinhalt abgrenzt, wurde keine Halluzination erkannt. Das ist für Produktion der richtige Mindeststandard. Akzeptabel ist jedoch nur die Fehlertransparenz, nicht die bloße Abwesenheit eines Halluzinationsflags. Da auch hier P2 fehlt, ist nicht belegt, wie sauber und operator-tauglich das Modell Fehler tatsächlich kommuniziert.

**Fazit & Empfehlung**

Allenfalls für interne Exploration unter enger Aufsicht. Nicht für Compliance-, Recherche-, Retrieval- oder Web-gestützte Agentenpipelines, in denen valide Tool-Calls und belastbare Synthese Pflicht sind. Vor einer Freigabe braucht dieses Modell einen vollständigen Re-Run mit auswertbaren Tool-Execution- und Synthesis-Signalen. Ohne diese Nachweise ist die Integration in eine MCP-Toolchain operativ nicht vertretbar.