**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:10:47


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber der Tool-Call nicht durchgängig valide war und die Synthesequalität für verlässliche produktive Verdichtung nur mittel belastbar ist. Der Gesamteindruck ist gut, aber nicht robust genug für unkontrollierte Agentenpfade.

**Tool-Execution-Profil**

Das Modell zeigt grundsätzlich brauchbare Tool-Kompetenz. P1 von 88.33 spricht dafür, dass es Werkzeuge nicht nur erkennt, sondern meist operativ sinnvoll einsetzt. Für eine MCP-Pipeline ist aber der Befund „Tool-Call valide: false“ der zentrale Vorbehalt. Das heißt: Die Ausführung war leistungsnah, aber nicht strikt protokollfest. In produktiven Ketten ist genau das oft die Trennlinie zwischen brauchbar und wartungsintensiv.

Zu den Auswahltests fehlen Asset-Einzelwerte, deshalb lässt sich die Werkzeugwahl nicht fein auseinandernehmen. Aus dem Gesamtbild folgt dennoch: Das Modell wirkt nicht wie ein reiner Schablonenfolger. Die hohe P1-Leistung bei gleichzeitig fehlender voller Validität deutet eher auf vorhandene Tool-Intelligenz mit Format- oder Präzisionsschwächen hin als auf blindes Immer-Fetch-Verhalten. Positiv ist, dass kein Retry erforderlich war. Das senkt den Orchestrierungsaufwand.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher ordentlich als stark. P2 von 63.33 reicht für einfache Zusammenfassungen, Extrakte und kurze Ergebnisaufbereitung. Für Compliance, Policy, Security oder mehrstufige Recherche ist das zu knapp. Dort braucht man präzise Verdichtung ohne semantisches Wegdriften.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist ein gutes Vertrauenssignal. Es beweist nicht hohe Präzision, aber es spricht dafür, dass das Modell die Tool-Infrastruktur nicht aktiv unterläuft.

**Fehlerresilienz**

Im Test Tool Failure Handling (404), der transparenten Umgang mit einem fehlgeschlagenen Abruf gegen erfundenen Ersatzinhalt misst, halluzinierte das Modell keinen Seiteninhalt. Das ist für Produktion wesentlich. Ein Modell darf bei Fehlern unvollständig sein. Es darf nicht so tun, als hätte das Tool geliefert. Gemma 4 bleibt hier auf der akzeptablen Seite.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Umgebungen attraktiv. Gleichzeitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist ein kleiner Abstand und zeigt: Der lokale Betrieb kostet hier keine massive Tool-Qualität. Für regulierte Umgebungen ist das ein echter Pluspunkt.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit menschlicher Kontrolle, klaren Tool-Schemas und Aufgaben wie Recherche, Extraktion und operative Assistenz. Nicht erste Wahl für vollautonome Pipelines, in denen jede Tool-Antwort deterministisch protokollkonform und jede Synthese hochpräzise sein muss. Wenn Sie es einsetzen, dann mit strikter Call-Validierung, Output-Checks und enger Begrenzung der Freitext-Synthese.