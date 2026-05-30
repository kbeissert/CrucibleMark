**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:49:25


Bedingt deploy, weil Grok 4.3 valide Tool-Calls liefert und nicht halluziniert, aber die Synthesetreue für produktionsnahe MCP-Pipelines zu unzuverlässig bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist der belastbare Teil dieses Modells. P1 liegt mit 83.33 klar über dem Syntheseanteil. Tool-Calls waren valide, MCP-konform und ohne Retry lauffähig. Das spricht gegen ein Protokoll- oder Formatproblem und für grundsätzlich saubere Einbindung in eine Tool-Infrastruktur.

Bei der Werkzeugwahl zeigt das Modell brauchbare, aber nicht starke Urteilskraft. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden lässt, erreicht es nur ein solides Ergebnis. Beim URL-Construction-Test, der korrekte Ziel-URL und anschließenden Fetch prüft, bleibt es auf demselben Niveau. Das wirkt nicht wie starres Blind-Schema, aber auch nicht wie robuste Tool-Intelligenz. Für klar geroutete Pipelines ist das ausreichend. Für dynamische Orchestrierung mit konkurrierenden Tools ist es zu unsicher.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. P2 liegt bei 43.33 und zieht sich konsistent durch mehrere Assets: EU License Research, Tool Failure Handling (404), Web Search & Tool Selection und URL Construction & Fetch bleiben alle deutlich unter dem Niveau, das man für präzise Ergebnisverdichtung in Produktionsketten erwartet. Positiv fällt nur HTTP Fetch & Extract sowie Multilingual Search & Synthesis auf. Das Modell kann Inhalte zusammenführen, aber nicht konstant präzise genug.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, ist das Vertrauenssignal gemischt. Es halluziniert nicht, was zentral ist. Aber P2=20 bei Content-Verification-State B2 zeigt, dass es den abgerufenen Inhalt nicht sauber in belastbare Aussagen überführt. Das Modell erfindet nichts. Es belegt aber auch nicht zuverlässig, dass es die Tool-Ausgabe präzise verstanden hat.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit Tool-Fehlern statt erfundenem Seiteninhalt misst, verhält sich Grok 4.3 akzeptabel. Es halluziniert trotz Fehler keinen Ersatzinhalt. Das ist für Produktion wesentlich. Schwach bleibt die Antwortaufbereitung nach dem Fehler. P2=40 bedeutet: formal sicher, kommunikativ und diagnostisch nur begrenzt hilfreich.

**Betriebsprofil**

Total 52.75s pro Run. Call 1: 2.70s. MCP-Latenz: 0.92s. Call 2: 5.17s. Insgesamt langsam für die gelieferte Qualität. Kosten/Run: $0.011412. Preislich günstig bis moderat. Im Verhältnis zur Leistung nur dann attraktiv, wenn Tool-Sicherheit wichtiger ist als Synthesepräzision.

**Fazit & Empfehlung**

Geeignet für überwachte MCP-Pipelines mit klaren Tool-Pfaden, einfacher Retrieval-Aufgabe und nachgelagerter Validierung durch Systemregeln oder einen zweiten Prüfschritt. Nicht geeignet für Compliance-nahe Recherche, autonome Tool-Auswahl oder Pipelines, in denen die textuelle Verdichtung selbst als verlässliches Endprodukt dient. Grok 4.3 ist als ausführendes Glied brauchbar. Als vertrauenswürdige Syntheseinstanz ist es zu schwach.