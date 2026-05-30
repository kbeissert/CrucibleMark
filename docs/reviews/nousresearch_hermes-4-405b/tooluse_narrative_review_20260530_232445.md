**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:45


Bedingt deploy, weil Hermes 4 405B valide Tool-Calls liefert und keine Halluzination im Lauf gezeigt hat, die Synthesetreue mit Combined 76.17 aber nicht stark genug ist, um unbeaufsichtigte High-Trust-Pipelines ohne enge Guardrails zu rechtfertigen.

**Tool-Execution-Profil**

Das stärkste Produktionssignal ist P1 90.00. Das Modell produziert valide Calls, blieb MCP-protokollkonform und brauchte keinen Retry. Das spricht nicht nur für Formatdisziplin, sondern für belastbare Übergabe in bestehende Tool-Infrastrukturen. Gerade in agentischen Ketten ist das wichtiger als reine Sprachqualität.

Bei der Werkzeugwahl bleibt die Aussage begrenzt, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelscores vorliegen. Deshalb lässt sich nicht sicher belegen, ob Hermes 4 405B aktiv zwischen web_search und fetch differenziert oder überwiegend einem stabilen Aufrufmuster folgt. Was man sagen kann: Es hat im Lauf keinen ungültigen Tool-Pfad erzeugt. Für deterministische Pipelines ist das ein gutes Zeichen. Für dynamische Recherchepfade mit konkurrierenden Tools fehlt noch der harte Nachweis der Werkzeugintelligenz.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 63.33 ist für ein Frontier-Modell keine Ausfallstufe, aber auch kein Signal für präzise, knappe und belastbare Verdichtung unter Produktionsdruck. Man sollte damit rechnen, dass Tool-Ergebnisse korrekt weitergereicht werden, die Zusammenfassung aber an Schärfe, Priorisierung oder faktischer Kompression verliert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im gegebenen Lauf ja. Beim EU License Research, also dem Honeypot-Test auf aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen, wurde keine Halluzination erkannt. Das ist das entscheidende Vertrauenssignal. Es gibt hier keinen Hinweis, dass das Modell erfundene Aktualität in die Pipeline einschleust.

**Fehlerresilienz**

Akzeptabel für Produktion. Beim Tool Failure Handling (404), also dem Test auf transparenten Umgang mit fehlgeschlagenem Abruf statt erfundenem Seiteninhalt, hat Hermes 4 405B nicht halluziniert. Das Modell scheint Fehlerzustände als Fehlerzustände stehen zu lassen. Genau das braucht eine Tool-Pipeline, damit nachgelagerte Komponenten sauber eskalieren oder neu planen können.

**Betriebsprofil**

Total 46.36s. Tool-Calls selbst schnell mit 1.89s und 4.95s, aber Gesamtlaufzeit klar lang. Kosten/Run 0.006693. Günstig für die Modellklasse, zeitlich jedoch kein Low-Latency-Kandidat.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines, in denen valider Tool-Use wichtiger ist als exzellente Endverdichtung: Recherche-Orchestrierung, strukturierte Extraktion, kontrollierte Agentenflüsse mit nachgelagerter Validierung. Nicht die erste Wahl für executive Briefings, Compliance-Summaries oder andere Ketten, in denen die letzte Syntheseschicht ohne menschliche Prüfung veröffentlichungsreif sein muss. Deployen, aber mit engen Ausgabe-Schemata, Resultat-Checks und klarer Trennung zwischen Tool-Ausführung und finaler Nutzerzusammenfassung.