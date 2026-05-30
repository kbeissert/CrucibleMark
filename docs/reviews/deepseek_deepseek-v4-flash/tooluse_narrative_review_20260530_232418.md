**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:18


Bedingt deploy, weil die Tool-Aufrufe valide sind und die Ausführung stark wirkt, aber die Synthesetreue mit Combined 67.92 und erkanntem Halluzinationssignal nicht ausreicht, um unbeaufsichtigt kritische Tool-Pipelines zu tragen.

**Tool-Execution-Profil**

DeepSeek V4 Flash ist auf der Ausführungsseite belastbar. P1 von 86.67 spricht dafür, dass es MCP-konform arbeitet, gültige Tool-Calls erzeugt und keine Retry-Schleife brauchte. Das ist für produktive Orchestrierung der wichtigste Basisnachweis.  
Bei der Werkzeugwahl bleibt das Bild unvollständig, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelscores vorliegen. Deshalb lässt sich nicht sauber belegen, ob das Modell situativ zwischen web_search und fetch unterscheidet oder primär einem festen Ausführungsmuster folgt. Positiv ist nur das harte Signal: valide Calls ohne Formatbruch. Für Architekten heißt das, dass die Protokolltreue belastbar erscheint, die eigentliche Tool-Intelligenz aber nicht hinreichend ausgeleuchtet ist.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 51.67 ist der klare Schwachpunkt des Laufs. Das Modell kann offenbar Ergebnisse einsammeln, verliert aber bei der Verdichtung Präzision, Priorisierung oder Quellentreue. Für Pipelines mit nachgelagerter Validierung ist das tolerierbar. Für Systeme, in denen die Modellantwort direkt als Arbeitsgrundlage dient, ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinations-Flag ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Infrastruktur. Hier liegt also kein pauschales Misstrauen gegen die Tool-Nutzung vor, aber auch kein Freifahrtschein für High-Trust-Antworten.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei scheiterndem Tool-Aufruf misst, hat das Modell keinen Seiteninhalt halluziniert. Das ist produktionsgerecht. Ein Tool-Fehler wird damit nicht in still erfundene Antwortsubstanz umgewandelt. Für robuste Pipelines ist dieses Verhalten wichtiger als stilistische Antwortqualität.

**Betriebsprofil**

Call 1: 3.24s. MCP-Latenz: 1.37s. Call 2: 10.21s. Total: 88.90s.  
Kosten pro Run: 0.000933 USD.  
Urteil: günstig, aber für eine Flash-Variante im End-to-End-Lauf klar langsam im Verhältnis zur nur moderaten Gesamtleistung.

**Fazit & Empfehlung**

Geeignet für kostenempfindliche MCP-Pipelines mit klaren Tool-Grenzen, vorgeschalteter Retrieval-Logik und nachgelagerter Ergebnisprüfung. Nicht geeignet für Compliance, regulatorische Recherche, direkte User-Antworten ohne Verifikation oder jede Pipeline, in der die finale Synthese als belastbarer System-of-Record gelten soll. Als Tool-Executor ist es brauchbar. Als vertrauenswürdige letzte Verdichtungsinstanz noch nicht.