**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:20:51


Bedingt deploy, weil die Tool-Ausführung meist stark ist, aber die Synthesetreue zu unzuverlässig bleibt und der Tool-Call im Lauf nicht durchgängig valide war.

**Tool-Execution-Profil**

Qwen 3.6 Plus zeigt echte Werkzeugintelligenz statt bloßer Schablonen-Nutzung. Beim Web Search & Tool Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr sicher. Auch beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus internem Wissen und anschließendes fetch misst, arbeitet es brauchbar, aber weniger deterministisch. Das spricht für flexible Planung, nicht für starres Musterfolgen.

Für eine MCP-Pipeline ist das Bild trotzdem nicht vollständig sauber. P1 ist mit 68.33 solide, aber das Signal „Tool-Call valide: false“ ist relevant. Das heißt praktisch: Das Modell versteht den Ablauf meist, produziert aber nicht in jedem Schritt protokollsaubere Aufrufe. Da kein Retry nötig war, liegt das Problem eher in Ausführungspräzision als in grundsätzlichem Missverständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt zuverlässig. P2 liegt bei 50.00, und die Streuung ist hoch. HTTP Fetch & Extract ist noch ordentlich, Tool Failure Handling (404) und URL Construction & Fetch sind gut, aber EU License Research fällt in der Verdichtung deutlich ab. Kritisch ist vor allem Multilingual Search & Synthesis: Bei sprachübergreifender Recherche mit deutscher Zusammenfassung bricht die Qualität stark ein. Für Pipelines, die knappe, belastbare Ergebnisverdichtung brauchen, ist das zu schwankend.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert es nicht. Das ist das wichtigste Vertrauenssignal. Der P2-Wert von 40 zeigt aber, dass es das beschaffte Material nicht sauber genug in eine belastbare Antwort überführt. Vertrauen in die Herkunft ist also besser als Vertrauen in die Verdichtung.

**Fehlerresilienz**

Beim 404-Test, der transparentes Scheitern gegen erfundenen Ersatzinhalt abgrenzt, reagiert Qwen 3.6 Plus produktionsgerecht. Es kommuniziert den Fehlschlag statt Seiteninhalt zu erfinden. Das ist für reale Tool-Ketten akzeptabel und deutlich wichtiger als stilistische Antwortqualität.

**Betriebsprofil**

Total 248.76s pro Run. Call 1 6.54s, Call 2 34.23s, MCP-Latenz 0.68s. Langsam für die gezeigte Leistung. Preis: $0.325 pro 1M Input-Tokens, $1.95 pro 1M Output-Tokens. API-seitig günstig bis moderat, aber die Laufzeit verschlechtert die Wirtschaftlichkeit.

**Fazit & Empfehlung**

Geeignet für agentische Recherche-Pipelines mit menschlicher Nachkontrolle, besonders dort, wo Tool-Auswahl und transparente Fehlerbehandlung wichtiger sind als perfekte Endverdichtung. Nicht geeignet für Compliance-, Policy- oder mehrsprachige Synthese-Pipelines, in denen die letzte Antwort ohne Review direkt weiterverarbeitet wird. Zusätzlich ist das Cloud-only-Betriebsmodell unter chinesischer Jurisdiktion für sensible Tool-Daten ein eigenständiger Ausschlussgrund.