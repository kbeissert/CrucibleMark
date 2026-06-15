**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:15:54


Bedingt deploy, weil die Tool-Ausführung stark ist und valide MCP-Calls liefert, aber die erkannte Halluzination im Honeypot das Vertrauen in faktenkritischen Pipelines bricht.

**Tool-Execution-Profil**

Gemini 3.1 Flash Lite Preview arbeitet auf der Ausführungsebene zuverlässig. P1 90 zeigt sich hier auch praktisch: Tool-Calls sind valide, protokollkonform und ohne Retry zustande gekommen. Das ist für MCP-Pipelines ein guter Befund.

Bei der Werkzeugwahl zeigt das Modell echte situative Unterscheidung statt bloß eines starren Fetch-Musters. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die Entscheidung sauber. Im Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus eigenem Wissen prüft, ist es weniger präzise. Das spricht für brauchbare Tool-Intelligenz, aber nicht für deterministische URL-Konstruktion ohne Leitplanken. Für dynamische Recherchepfade ist das gut genug. Für direkte Fetch-Ketten mit vorausgesetzter URL-Exaktheit braucht es enges Prompting oder Vorvalidierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 59.17 ist der klare Schwachpunkt. Das Modell extrahiert und verbindet einfache Befunde ordentlich, etwa bei HTTP Fetch & Extract und bei Multilingual Search & Synthesis. Sobald aktuelle, sensible oder mehrdeutige Informationen sauber zusammengeführt werden müssen, sinkt die Verlässlichkeit sichtbar. Es ist damit eher ein Ausführungsmodell als ein belastbares Synthesemodell.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research nicht. Dieser Test prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen bezogen werden. Das Modell halluziniert hier trotz verfügbarer Tool-Infrastruktur, P2 15. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene Aussagen als Ergebnis einer Recherchekette ausgibt, verliert die gesamte Tool-Pipeline ihre Beweiskraft.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlgeschlagene Tool-Calls prüft, verhält sich das Modell produktionsgerecht. Es kommuniziert den Fehler offen und erfindet keinen Seiteninhalt. P2 80 ist hier ausreichend. Für reale Systeme heißt das: bei Tool-Fehlern eher kontrollierter Abbruch als verdeckte Fiktion.

**Betriebsprofil**

0.57s bis 1.38s Modellaufrufe, 0.84s MCP-Latenz, 16.77s total. Schnell auf Call-Ebene, aber die End-to-End-Zeit bleibt spürbar. Kosten pro Run: $0.004118. Sehr günstig im Verhältnis zur starken Tool-Ausführung, aber die schwächere Synthesis begrenzt den Wert für anspruchsvolle Entscheidungen.

**Fazit & Empfehlung**

Geeignet für volumenstarke MCP-Pipelines mit klaren Werkzeugpfaden, Extraktion, Vorklassifikation, multilingualer Recherche und kontrollierter Fehlerbehandlung. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere faktenkritische Workflows, in denen die Antwort strikt an Tool-Belege gebunden bleiben muss. Wenn Sie es einsetzen, dann als günstigen Executor vor einer zweiten Verifikationsstufe, nicht als letzte Instanz für inhaltliche Wahrheit.