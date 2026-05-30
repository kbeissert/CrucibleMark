**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:44:52


Bedingt deploy, weil Claude Opus 4.5 valide Tool-Calls produziert und operativ stabil wirkt, aber die Synthesetreue für produktionsnahe MCP-Pipelines nicht durchgehend verlässlich genug ist. Der Combined-Score von 72.79 ist dafür gut, aber nicht hinreichend für unkritische Freigabe.

**Tool-Execution-Profil**

Bei der Tool-Ausführung arbeitet das Modell stark. Tool-Call valide: true, Retry war nicht nötig, und P1 liegt mit 86.67 klar im produktionsfähigen Bereich. Besonders relevant ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, erkennt das Modell korrekt, dass web_search statt fetch nötig ist. Das spricht für echte Tool-Intelligenz, nicht nur für starres Call-Schema. Beim URL-Construction-Test, der prüft, ob das Modell die Ziel-URL selbst ableiten und dann korrekt abrufen kann, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Kurz: gute Orchestrierung, leichte Schwäche bei präziser Ableitung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 liegt bei 59.17 und zeigt das eigentliche Risiko dieses Modells im MCP-Betrieb: Nicht die Tool-Nutzung ist das Problem, sondern die Weiterverarbeitung. Die Schwäche zieht sich sichtbar durch EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis. Claude Opus 4.5 holt die Daten, verdichtet sie aber nicht durchgehend präzise, trennscharf und eng am Quellmaterial.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gemischt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Modellwissen kommen, liegt P2 nur bei 40 bei Verification-State B1. Gleichzeitig wurde dort keine Halluzination erkannt. Global ist jedoch hallucination_flag=true. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Inhalte als Tool-Ergebnis ausgibt, wird die gesamte Tool-Infrastruktur als Wahrheitsanker unterlaufen.

**Fehlerresilienz**

Im 404-Test, der das Verhalten bei scheiterndem Tool-Call misst, reagiert das Modell produktionsgerecht. P2=80, keine Halluzination trotz Fehler, klare Fehlerkommunikation statt erfundenem Seiteninhalt. Das ist für robuste Pipelines akzeptabel.

**Betriebsprofil**

Total 71.45s pro Run. Call-Latenzen 2.08s und 8.79s, MCP-Latenz 1.04s. Langsam. Kosten pro Run 0.111900 USD. Teuer. Im Verhältnis zur Tool-Ausführung vertretbar, im Verhältnis zur Synthesequalität angespannt.

**Fazit & Empfehlung**

Geeignet für orchestrierende Pipelines, in denen Tool-Wahl, mehrstufige Planung und saubere Fehlerbehandlung wichtiger sind als hochpräzise Verdichtung der Ergebnisse. Geeignet auch als Planner oder Supervisor über verifizierende Subsysteme. Nicht geeignet als letzte Syntheseinstanz in Compliance-, Research- oder Policy-Pipelines, wenn die Ausgabeschicht ohne zusätzliche Quellprüfung direkt an Nutzer oder Folgeprozesse geht. Empfehlung: deploy nur mit Retrieval-Nachweis, Quellzitat-Pflicht und einem nachgelagerten Verifier für die Endantwort.