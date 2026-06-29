**Deployment-Urteil**

> **Erstellt am:** 29.06.2026, 00:47:18


Bedingt deploy, weil GLM-5.2 stark in der Tool-Ausführung ist, aber mit erkannter Halluzination und nicht validem Tool-Call kein uneingeschränkt vertrauenswürdiger Kandidat für MCP-Pipelines mit harten Korrektheitsanforderungen ist.

**Tool-Execution-Profil**

GLM-5.2 zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung zuverlässig. Das spricht für brauchbare Planungslogik in dynamischen Pipelines. Auch bei EU License Research arbeitet es korrekt tool-basiert statt aus dem Stand zu antworten.

Schwächer wird es bei der Protokollschärfe. Der Tool-Call war insgesamt nicht valide, obwohl kein Retry nötig war. Das deutet eher auf Format- oder Argumentpräzision als auf ein Verständnisproblem. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar, aber nicht robust genug für deterministische Abläufe. Für produktive MCP-Setups heißt das: gute Tool-Wahl, aber die Call-Schicht braucht Guardrails, Schema-Validierung und im Zweifel serverseitige Korrektur.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mäßig. Die P2-Leistung ist mit 55.83 der klare Schwachpunkt. GLM-5.2 holt Informationen aus Tools, verdichtet sie aber nicht konsistent präzise weiter. Das sieht man besonders bei Web Search & Tool Selection und Multilingual Search & Synthesis, wo die Ausführung stark ist, die nachgelagerte Zusammenführung aber sichtbar an Genauigkeit verliert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es im akzeptablen Bereich. Dieser Test prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen geholt statt aus Trainingswissen behauptet werden. Content-Verification-State A und keine Halluzination sind hier ein Vertrauenssignal. Der globale Halluzinationsbefund bleibt trotzdem ein Sicherheitsrisiko: Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert GLM-5.2 produktionstauglich. Im 404-Test, der transparentes Fehlermanagement statt erfundenem Seiteninhalt misst, kommuniziert das Modell den Fehlschlag sauber und halluziniert keinen Ersatzinhalt. Das ist für operative Systeme akzeptabel und deutlich wichtiger als elegante Formulierungen.

**Betriebsprofil**

Total 159.79s. Langsam.  
Call 1 4.59s, Call 2 21.21s, MCP-Latenz 0.83s.  
Kosten pro Run 0.047017. Eher günstig für Frontier-Betrieb, aber die Laufzeit ist im Verhältnis zur Leistung hoch.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen Tool-Wahl, lange Kontexte und transparentes Fehlerverhalten wichtiger sind als perfekte Endverdichtung. Nicht geeignet für Compliance-, Policy- oder Customer-facing-Systeme, in denen jede Synthese direkt als verlässlicher Output gelten muss. Wenn Sie GLM-5.2 einsetzen, dann hinter strikter Tool-Call-Validierung, mit Output-Prüfung und vorzugsweise als ausführende Agentenschicht, nicht als letzte wahrheitsführende Instanz.