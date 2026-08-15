**Deployment-Urteil**

> **Erstellt am:** 15.08.2026, 12:31:51


Bedingt deploy, weil die Tool-Ausführung stark ist und keine Halluzination erkannt wurde, aber die Tool-Calls nicht durchgängig valide waren und die Synthese für produktionskritische Auswertung zu ungleichmäßig bleibt.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt blindem Standardmuster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis prüft, ob web_search statt fetch nötig ist, wählt es das richtige Werkzeug konsequent. Das spricht für brauchbare Orchestrierungsintelligenz in dynamischen MCP-Pipelines. Auch bei Multilingual Search & Synthesis und EU License Research ruft es externe Quellen aktiv ab, statt vorschnell aus Vorwissen zu antworten.

Die Schwäche liegt nicht in der Entscheidung für Tools, sondern in der operativen Präzision einzelner Calls. Beim URL-Construction-Test, der korrekte Ziel-URL plus anschließenden Fetch verlangt, war die Ausführung nur brauchbar, nicht deterministisch genug. Das passt zum Befund tool_call_valid=false: Das Modell versteht die Pipeline, arbeitet aber nicht auf jedem Schritt protokollsicher. Für produktive Systeme heißt das: gute Kandidatur als Agenten-Front-End, aber nur mit Guardrails, Schema-Validierung und enger Tool-Call-Kontrolle.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht belastbar auf hohem Präzisionsniveau. Die P2-Leistung von 70 zeigt: Es fasst Treffer verwertbar zusammen, verliert dabei jedoch Struktur und Genauigkeit, sobald mehrere Quellen oder mehrsprachige Inputs verdichtet werden müssen. Das sieht man auch daran, dass mehrere Recherche-Assets bei starker Tool-Nutzung nur auf mittlere Synthesequalität kommen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Signal besser. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das Vertrauensurteil ist daher positiv, aber nicht maximal: Es bleibt grundsätzlich an den eingeholten Quellen, verdichtet diese jedoch nicht immer mit der Präzision, die für Compliance- oder Policy-Pipelines nötig wäre.

**Fehlerresilienz**

Akzeptabel für Produktion. Beim 404-Test, der prüft, ob ein Modell bei Tool-Fehlern transparent bleibt statt Seiteninhalt zu erfinden, kommuniziert Gemini 3.7 Flash den Fehlschlag ohne halluzinierten Ersatzinhalt. Das ist ein harter positiver Befund. Fehler werden als Fehler behandelt, nicht überdeckt.

**Betriebsprofil**

Total 51.49s pro Run. Einzelaufrufe 2.08s und 5.44s. MCP-Latenz 1.07s. Schnell auf Call-Ebene, aber als End-to-End-Run nicht kurz. Kosten/Run: local.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und Agentenpipelines, in denen Tool-Wahl wichtiger ist als hochwertige Endverdichtung. Weniger geeignet für Compliance, regulatorische Zusammenfassungen oder andere Workflows, in denen die Antwort selbst als belastbares Endprodukt dienen muss. Deploy nur mit strikter Tool-Call-Validierung, Antwortschema und nachgelagerter Prüfung der Synthese.