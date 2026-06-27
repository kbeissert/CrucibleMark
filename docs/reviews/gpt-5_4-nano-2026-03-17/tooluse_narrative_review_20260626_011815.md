**Deployment-Urteil**

> **Erstellt am:** 26.06.2026, 01:18:15


Bedingt deploy, weil die Tool-Ausführung oft brauchbar ist, aber ungültige Tool-Calls und erkannte Halluzinationen das Modell für vertrauenskritische MCP-Pipelines begrenzen.

**Tool-Execution-Profil**

GPT-5.4 Nano erkennt grundsätzlich, wann es suchen statt direkt abrufen muss. Beim Test Web Search & Tool Selection, der die Wahl zwischen web_search und fetch ohne expliziten Hinweis prüft, liegt die Ausführung sehr stark. Das spricht gegen ein rein starres Muster und für brauchbare Werkzeugwahl in offenen Retrieval-Schritten. Auch beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Fetch misst, arbeitet das Modell solide, aber nicht deterministisch genug für fragile Pipelines mit strikten Pfadannahmen.

Der kritische Punkt ist die Protokolltreue. Tool-Call valide: False bedeutet, dass die Pipeline nicht nur inhaltlich, sondern operativ absichern muss. Das Modell kann also den richtigen Arbeitsmodus erkennen, produziert aber nicht zuverlässig MCP-konforme Aufrufe. Für produktive Tool-Ketten ist das ein Integrationsrisiko, weil nachgelagerte Systeme an Format- oder Parameterfehlern scheitern können. Retry war nicht erforderlich. Das wirkt daher eher wie inkonsistente Ausführung als ein einmaliges Formatproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt brauchbar. Die P2-Leistung ist der schwächste Teil des Profils. Bei HTTP Fetch & Extract, also der strukturierten Verdichtung realer Seiteninhalte, bleibt die Qualität wechselhaft. Auch bei Multilingual Search & Synthesis zeigt sich starke Streuung. Das Modell kann Ergebnisse zusammenziehen, hält Präzision und Vollständigkeit aber nicht stabil genug für Compliance-, Policy- oder entscheidungsnahe Zusammenfassungen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, ist das Vertrauenssignal schwach. Zwar wurde dort keine Halluzination markiert, aber P2=20 zeigt, dass das Modell die abgerufenen Inhalte kaum belastbar in eine Antwort überführt. Da global Halluzination erkannt: True gilt, ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Erfundenes als angebliches Tool-Ergebnis untergräbt die gesamte Tool-Infrastruktur.

**Fehlerresilienz**

Bei Tool Failure Handling (404), also dem Test auf transparentes Verhalten nach fehlgeschlagenem Abruf, reagiert das Modell grundsätzlich akzeptabel. Es halluziniert im ausgewiesenen 404-Fall keinen Seiteninhalt und bleibt damit auf der richtigen Seite der Produktionsgrenze. Die Transparenz ist aber nicht durchgehend stark, wie die Streuung zwischen den beiden 404-Durchläufen zeigt. Für robuste Systeme ist das ausreichend, für autonome Agenten ohne Guardrails nicht.

**Betriebsprofil**

1.80s erster Modell-Call. 1.29s MCP-Latenz. 4.05s zweiter Call. 42.84s total. Günstig, aber für die erzielte Qualität und Zuverlässigkeit nicht schnell genug im End-to-End-Verlauf.

**Fazit & Empfehlung**

Geeignet als kostengünstiger Sub-Agent für einfache Suchanstoß-, Routing- und Vorfilter-Aufgaben, bei denen nachgelagerte Validatoren Tool-Calls prüfen und Antworten gegen Quellmaterial abgleichen. Nicht geeignet für direkt vertrauenswürdige Recherche-Synthese, Compliance-Ausgaben oder MCP-Pipelines, in denen das Modell ohne strikte Schema-Prüfung, Source-Grounding und Antwortvalidierung eigenständig Ergebnisse ausliefern soll.