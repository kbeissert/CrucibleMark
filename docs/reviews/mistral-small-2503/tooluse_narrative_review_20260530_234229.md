**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:29


Bedingt deploy: Das Modell ist für einfache, eng geführte Tool-Pipelines nutzbar, aber wegen erkannter Halluzination, ungültiger Tool-Calls und notwendigem Retry nicht als vertrauenswürdiger Standard-Agent für offene MCP-Orchestrierung geeignet.

**Tool-Execution-Profil**

Mistral Small 3.1 führt bekannte Abrufmuster solide aus, zeigt aber keine verlässliche Werkzeugwahl in offenen Situationen. Beim Test HTTP Fetch & Extract, der präzise Fakten aus realem Fetch-Content misst, arbeitet es stark. Auch beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch prüft, bleibt die Ausführung brauchbar. Anders sieht es beim Test Web Search & Tool Selection aus, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden lässt. Dort bricht die Leistung deutlich ein. Das spricht gegen echte Tool-Intelligenz und eher für ein festes Abrufschema: Wenn eine URL nahe liegt, funktioniert es. Wenn zuerst Suchentscheidung nötig ist, greift es zu oft zum falschen Werkzeug. Dass ein Retry erforderlich war und der Tool-Call nicht valide war, wirkt hier eher wie ein Verständnis- und Orchestrierungsproblem als ein bloßes Formatproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung bleibt insgesamt schwach, obwohl einzelne Aufgaben wie HTTP Fetch & Extract sehr gut zusammengeführt werden. Sobald mehrere Quellen, Suchschritte oder mehrsprachige Recherche zusammenkommen, sinkt die Verdichtungsqualität deutlich. Für produktive Pipelines heißt das: Rohdaten holt es teils ordentlich, aber die letzte Antwortschicht ist nicht stabil genug für belastbare Entscheidungsunterstützung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, fiel das Modell mit Halluzination auf. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Ein Modell, das erfundene oder aus Vorwissen rekonstruierte Aussagen als Ergebnis eines Tool-Laufs ausgibt, untergräbt die Nachprüfbarkeit der gesamten Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem gescheiterten Tool-Call misst, halluziniert das Modell keinen Seiteninhalt. Das ist der wichtigste Punkt und für Produktion akzeptabel. Die Kommunikation bleibt aber nur mäßig klar. Für robuste Systeme genügt das, wenn die Laufzeitumgebung Fehler selbst abfängt und Antworten mit Statuslogik absichert.

**Souveränitätsprofil**

Lokal betreibbar und kostensehr niedrig. Für souveräne Deployments ist das attraktiv. Leistungsseitig liegt es jedoch 5.32 Punkte unter dem Fleet-Ø von 66.76. Damit ist es lokal verfügbar, aber nicht fleet-kompetitiv genug für anspruchsvolle Tool-Agenten.

**Fazit & Empfehlung**

Geeignet für kostensensitive, lokal laufende Pipelines mit enger Führung: feste URL-Schemata, einfache Fetch-Extraktion, kontrollierte Fehlerrouten. Nicht geeignet für Compliance-, Recherche- oder Agenten-Pipelines, in denen das Modell eigenständig Tools wählen, aktuelle Web-Fakten strikt von Vorwissen trennen und belastbare Synthesen liefern muss. Wenn Sie es einsetzen, dann nur mit harter Tool-Gating-Logik, Antwortvalidierung und ohne Vertrauen in freie Rechercheentscheidungen.