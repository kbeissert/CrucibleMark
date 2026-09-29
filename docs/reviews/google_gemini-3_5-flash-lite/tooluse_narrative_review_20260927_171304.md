**Deployment-Urteil**

> **Erstellt am:** 27.09.2026, 17:13:04


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Combined 73.88 nur dann tragfähig ist, wenn nachgelagerte Validierung die Ergebnisverdichtung absichert. Halluzination wurde nicht erkannt, aber der Tool-Call war nicht durchgehend valide.

**Tool-Execution-Profil**

Gemini 3.5 Flash Lite arbeitet grundsätzlich agentisch brauchbar. P1 88.33 zeigt, dass es MCP-gestützte Abläufe meist korrekt anstößt. Besonders stark ist es beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis search statt fetch gewählt werden muss: P1 95. Das spricht für echte Werkzeugwahl statt starrem Muster. Beim URL-Construction-Test, der die korrekte Ziel-URL aus eigenem Wissen ableiten und dann fetch ausführen soll, fällt es auf P1 80 zurück. Es kann also Werkzeuge intelligent auswählen, ist aber weniger deterministisch, wenn es erst die Zieladresse selbst konstruieren muss. Für produktive Pipelines heißt das: Discovery gut, präzise Adressbildung nur mit Guardrails. Kritisch bleibt, dass der Tool-Call nicht vollständig valide war. Das ist kein Totalausfall, aber ein Integrationssignal für strikte Schema-Prüfung und Tool-Wrapper.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. P2 60 ist der klare Schwachpunkt dieses Laufs. Das Modell extrahiert und kombiniert Ergebnisse oft brauchbar, aber nicht präzise genug für Compliance-, Policy- oder andere textkritische Workflows. Die Schwäche zeigt sich besonders bei EU License Research und Multilingual Search & Synthesis mit jeweils P2 40, also gerade dort, wo Quelltreue über Sprach- oder Aktualitätsgrenzen hinweg zählt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist der zentrale Vertrauenspunkt. Trotzdem ist P2 40 ein Warnsignal: Es erfindet nichts, verdichtet das beschaffte Material aber zu unscharf, um regulatorische Aussagen ohne Kontrolle freizugeben.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, hat das Modell keinen Ersatzinhalt halluziniert. Das ist für Produktion akzeptabel. P2 60 zeigt jedoch, dass die Fehlerkommunikation eher ausreichend als sauber ist. Für robuste Pipelines ist das tragbar, solange der Orchestrator Fehlerzustände selbst sichtbar macht und nicht nur auf die Modellformulierung vertraut.

**Betriebsprofil**

Total 28.06s. Einzelaufrufe 1.65s und 1.87s. MCP-Latenz 1.16s. Schnell auf Call-Ebene, aber kein kurzer End-to-End-Run. Preis: local. Für die gezeigte Leistung kostenseitig unkritisch.

**Fazit & Empfehlung**

Geeignet für volumenstarke Agentik mit Suche, Fetch, Vorstrukturierung und transparenter Fehlerbehandlung. Nicht geeignet als alleinige letzte Instanz für Compliance, Lizenzprüfung, mehrsprachige Evidenzsynthese oder andere Pipelines, in denen die textliche Verdichtung selbst entscheidungsrelevant ist. Deploy sinnvoll als schneller Tool-Operator mit strenger Output-Validierung, Schema-Enforcement und optionalem Second-Pass durch ein präziseres Modell.