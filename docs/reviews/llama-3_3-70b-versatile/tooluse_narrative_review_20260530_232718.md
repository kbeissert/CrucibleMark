**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:18


Bedingt deploy, weil die Tool-Calls formal valide sind, das Modell aber mit schwacher Gesamtleistung und erkannten Halluzinationen kein verlässlicher Standardbaustein für tool-zentrierte Produktionspipelines ist.

**Tool-Execution-Profil**

Das Modell spricht das MCP-Protokoll sauber genug an: Tool-Call valide, kein Retry erforderlich. Das ist die Mindestvoraussetzung, und die erfüllt es. Die eigentliche Schwäche liegt nicht im Format, sondern in der Werkzeugwahl. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es nur P1=40. Beim Test URL Construction & Fetch, der präzise URL-Ableitung und anschließenden Fetch misst, bleibt es ebenfalls bei P1=40. Das spricht nicht für flexible Tool-Intelligenz, sondern für ein starres, nur teilweise passendes Muster. Positiv ist HTTP Fetch & Extract mit P1=80: Wenn die richtige Ressource bereits vorliegt, kann es den Abrufpfad ausführen. Für dynamische Pipelines, in denen das Modell selbst das passende Werkzeug und den richtigen Einstiegspunkt wählen muss, ist das zu unsicher.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2=31.67 zeigt, dass die eigentliche Verdichtung der abgerufenen Informationen der Engpass ist. Besonders sichtbar wird das bei HTTP Fetch & Extract mit P2=15 sowie bei EU License Research und Web Search & Tool Selection mit jeweils P2=20. Das Modell ruft also teils verwertbare Signale ab, überführt sie aber nicht stabil in belastbare, knappe Arbeitsantworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nur eingeschränkt vertrauenswürdig. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen beantwortet werden, liegt P2 bei 20 und der Content-Verification-State bei B2. Dort wurde zwar keine Halluzination markiert. Auf Run-Ebene ist Halluzination aber erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als tool-gestützte Ausgabe ausgibt, verliert die gesamte Pipeline ihre Beweiskraft.

**Fehlerresilienz**

Hier verhält sich das Modell produktionsgerecht. Im 404-Test, der den Umgang mit scheiternden Tool-Aufrufen prüft, erreicht es P2=80 und halluziniert keinen Ersatzinhalt. Es kommuniziert Fehler also transparent, statt Seiteninhalt zu erfinden. Das ist für Produktion akzeptabel und klar besser als seine Syntheseleistung im Erfolgsfall.

**Souveränitätsprofil**

Lokal betreibbar und kostenseitig attraktiv, aber nicht fleet-kompetitiv. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet ist das Modell für lokale, datensensible Pipelines mit enger Führung: feste Tool-Pfade, klare Prompts, geringe Autonomie und nachgelagerte Validierung. Nicht geeignet ist es für Compliance-, Recherche- oder Entscheidungs-Pipelines, in denen das Modell selbst Werkzeuge wählen, Ergebnisse zuverlässig verdichten und als belastbare Tool-Wahrheit ausgeben muss. Als ausführendes Glied unter strikter Orchestrierung ist es brauchbar. Als eigenständig handelnde Tool-Instanz ist es nicht robust genug.