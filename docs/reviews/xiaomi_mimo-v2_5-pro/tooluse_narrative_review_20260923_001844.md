**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:18:44


Bedingt deploy, weil die Tool-Ausführung stark ist, das Modell aber bei erkannter Halluzination und ungültigem Tool-Call das zentrale Vertrauenssignal für produktive MCP-Pipelines nicht stabil hält.

**Tool-Execution-Profil**

Xiaomi MiMo V2.5 Pro zeigt echte Werkzeugintelligenz, nicht nur starres Call-Muster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sauber. Das spricht für belastbare Planungslogik in dynamischen Agentenläufen. Auch HTTP Fetch & Extract ist solide.

Schwächer wird es beim URL-Construction-Test, der die eigenständige Herleitung einer Ziel-URL und den anschließenden Abruf misst. Hier ist die Leistung brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen direkt operative URLs ableiten lassen. Kritischer ist der Befund, dass der Tool-Call insgesamt nicht durchgehend valide war. Da kein Retry erforderlich war, wirkt das weniger wie ein reines Formatproblem und eher wie eine situative Ausführungsschwäche im Orchestrierungspfad.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 44.17 zeigt: Es kann gefundene Inhalte zusammenführen, aber nicht konstant präzise genug. Das sieht man besonders bei EU License Research und URL Construction & Fetch, wo die Ausführung noch brauchbar ist, die Verdichtung aber deutlich abfällt. Für produktive Tool-Pipelines ist das ein Problem, weil der eigentliche Wert erst in der korrekten Rückübersetzung der Tool-Daten in verlässliche Aussagen entsteht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Trainingswissen stammen, halluziniert das Modell. Das ist kein Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene oder vorab gelernte Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Infrastruktur ihre Auditierbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Abruf prüft, erfindet Xiaomi MiMo V2.5 Pro keinen Seiteninhalt. Das ist der richtige Produktionsreflex. Die Kommunikation des Fehlers bleibt jedoch nur mittelstark verdichtet. Für den Betrieb ist das akzeptabel, weil Transparenz wichtiger ist als sprachliche Qualität.

**Betriebsprofil**

Call 1: 65.39s. Call 2: 79.60s. MCP-Latenz: 1.19s. Total: 877.06s. Langsam. Kosten/Run: local. Günstig im Betrieb, aber die Laufzeit steht nur teilweise im Verhältnis zur erreichten Synthesesicherheit.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen Tool-Wahl, Suchstrategie und Fehleroffenlegung wichtiger sind als die letzte Meile der faktenstrengen Synthese. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere High-Trust-Pipelines, in denen das Modell strikt an Tool-Ergebnissen bleiben muss. Wenn Sie es einsetzen, dann mit harter Antwortvalidierung, Output-Scoring und nachgelagerter Prüfkomponente vor jeder extern wirksamen Entscheidung.