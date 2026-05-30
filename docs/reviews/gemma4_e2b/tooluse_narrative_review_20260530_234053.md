**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:53


Bedingt deploy, weil Gemma 4 2B valide Tool-Calls produziert und operativ steuerbar bleibt, aber die Synthesetreue mit Combined 67.75 und erkanntem Halluzinationssignal nicht stabil genug für vertrauenskritische Pipelines ist.

**Tool-Execution-Profil**

Auf der Ausführungsebene ist das Modell belastbar. P1 liegt bei 90.00, die Tool-Calls sind valide und es brauchte keinen Retry. Das spricht für saubere MCP-Anbindung und dafür, dass das Modell das Protokoll nicht erst über Formatkorrekturen lernen muss.

Bei der Werkzeugwahl zeigt es mehr als bloßes Schema-Folgen. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, erreicht es P1 100. Das ist ein gutes Signal für dynamische Pipelines, in denen das Modell den Informationszugang selbst wählen muss. Schwächer ist es beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen ableitet und dann fetch ausführt: P1 80. Das reicht für brauchbare Calls, aber nicht für deterministische Abläufe, in denen URL-Präzision selbst geschäftskritisch ist. Das Muster ist klar: Das Modell wählt Tools intelligent, aber es konstruiert Eingaben nicht immer präzise genug.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 liegt bei 45.83. Besonders sichtbar ist das bei EU License Research mit P2 40 und bei Multilingual Search & Synthesis ebenfalls mit P2 40. Das Modell ruft Informationen ab, verdichtet sie danach aber oft zu grob, lässt wichtige Einschränkungen liegen oder verliert Präzision in der Zusammenführung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau das prüft, bleibt es innerhalb des abgerufenen Materials. Content-Verification-State A und keine Halluzination in diesem Test sind ein starkes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnisse ausgeben kann, wird nicht nur die Antwort schwächer, sondern die Integrität der gesamten Infrastruktur angegriffen.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlschlagenden Tool-Aufruf misst, reagiert Gemma 4 2B akzeptabel. P2 60 ist nicht elegant, aber entscheidend ist: Es halluziniert keinen Seiteninhalt trotz Fehler. Für Produktion ist genau das die Mindestanforderung. Das Modell kommuniziert Grenzen, statt fehlende Daten zu erfinden.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Setups praktisch nutzbar. Gleichzeitig liegt es 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist nah genug für kosten- und datensensible Edge-Deployments, aber kein Beleg für volle Fleet-Konkurrenzfähigkeit.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit klaren Tool-Grenzen, moderatem Risiko und nachgelagerter Validierung, etwa Recherche-Vorstufen, Routing, einfache Extraktion und fehlertolerante Assistenten. Nicht geeignet für Compliance, Policy, Vertrags- oder andere High-Trust-Workflows, in denen die verbale Verdichtung selbst verbindlich ist. Wenn Sie Gemma 4 2B einsetzen, dann als günstigen lokalen Executor mit strikter Kontrolle über die finale Synthese, nicht als letzte Instanz der inhaltlichen Wahrheit.