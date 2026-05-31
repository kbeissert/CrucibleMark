**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:52:49


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die nachgelagerte Synthese mit erkannter Halluzination das Vertrauen in eine MCP-Pipeline nur eingeschränkt trägt. Der valide Tool-Call bei Combined 64.67 reicht für produktive Nutzung nur dort, wo ein zweiter Verifikationsschritt existiert.

**Tool-Execution-Profil**

Gemma 4 E4B verhält sich auf der Ausführungsebene überraschend sauber. Es wählt Werkzeuge meist korrekt, produziert valide Calls und zeigt kein MCP-Formatproblem; ein Retry war nicht nötig. Das stärkste Signal kommt aus Web Search & Tool Selection: Dort erkennt das Modell ohne expliziten Hinweis, dass zuerst gesucht statt direkt gefetcht werden muss. Das spricht für echte Werkzeugwahl, nicht nur für starres Abarbeiten eines Musters.

Schwächer ist es beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen ableiten und dann korrekt fetchen kann. P1 80 ist brauchbar, aber nicht präzise genug für deterministische Pipelines mit harter URL-Abhängigkeit. Insgesamt gilt: Das Modell kann Infrastruktur bedienen. Es ist aber besser beim Entscheiden zwischen Such- und Fetch-Werkzeugen als beim exakten Konstruieren von Endpunkten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 39.17 ist der klare Engpass. Bei HTTP Fetch & Extract, also strukturierter Faktenextraktion aus realem Content, bleibt die Verdichtung noch solide. In mehreren anderen Aufgaben kippt die Antwortqualität jedoch von Extraktion zu lockerer Zusammenfassung. Für Pipelines, die präzise Felder, Jahreszahlen oder Restriktionsdetails weiterreichen, ist das zu unscharf.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research nicht verlässlich. Dieser Test prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen geholt statt aus dem Trainingswissen beantwortet werden. Mit P2 15, Content-Verification-State B2 und erkannter Halluzination ist das ein Sicherheitsrisiko, kein bloßer Qualitätsmangel. Wenn ein Modell in einer Compliance-nahen Recherche erfundene oder vorab gelernte Fakten als Tool-Ergebnis ausgibt, beschädigt es die Vertrauenskette der gesamten Pipeline.

**Fehlerresilienz**

Beim 404-Test reagiert das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz fehlgeschlagenem Tool-Aufruf. Die Transparenz ist nicht stark genug für hohe Synthesequalität, aber sie bleibt auf der richtigen Seite der Produktionsgrenze: Fehler werden eher offengelegt als kaschiert.

**Souveränitätsprofil**

Lokal betreibbar, geringe operative Hürde, Kosten pro Run lokal. Gleichzeitig bleibt die Leistung 3.57 Punkte unter dem Fleet-Ø von 66.54. Das ist als souveräne Option vertretbar, aber nicht fleet-kompetitiv, wenn hohe Antworttreue wichtiger ist als lokaler Betrieb.

**Fazit & Empfehlung**

Geeignet für lokale, kostensensitive Tool-Pipelines mit klaren Guardrails, etwa Recherche-Vorstufen, Such-Orchestrierung, Routing und kontrollierte Fetch-Workflows. Nicht geeignet für Compliance, Policy, Lizenzprüfung oder jede Pipeline, in der die verbale Synthese direkt als verlässliches Faktum weiterverarbeitet wird. Wer es einsetzt, sollte Antworten gegen Roh-Tool-Output prüfen oder das Modell auf reine Tool-Ausführung begrenzen.