**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:38:58


Bedingt deploy, weil die Tool-Ausführung stark ist und valide MCP-Calls produziert, das Modell aber mit erkannter Halluzination und nur mäßiger Synthesetreue kein blind vertrauenswürdiger Endpunkt für faktenkritische Pipelines ist.

**Tool-Execution-Profil**

Mistral Medium 3.5 zeigt ein klares Produktionsprofil auf der Ausführungsseite. P1 mit 89.17 spricht dafür, dass es Tools zuverlässig ansteuert und formal gültige Aufrufe erzeugt. Der gesetzte Validitätsbefund bestätigt das. Für MCP-gestützte Umgebungen ist das die notwendige Basis: Das Modell versteht die Infrastruktur und bricht nicht schon am Protokoll.

Weniger klar ist, wie intelligent die Werkzeugwahl im Detail ausfällt, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelwerte vorliegen. Deshalb lässt sich nicht belastbar sagen, ob es dynamisch zwischen web_search und fetch unterscheidet oder primär einem festen Muster folgt. Der Retry-Befund wirkt hier eher wie ein Robustheits- als ein Verständnisproblem. Bei einem Modell mit validen Calls und hoher P1 ist ein erforderlicher zweiter Anlauf typischerweise ein Format- oder Ablaufproblem, nicht ein grundlegendes Versagen der Tool-Logik.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 mit 55.00 ist der klare Schwachpunkt. Das Modell kann Informationen offenbar einsammeln, verdichtet sie aber nicht konsistent präzise genug für Antworten, die ohne Nachkontrolle in eine Produktionskette zurückgeschrieben werden sollten. Genau dort entsteht das Risiko: nicht beim Zugriff auf Daten, sondern bei ihrer textlichen Rückübersetzung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen bezogen werden, hat es nicht halluziniert. Das ist ein gutes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko. In einer Tool-Pipeline zählt nicht nur, ob das Modell Tools nutzt, sondern ob jede behauptete Tatsache sauber auf Tool-Ausgaben zurückführbar bleibt.

**Fehlerresilienz**

Im 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Calls prüft, hat Mistral Medium 3.5 keinen Ersatzinhalt erfunden. Das ist für Produktion akzeptabel. Ein Modell darf an einem Tool scheitern. Es darf dabei nur nicht so tun, als hätte es trotzdem verwertbaren Seiteninhalt gesehen. Diese Grenze hält es hier ein.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Gegenüber der Fleet bleibt es konkurrenzfähig, liegt aber mit -5.32 Punkten unter dem Fleet-Ø von 66.76. Das ist nah genug für ernsthafte EU- oder On-Prem-Entscheidungen, aber kein Sonderfall mit klarer Leistungsreserve.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit starker Tool-Orchestrierung, klaren Zwischenschritten und nachgelagerter Validierung. Besonders sinnvoll, wenn lokaler Betrieb, Open Weights und europäische Herkunft harte Anforderungen sind. Nicht geeignet als unbeaufsichtigter Synthese-Endpunkt für Compliance, Research-Briefings oder andere faktenkritische Antworten mit direkter Außenwirkung. Deploy als Tool-Operator, nicht als letzte Wahrheitsinstanz.