**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:38:49


Bedingt deploy, weil GPT-4o Mini valide Tool-Calls erzeugt und die Ausführungsschicht zuverlässig trifft, aber die Synthesetreue mit Combined 66.21 und aktiv erkanntem Halluzinationssignal nicht stabil genug für hochvertrauenswürdige Tool-Pipelines ist.

**Tool-Execution-Profil**

Die Ausführungsseite ist brauchbar. P1 liegt bei 83.33, Tool-Calls waren valide, und es brauchte keinen Retry. Das spricht für saubere MCP-Anbindung und geringe Protokollfriktion im produktiven Betrieb.

Bei der Werkzeugwahl zeigt das Modell aber nur begrenzte Werkzeugintelligenz. Im Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erreicht es zwar P1 80, die sehr schwache inhaltliche Folgequalität zeigt aber, dass die Wahl nicht sicher in eine belastbare Recherchelogik überführt wird. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL plus korrekten Fetch misst, arbeitet es ebenfalls mit P1 80 solide, aber nicht deterministisch genug für fragile Pipelines. Das Muster wirkt daher eher wie brauchbare Standard-Tool-Nutzung als wie robuste adaptive Tool-Planung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 liegt bei 48.33. Stark ist nur HTTP Fetch & Extract, wo reale Seiteninhalte präzise extrahiert und verdichtet werden. Schwach sind dagegen Web Search & Tool Selection und Multilingual Search & Synthesis mit jeweils P2 15. Genau dort, wo mehrere Quellen, Sprachwechsel oder implizite Rechercheentscheidungen zusammenkommen, verliert das Modell Präzision und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, erreicht es nur P2 40 bei Content-Verification-State B2. Zwar wurde dort keine Halluzination markiert, aber global ist Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Tool-Infrastruktur ihre Beweiskraft.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf misst, hat das Modell keinen Seiteninhalt erfunden. P2 60 ist nicht stark, aber die entscheidende Eigenschaft ist vorhanden: Es bleibt bei der Fehlersituation und ersetzt sie nicht durch erfundene Ergebnisse.

**Betriebsprofil**

Call 1: 1.87s. MCP-Latenz: 1.16s. Call 2: 3.56s. Total: 39.51s. Kosten pro Run: $0.001794. Schnell auf Einzelschritten, günstig pro Run, aber die Gesamtdauer ist für die gezeigte Syntheseleistung nicht besonders effizient.

**Fazit & Empfehlung**

Geeignet für kostensensitive MCP-Pipelines mit klaren Tool-Grenzen, einfacher Extraktion, strukturierten Fetch-Aufgaben und expliziter Nachvalidierung. Nicht geeignet für Compliance, mehrsprachige Recherche, offene Web-Recherche oder jede Pipeline, in der die verbale Verdichtung selbst als vertrauenswürdiges Endprodukt gilt. Wenn Sie GPT-4o Mini einsetzen, dann als günstige Tool-Ausführungsschicht mit nachgelagerter Prüfung, nicht als letzte Instanz für synthesisgetriebene Entscheidungen.