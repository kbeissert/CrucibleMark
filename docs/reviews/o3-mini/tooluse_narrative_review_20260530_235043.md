**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:50:43


Bedingt deploy, weil o3-mini die Tool-Infrastruktur sauber bedient und valide Calls liefert, aber die inhaltliche Verdichtung mit Combined 72.79 und gesetztem Halluzinationssignal nicht durchgehend vertrauensfest für sensible Produktionspfade ist.

**Tool-Execution-Profil**

Im Tool-Use ist das Modell stark. P1 bei 90 zeigt keine grundsätzliche Schwäche im MCP-Betrieb. Tool-Calls waren valide, ein Retry war nicht nötig. Das spricht für saubere Protokollführung und stabile Ausführung.

Die Werkzeugwahl wirkt nicht rein schematisch. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erreicht o3-mini P1 100. Es erkennt also den Recherchebedarf zuverlässig. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, fällt es auf P1 80 zurück. Das ist noch brauchbar, aber nicht präzise genug für Pipelines, die aus Modellwissen deterministische Ziel-URLs erwarten. Kurz: stark in der Wahl des richtigen Werkzeugtyps, weniger belastbar bei der letzten Meile der URL-Konstruktion.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 bei 55.83 ist der klare Engpass. Die Ausführung stimmt, die Zusammenführung der gefundenen Inhalte bleibt aber oft zu grob. Das sieht man besonders bei Web Search & Tool Selection mit P2 35 und bei Multilingual Search & Synthesis mit P2 40. Für Extraktion und operative Antwortformate reicht das oft aus. Für Compliance, Policy oder mehrquellige Entscheidungsgrundlagen ist diese Verdichtungsqualität zu instabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau das bei aktuellen Lizenzrestriktionen prüft, bleibt o3-mini im abgerufenen Material. P2 60 ist kein Qualitätsbeweis, aber Content-Verification-State A und keine Halluzination sind ein belastbares Vertrauenssignal. Gleichzeitig bleibt das globale Halluzinationssignal ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Befund ausgibt, ist nicht nur die Antwort, sondern die Infrastrukturkette kompromittiert.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Calls gegen erfundenen Ersatzinhalt misst, verhält sich o3-mini produktionsgerecht. P2 80, keine Halluzination trotz Fehler. Das Modell kommuniziert Ausfälle akzeptabel und erfindet keinen Seiteninhalt. Das ist für reale MCP-Pipelines ein wesentliches Stabilitätssignal.

**Betriebsprofil**

Total 67.24s pro Run: langsam.  
MCP-Latenz 1.51s, Modellaufrufe 2.19s und 7.51s: der Hauptkostenfaktor ist die Gesamtorchestrierung.  
Kosten 0.037873 USD pro Run: günstig bis moderat, gemessen an der Tool-Use-Leistung.

**Fazit & Empfehlung**

Geeignet für recherchierende Tool-Pipelines, in denen korrektes Anstoßen von Suche, Fetch und Fehlerbehandlung wichtiger ist als hochwertige Mehrquellen-Synthese. Gut einsetzbar für Retrieval, Vorstrukturierung, Agenten-Schritte mit menschlicher Nachkontrolle und technische Assistenz mit klaren Guardrails. Nicht erste Wahl für Compliance, Policy-Auslegung, Executive Summaries oder andere Pfade, in denen die Verdichtung selbst als verlässlicher Endbefund dienen muss.