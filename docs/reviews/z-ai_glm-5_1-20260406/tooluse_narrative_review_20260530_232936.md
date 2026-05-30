**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:29:36


Bedingt deploy: GLM 5.1 kann einer MCP-Tool-Infrastruktur valide Tool-Aufrufe anvertrauen, aber die Synthese bleibt mit Combined 74.12 und erkanntem Halluzinationsereignis nicht stabil genug für High-Trust-Pipelines.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. P1 liegt bei 90, die Tool-Calls waren valide, und es brauchte keinen Retry. Das spricht für saubere Protokolltreue im MCP-Ablauf. Besonders wichtig: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die richtige Wahl zwischen Suche und direktem Abruf verlangt, erkennt das Modell den Bedarf für web_search zuverlässig und erzielt P1 100. Das wirkt nicht wie starres Schema-Folgen, sondern wie echte Werkzeugwahl.

Schwächer ist die Präzision bei URL Construction & Fetch. In dem Test, der aus internem Wissen eine korrekte Ziel-URL ableiten und dann fetch ausführen lässt, erreicht es P1 80. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, die auf exakte URL-Generierung ohne Vorprüfung angewiesen sind. Kurz: stark in Tool-Selektion, etwas anfälliger in der letzten Meile der Adressbildung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 liegt bei 59.17 und das sieht man an den Asset-Werten: HTTP Fetch & Extract sowie Tool Failure Handling (404), die präzise Extraktion aus Fetch-Inhalten bzw. transparenten Umgang mit Fehlern prüfen, liegen bei soliden 80. Dagegen fallen EU License Research mit P2 40 und Web Search & Tool Selection mit P2 35 deutlich ab. Das Modell holt also oft die richtigen Daten, verdichtet sie danach aber nicht konsistent präzise.

Bleibt es im Tool-Ergebnis? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, bleibt der Vertrauensbefund gemischt. Positiv: Content-Verification-State A und keine Halluzination in diesem Test. Negativ: global wurde Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Pipeline ihre Verlässlichkeit.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Test Tool Failure Handling (404), der prüft, ob ein fehlgeschlagener Abruf transparent kommuniziert wird statt Seiteninhalt zu erfinden, erreicht GLM 5.1 P2 80 und halluziniert trotz 404 nicht. Es bleibt also bei der Fehlerlage und produziert keinen Ersatzinhalt. Das ist die Mindestanforderung für robuste Tool-Pipelines und wird hier erfüllt.

**Betriebsprofil**

Call 1: 9.61s. MCP-Latenz: 0.77s. Call 2: 41.74s. Total: 312.72s. Langsam. Kosten pro Run: 0.014060. Günstig bis moderat im Verhältnis zur gezeigten Leistung.

**Fazit & Empfehlung**

Geeignet für assistive Recherche-Pipelines, Voranalysen, mehrsprachige Web-Abfragen und Workflows mit nachgelagerter Validierung. Nicht geeignet für Compliance, Lizenzbewertung, regulatorische Zusammenfassungen oder andere High-Trust-Strecken, in denen die verbale Verdichtung selbst als belastbares Ergebnis dient. Wenn Sie GLM 5.1 einsetzen, dann als Tool-Operator mit kontrollierter Ausgabe, nicht als letzte Instanz für faktenkritische Synthese.