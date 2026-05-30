**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:16


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Synthese aber nicht konstant genug auf dem Niveau einer hochvertrauenswürdigen Produktionspipeline liegt. Der kombinierte Score von 75.75 ist tragfähig, aber nicht selbstabsichernd.

**Tool-Execution-Profil**

Kimi K2 Thinking verhält sich auf der MCP-Ebene grundsätzlich produktionsfähig. Die Tool-Calls waren valide, und es gibt keinen Befund für Protokollbruch oder erfundene Tool-Ergebnisse. Besonders stark ist der Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird: P1 100 zeigt echte Werkzeugwahl statt starrem Muster. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableitet und dann fetch ausführt, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile URL-Schemata.

Das Retry-Signal wirkt hier eher wie ein Ablauf- oder Formatproblem als wie ein Verständnisfehler. Dafür spricht die insgesamt valide Tool-Nutzung bei gleichzeitig guter Orchestrierung über mehrere Schritte.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber ungleichmäßig. P2 70 insgesamt reicht für operative Zusammenfassungen, vor allem bei HTTP Fetch & Extract mit P2 100 und bei den Such-/Fetch-Aufgaben mit P2 80. Kritisch sind die Einbrüche bei EU License Research und Multilingual Search & Synthesis mit jeweils P2 40. Das Modell findet also Informationen öfter, als es sie anschließend belastbar verdichtet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, ist das Vertrauenssignal gemischt. Es halluziniert nicht, was entscheidend ist. Der Content-Verification-State B2 und P2 40 zeigen aber, dass es sich nicht eng genug an den abgerufenen Beleg hält. Für Compliance-nahe Ketten ist das zu locker.

**Fehlerresilienz**

Im 404-Test, der misst, ob das Modell bei einem fehlgeschlagenen Tool-Call transparent bleibt statt Ersatzinhalt zu erfinden, verhält es sich akzeptabel. P2 80 bei gleichzeitig keiner Halluzination trotz Fehler ist ein produktionsfähiges Signal. Das Modell kommuniziert Ausfallzustände, ohne die Tool-Infrastruktur durch erfundene Inhalte zu unterlaufen.

**Betriebsprofil**

Total 157.28s pro Run. Langsam.  
Call-Latenzen 4.57s und 20.05s, MCP-Latenz 1.60s.  
Kosten 0.005985 pro Run. Günstig.  
Verhältnis zur Leistung: ökonomisch attraktiv, aber zeitlich schwer für interaktive Pipelines.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen korrekte Tool-Wahl, Fehlertransparenz und niedrige Kosten wichtiger sind als enge Belegtreue in der Endverdichtung. Nicht die erste Wahl für Compliance, regulatorische Auskünfte, mehrsprachige Evidenzsynthese oder andere Pfade, in denen jedes Detail aus den Tool-Ergebnissen sauber konserviert werden muss. Mit nachgelagerter Verifikation oder strengem Citation-Checking ist es ein brauchbarer Tool-Operator. Ohne solche Guardrails nicht als alleinige Vertrauensinstanz.