**Deployment-Urteil**

> **Erstellt am:** 06.09.2026, 18:11:34


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgehend valide sind und die Synthese mit Halluzinationsbefund das Vertrauen in produktive Tool-Pipelines begrenzt.

**Tool-Execution-Profil**

Qwen 3.8 27B Uncensored zeigt echte Werkzeugintelligenz statt bloßer Schema-Nutzung. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf an web_search zuverlässig. Das ist ein gutes Signal für dynamische MCP-Pipelines. Beim Test URL Construction & Fetch, der die eigenständige Ableitung der Ziel-URL und den anschließenden Abruf misst, arbeitet es brauchbar, aber nicht deterministisch genug für Infrastrukturen mit strikten Format- oder Routing-Anforderungen. Die P1-Leistung ist insgesamt hoch, aber der Befund „Tool-Call valide: false“ ist operativ wichtiger als der Score. Das Modell versteht offenbar, welches Werkzeug gebraucht wird, produziert aber nicht in jeder Situation protokollsaubere Aufrufe. Da kein Retry nötig war, spricht das eher für punktuelle Formfehler oder unpräzise Parameterisierung als für grundlegendes Tool-Verständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist mit 59.17 der klare Schwachpunkt dieses Laufs. Besonders bei EU License Research, das aktuelle Lizenzrestriktionen aus Web-Quellen verdichten soll, und bei HTTP Fetch & Extract, das präzise Fakten aus abgerufenem Inhalt extrahiert, verliert das Modell an Genauigkeit und Verdichtungsdisziplin. Für produktive Nutzung heißt das: Es holt die Daten oft richtig, formuliert sie aber nicht stabil genug in verlässliche Ergebnisobjekte oder knappe Entscheidungstexte um.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research ist der Vertrauensbefund gemischt. Positiv ist, dass keine Halluzination erkannt wurde. Negativ ist die schwache Verdichtung mit P2=40. Das Modell driftet hier nicht offen in frei erfundene Compliance-Aussagen ab, aber es zeigt auch nicht die Präzision, die man für regulatorische oder lizenzbezogene Entscheidungen braucht. Da global ein Halluzinationsbefund gesetzt ist, ist das als Sicherheitsrisiko zu lesen: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgeben kann, verliert die gesamte Pipeline ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der prüft, ob ein fehlgeschlagener Tool-Aufruf transparent behandelt wird, kommuniziert das Modell den Fehler sauber und erfindet keinen Seiteninhalt. Genau dieses Verhalten braucht eine robuste Tool-Kette.

**Betriebsprofil**

Call 1: 7.36s. MCP-Latenz: 1.02s. Call 2: 52.86s. Total: 367.42s.  
Langsam für den erzielten Qualitätsgrad. Lokal betrieben, daher keine API-Kosten. Wirtschaftlich nur dann attraktiv, wenn lokale Ausführung und offene Gewichte Vorrang vor Durchsatz haben.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Orchestrierungs-Pipelines, in denen Tool-Wahl, Suchanstoß und transparente Fehlerbehandlung wichtiger sind als perfekte Endverdichtung. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere entscheidungsnahe Workflows, in denen die Antwort selbst als verlässliches Ergebnisartefakt dienen muss. Wenn Sie es einsetzen, dann mit harter Schema-Validierung, nachgelagerter Verifikation und einer Instanz, die Synthesen gegen Rohquellen prüft.