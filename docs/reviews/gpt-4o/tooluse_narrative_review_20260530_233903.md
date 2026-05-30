**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:03


Bedingt deploy, weil GPT-4o valide Tool-Calls produziert und operativ sicher genug wirkt, aber die Synthesetreue mit Combined 66.83 und erkanntem Halluzinationsereignis nicht stabil genug für hochvertrauenswürdige Output-Strecken ist.

**Tool-Execution-Profil**

Bei der Tool-Ausführung ist GPT-4o klar produktionsfähig. Die Call-Struktur war valide, retry war nicht erforderlich, und das Modell zeigt mehr als bloßes Musterfolgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es zuverlässig, dass zuerst web_search nötig ist. Das spricht für echte Werkzeugwahl statt starrer fetch-First-Heuristik. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Weltwissen prüft, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. P1 ist insgesamt stark, doch die Unterschiede zwischen 100 bei Werkzeugwahl und 80 bei URL-Konstruktion zeigen die Grenze: Es plant gut, aber es trifft bei selbst konstruierten Zieladressen nicht immer präzise genug.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist der eigentliche Schwachpunkt dieses Laufs. Besonders HTTP Fetch & Extract und Multilingual Search & Synthesis zeigen, dass GPT-4o abgerufene Inhalte nicht konsistent in präzise, vollständige Endantworten überführt. Das ist kein Tooling-Problem, sondern ein Übergabeproblem zwischen Abruf und Antwort. Für produktive MCP-Pipelines heißt das: Die Infrastruktur kann korrekt arbeiten, während die finale Verdichtung trotzdem relevante Details verliert oder unscharf umformt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch bei aktuellen Lizenzrestriktionen prüft, bleibt GPT-4o im Tool-Ergebnis. Halluzination wurde dort nicht erkannt, trotz nur mäßiger P2 von 40. Das ist wichtig. Gleichzeitig bleibt der globale Halluzinations-Flag ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Ergebnis ausgibt, wird nicht nur eine Antwort schwach, sondern die Vertrauenskette der gesamten Infrastruktur beschädigt.

**Fehlerresilienz**

Beim 404-Test reagiert GPT-4o produktionsgerecht. Es kommuniziert den Fehlschlag transparent und erfindet keinen Seiteninhalt. Das ist für Betrieb wichtiger als elegante Formulierung. Ein Modell, das nach Tool-Fehlern sichtbar stoppt statt zu improvisieren, ist integrierbar.

**Betriebsprofil**

Total 23.68s pro Run. Modell-Calls 0.71s und 2.19s, MCP-Latenz 1.05s. Eher langsam im End-to-End-Verhalten. Kosten 0.032734 USD pro Run. Für Frontier-Niveau günstig, gemessen an der nur moderaten Gesamtausbeute aber kein Effizienzvorteil für qualitätskritische Pipelines.

**Fazit & Empfehlung**

Geeignet für allgemeine Tool-Pipelines mit menschlicher Sichtkontrolle, Recherche-Vorstufen, Routing, Web-Zugriff und robuste Fehlerbehandlung. Nicht geeignet für Compliance-nahe, mehrsprachige oder faktenkritische Endausgaben, bei denen Tool-Ergebnisse ohne zusätzliche Verifikation direkt in Nutzer- oder Systementscheidungen eingehen. Wenn Sie GPT-4o einsetzen, dann als zuverlässigen Tool-Bediener mit nachgeschalteter Validierung, nicht als letzte Vertrauensinstanz der Antwort.