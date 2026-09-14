**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:29:40


Bedingt deploy, weil die Tool-Nutzung oft funktional wirkt, das Modell aber halluziniert und dabei keine durchgehend validen Tool-Calls liefert. Für produktive MCP-Pipelines reicht ein Combined-Score von 56.42 hier nur unter enger Absicherung.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl-Kompetenz, aber keine verlässliche Protokolltreue. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erkennt es den Bedarf korrekt und erreicht P1 100. Das spricht gegen reines Schema-Folgen. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL und den anschließenden Fetch misst, fällt es auf P1 75 zurück. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, in denen ein einzelner falscher Endpunkt den Lauf entwertet.

Kritischer ist der Formfaktor der Ausführung: Der Tool-Call war nicht valide, obwohl kein Retry nötig war. Das wirkt weniger wie ein Verständniskollaps als wie unzuverlässige MCP-Ausgabe unter Last. Für produktive Orchestrierung heißt das: Tool-Gating, Call-Schema-Validierung und hartes Fail-Closed sind Pflicht.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 32.50 ist der eigentliche Engpass dieses Modells. In HTTP Fetch & Extract, URL Construction & Fetch und Multilingual Search & Synthesis, also genau dort, wo extrahierte Web-Inhalte präzise zusammengeführt werden müssen, bleibt die Verdichtung jeweils bei P2 15. Das Modell kann Informationen anholen, aber es transformiert sie nicht zuverlässig in belastbare Ergebnistexte.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, und das ist das zentrale Sicherheitsproblem. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell bei P2 15. Damit ist die Schwäche nicht nur stilistisch, sondern vertrauenskritisch: Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als recherchiertes Ergebnis ausgibt, unterläuft es die Kontrollfunktion der gesamten Infrastruktur.

**Fehlerresilienz**

Hier verhält sich das Modell produktionsgerecht. Im Test Tool Failure Handling (404), der misst ob ein fehlgeschlagener Tool-Call transparent statt mit erfundenem Ersatzinhalt behandelt wird, erreicht es P2 100. Es kommuniziert den Fehler offen und halluziniert keinen Seiteninhalt. Diese Art von Transparenz ist für Produktion akzeptabel.

**Souveränitätsprofil**

Lokal betreibbar, Apache 2.0, offene Gewichte und damit operativ attraktiv für sensible Datenflüsse. Mit 56.42 liegt es 11.33 Punkte unter dem Fleet-Ø von 67.75. Das Modell ist also souverän betreibbar, aber nicht fleet-kompetitiv genug, um ohne zusätzliche Guardrails als allgemeines Tool-Modell zu dienen.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische Assistenz-Pipelines mit klar begrenztem Tool-Scope, starker Schema-Validierung und nachgelagerter Ergebnisprüfung. Nicht geeignet für Compliance-, Recherche- oder Entscheidungs-Pipelines, in denen Tool-Ergebnisse als belastbare Tatsachen weitergereicht werden. Wer nur robuste Fehlerkommunikation und einfache Tool-Auslösung braucht, kann es einsetzen. Wer verifizierbare Synthese braucht, sollte es nicht als letzte Instanz in die MCP-Kette setzen.