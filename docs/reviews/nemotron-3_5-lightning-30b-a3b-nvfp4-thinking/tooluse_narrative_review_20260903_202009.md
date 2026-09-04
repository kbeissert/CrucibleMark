**Deployment-Urteil**

> **Erstellt am:** 03.09.2026, 20:20:09


Bedingt deploy, weil die Tool-Ausführung stark ist, aber der Lauf mindestens einen Halluzinationsbefund enthält und die Tool-Calls nicht durchgängig valide waren. Für produktive MCP-Pipelines reicht das nur mit harten Guardrails.

**Tool-Execution-Profil**

NVIDIA Nemotron 3.5 Lightning 30B zeigt ein klar agentisches Profil. Es erkennt im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheidet, zuverlässig, dass web_search statt fetch nötig ist. Das spricht gegen bloßes Schema-Folgen und für echte Werkzeugwahl. Auch bei Multilingual Search & Synthesis und EU License Research greift es die Tool-Schicht korrekt an.

Schwächer wird es bei der formalen Zuverlässigkeit der Aufrufe. Tool-Call valide: False ist für MCP-Betrieb ein Warnsignal, selbst bei P1 90. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann fetch ausführen lässt, arbeitet es brauchbar, aber nicht deterministisch genug für Infrastrukturen, die exakt reproduzierbare Calls erwarten. Das Muster ist damit klar: gute Tool-Entscheidung, weniger saubere Protokollausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt. P2 55.83 ist der eigentliche Engpass dieses Modells. Die Rohbeschaffung funktioniert, aber bei der Verdichtung verliert es Präzision, vor allem bei HTTP Fetch & Extract und EU License Research, also genau dort, wo Jahreszahlen, Eigennamen und regulatorische Details sauber zusammengeführt werden müssen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellwissen beantwortet werden, bleibt es zwar ohne Halluzination im sicheren Bereich. Das ist positiv. Gleichzeitig steht auf Run-Ebene Halluzination erkannt: True. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparentes Scheitern gegen erfundenen Ersatzinhalt prüft, reagiert das Modell akzeptabel. Es halluziniert trotz Fehler keinen Seiteninhalt. P2 40 zeigt allerdings, dass die Kommunikation des Fehlers nicht besonders stark verdichtet oder hilfreich formuliert ist. Für Produktion ist das tolerierbar, weil Transparenz hier wichtiger ist als Eleganz.

**Betriebsprofil**

Call 1: 4.59s. MCP-Latenz: 1.82s. Call 2: 20.22s. Total: 159.78s. Langsam für die erzielte Synthesequalität. Kosten/Run: local. Günstig im Betrieb, aber zeitlich teuer.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Retrieval-, Search- und Orchestrierungs-Pipelines, in denen ein nachgelagerter Validator Antworten gegen Tool-Rohdaten prüft und ungültige Calls abfängt. Nicht geeignet für Compliance-, Regulatorik- oder Executive-Summary-Pipelines, in denen die Modellantwort selbst als verlässliche Endverdichtung dienen soll. Wer dieses Modell einsetzt, sollte es als Ausführungsschicht behandeln, nicht als letzte Instanz der Wahrheit.