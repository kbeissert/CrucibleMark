**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:48:58


Bedingt deploy, weil die Tool-Aufrufe grundsätzlich valide sind und die Tool-Ausführung solide wirkt, das Modell aber mit erkannter Halluzination im Syntheseschritt das Vertrauensniveau für produktive Tool-Pipelines klar begrenzt.

**Tool-Execution-Profil**

Grok 4 (Non-Reasoning) zeigt brauchbare Werkzeugnutzung. Die Calls sind valide, MCP-konform und mit P1 82.50 klar über der Schwelle für ernsthafte Pipeline-Nutzung. Besonders stark ist es beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis das passende Recherche-Tool gewählt wird: P1 95 spricht für echte Tool-Intelligenz statt reiner Schema-Nachahmung. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableitet und dann fetch ausführt, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Fetch-Ketten. Das Muster ist also nicht starr. Das Modell erkennt den Unterschied zwischen Suchbedarf und Direktabruf meist richtig, verliert aber etwas Präzision, sobald es die Zieladresse selbst konstruieren muss.

Dass ein Retry erforderlich war, wirkt hier eher wie ein Ausführungs- oder Formatproblem als wie ein grundlegendes Verständnisdefizit. Die Validität der finalen Tool-Calls spricht gegen ein systemisches Protokollproblem.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 54.17 ist für ein Frontier-Generalist-Modell zu schwach, und die Spannweite zwischen HTTP Fetch & Extract mit P2 80 und Multilingual Search & Synthesis mit P2 15 zeigt eine instabile Verdichtungsqualität. Das Modell kann extrahierte Fakten ordentlich zusammenführen, verliert aber schnell Präzision, sobald mehrdeutige oder mehrsprachige Quellenlagen verdichtet werden müssen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im EU License Research-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, liegt P2 bei 15, Content-Verification-State bei B2, und Halluzination wurde erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene oder vortrainierte Fakten als Ergebnis einer Tool-Recherche ausgibt, unterläuft es die Kontrollfunktion der gesamten MCP-Infrastruktur.

**Fehlerresilienz**

Hier ist das Modell belastbar. Im Tool Failure Handling (404)-Test, der transparentes Verhalten bei fehlgeschlagenem Abruf misst, kommuniziert es den Fehler sauber und halluziniert keinen Ersatzinhalt. P2 100 und keine Halluzination trotz 404 sind für Produktion ein klares positives Signal. Fehlertoleranz ist vorhanden, Vertrauensdisziplin aber nicht durchgehend.

**Betriebsprofil**

Call 1: 5.44s. MCP-Latenz: 1.18s. Call 2: 3.69s. Total: 61.88s.  
Für die erzielte Leistung langsam.  
Kosten pro Run: 0.029169.  
Für Frontier-API-Nutzung moderat bepreist, aber nicht günstig im Verhältnis zur gemessenen Synthesetreue.

**Fazit & Empfehlung**

Geeignet für tool-gestützte Assistenzpipelines, in denen das Modell suchen, abrufen und Fehler transparent melden soll, und in denen ein nachgelagerter Verifikationsschritt die Antwort prüft. Nicht geeignet für Compliance-, Policy-, Research- oder mehrsprachige Wissenspipelines, in denen das Tool-Ergebnis selbst die Vertrauensquelle sein muss. Wenn Sie Grok 4 (Non-Reasoning) einsetzen, dann als Tool-Operator mit externer Ergebnisprüfung, nicht als verlässliche Instanz für finale faktengebundene Synthese.