**Deployment-Urteil**

> **Erstellt am:** 22.06.2026, 21:33:53


Bedingt deploy, weil das Modell brauchbare Tool-Ausführung zeigt, aber mit ungültigem Tool-Call und schwacher Synthesetreue kein verlässlicher Endpunkt für autonome MCP-Pipelines ist.

**Tool-Execution-Profil**

Das Ausführungsprofil ist auf den ersten Blick solide. Der Tool-Execution-Score von 78.33 zeigt, dass das Modell Werkzeuge meist zweckmäßig einsetzt. Besonders wichtig: Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, wählt es mit P1=100 erkennbar das richtige Werkzeug. Das spricht gegen bloßes Musterfolgen und für echte Werkzeugwahl im Kontext.

Beim URL-Construction-and-Fetch-Test, der die eigenständige Ableitung einer Ziel-URL misst, bleibt es mit P1=80 brauchbar, aber nicht deterministisch genug für fragile Produktionspfade. Der globale Befund „Tool-Call valide: False“ wiegt deshalb schwerer als die Teil-Scores. Das Modell versteht den Ablauf meist, hält ihn aber nicht durchgehend protokollkonform ein. Positiv ist, dass kein Retry erforderlich war. Das Problem liegt daher eher in der Erstpräzision des Calls als in grundlegendem Missverständnis des MCP-Schemas.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 50.00 ist der eigentliche Bremsfaktor dieses Modells. In einfachen Abruf- und Extraktionsaufgaben bleibt die Verdichtung noch brauchbar, aber nicht scharf. Bei EU License Research, das aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, fällt die Zusammenführung mit P2=40 klar ab. Noch kritischer ist Multilingual Search and Synthesis mit Combined 28. Für mehrsprachige Recherche- und Berichtspipelines ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil vorsichtig positiv. Im Honeypot EU License Research wurde keine Halluzination erkannt. Das Modell hat also das Vertrauensfundament nicht gebrochen. Trotzdem liefert es keine saubere, belastbare Verdichtung der beschafften Inhalte. Für Compliance-nahe Workflows ist das besser als freies Erfinden, aber noch nicht gut genug für ungeprüfte Übergabe.

**Fehlerresilienz**

Akzeptabel für Produktion mit Aufsicht. Beim 404-Test, der prüft, ob ein fehlgeschlagener Tool-Call transparent behandelt wird, halluziniert das Modell keinen Ersatzinhalt. P2=60 ist kein Glanzwert, aber die Reaktion bleibt ehrlich. Das ist der entscheidende Punkt. Ein Modell, das Fehler sichtbar macht statt Seiteninhalt zu erfinden, lässt sich mit Guardrails und Fehlerpfaden betreiben.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Mit 64.08 Combined liegt es 3.85 Punkte unter dem Fleet-Ø von 67.93. Das ist konkurrenzfähig genug für lokale Tool-Orchestrierung, aber nicht stark genug, um Qualitätsdefizite in der Synthese zu kaschieren.

**Fazit & Empfehlung**

Geeignet für lokal betriebene MCP-Pipelines, in denen das Modell primär Werkzeuge auswählt, Abrufe anstößt und Fehler transparent meldet. Nicht geeignet als autonomer Abschlussagent für Compliance, mehrsprachige Recherche oder präzise Executive Summaries. Empfehlung: als orchestrierender Zwischenagent mit nachgelagerter Validierung oder zweitem Synthese-Schritt einsetzen, nicht als alleinige Instanz für finale Nutzerantworten.