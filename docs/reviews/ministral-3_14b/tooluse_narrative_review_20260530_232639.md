**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:39


Bedingt deploy, weil die Tool-Aufrufe valide und meist treffsicher sind, das Modell aber im Honeypot belegbar auf Trainingswissen ausweicht und damit das Vertrauen in eine Tool-Pipeline verletzt.

**Tool-Execution-Profil**

Die Ausführungsseite ist die klare Stärke. Mit P1 90 zeigt Ministral 14B, dass es MCP-konforme Tool-Calls erzeugen kann. Der Aufruf war valide, ein Retry war nicht nötig. Das spricht gegen ein Protokoll- oder Formatproblem.

Bei der Werkzeugwahl zeigt das Modell echte situative Unterscheidung statt bloßes Schema-F. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es P1 100. Das ist ein starkes Signal für produktive Pipelines mit wechselnden Informationsquellen. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Fetch-Ketten. Es kann also Werkzeuge intelligent auswählen, arbeitet bei selbst konstruierten Zieladressen jedoch weniger präzise als bei der reinen Tool-Entscheidung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Mit P2 50.83 ist die Verdichtung oft zu grob oder nicht eng genug am Quellmaterial. Das sieht man besonders bei EU License Research und Web Search & Tool Selection, wo die Ausführung stark ist, die inhaltliche Verdichtung aber jeweils nur P2 15 erreicht. Besser wirkt es bei URL Construction & Fetch mit P2 100 und bei Multilingual Search & Synthesis mit P2 60.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das Produktionsrisiko. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellgedächtnis kommen, wurde eine Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsproblem. Sobald ein Modell erfundene oder vorgelernte Fakten als Ergebnis einer Recherche ausgibt, ist die Nachvollziehbarkeit der gesamten Infrastruktur beschädigt.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell brauchbar. Im 404-Test, der Transparenz bei einem gescheiterten Abruf misst, erreicht es P2 80 und halluziniert keinen Seiteninhalt. Genau das ist für Produktion akzeptabel: Fehler offen benennen, statt Ersatzinhalt zu erfinden.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Gleichzeitig liegt es mit einem Sovereignty Gap von -5.32 Punkten unter dem Fleet-Ø von 66.76. Das ist konkurrenzfähig genug für lokale Tool-Ausführung, aber nicht stark genug, um den Vertrauensverlust in der Synthesis zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokal laufende, kostenkritische Pipelines, in denen das Modell primär Tools auswählt, Aufrufe formuliert und Fehler sauber weiterreicht. Nicht geeignet für Compliance-, Research- oder Entscheidungs-Pipelines, in denen die Antwort selbst als verlässliche Verdichtung von Tool-Ergebnissen dienen muss. Wenn Sie es einsetzen, dann als ausführende Orchestrierungsschicht mit harter Downstream-Validierung und ohne Freigabe für unbeaufsichtigte faktische Synthese.