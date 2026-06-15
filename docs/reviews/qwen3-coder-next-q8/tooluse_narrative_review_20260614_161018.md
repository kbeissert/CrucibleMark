**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:10:18


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber ein ungültiger Tool-Call und ein erkannter Halluzinationsfall das Vertrauen für unbeaufsichtigte MCP-Pipelines begrenzen. Der Combined-Score von 74.62 stützt ein produktionsnahes Potenzial, nicht aber Freigabe ohne Guardrails.

**Tool-Execution-Profil**

Mit P1 90.00 zeigt das Modell klar, dass es auf Tool-Nutzung ausgelegt ist und MCP-gestützte Abläufe grundsätzlich versteht. Das ist für ein Coding- und Agentic-Modell die richtige Richtung. Kritisch ist jedoch das Zuverlässigkeitssignal: Der Tool-Call war nicht valide, obwohl kein Retry nötig war. Das spricht eher gegen ein reines Formatproblem und eher für einen einmaligen Protokoll- oder Parametrierungsfehler im Call selbst.

Zu den Auswahltests fehlt leider Asset-Granularität. Deshalb lässt sich nicht belastbar sagen, ob es im Test Web Search & Tool Selection wirklich situationsgerecht zwischen Suche und direktem Fetch unterscheidet oder nur einem festen Tool-Muster folgt. Ebenso bleibt offen, ob es beim URL-Construction-Test Zieladressen präzise genug konstruiert. Für produktive Pipelines heißt das: Tool-Kompetenz ist wahrscheinlich vorhanden, aber nicht ausreichend belegt, um autonome Werkzeugwahl ohne zusätzliche Validierung freizugeben.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 59.17 ist der schwächere Teil des Profils und zeigt, dass die eigentliche Verdichtung, also das saubere Zusammenführen und präzise Wiedergeben von Tool-Output, deutlich hinter der Ausführung zurückbleibt. Für Code-Agents ist das akzeptabel, für Compliance-, Policy- oder Research-Synthesen ist es zu knapp.

Bleibt es im Tool-Ergebnis? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Wenn ein Modell erfundene Fakten als angebliches Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Im 404-Test, der transparenten Umgang mit einem scheiternden Tool-Aufruf gegen erfundenen Ersatzinhalt prüft, halluzinierte das Modell keinen Seiteninhalt. Das ist für Produktion akzeptabel. Es deutet darauf hin, dass das Modell Fehlerzustände zumindest in diesem Pfad nicht kaschiert, sondern als Fehler behandelt.

**Souveränitätsprofil**

Lokal betreibbar, damit für sensible Intranet- oder Sovereign-Deployments operativ attraktiv. Mit einem Sovereignty Gap von -1.37 Punkten liegt es nur 1.37 Punkte unter dem Fleet-Ø von 67.84 und bleibt damit fleet-nah konkurrenzfähig.

**Fazit & Empfehlung**

Geeignet für lokale Coding-Agents, IDE-nahe Automationen und MCP-Pipelines mit enger Tool-Validierung, Schema-Prüfung und nachgelagerter Ergebniskontrolle. Nicht geeignet für vollautonome Recherche-, Compliance- oder Entscheidungs-Pipelines, in denen die textliche Synthese selbst der vertrauensrelevante Output ist. Wer es einsetzt, sollte Tool-Calls hart validieren und finale Antworten gegen den tatsächlichen Tool-Output prüfen.