**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:19:00


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Synthese aber zu oft unpräzise bleibt und damit bei produktiven Entscheidungs-Pipelines ein Vertrauensrisiko erzeugt. Der kombinierte Befund ist nur moderat, obwohl Tool-Calls valide waren und kein Retry nötig war.

**Tool-Execution-Profil**

GPT-4o Mini verhält sich auf MCP-Ebene solide. Die Tool-Calls sind valide, protokollkonform und ohne Nachbesserung ausführbar. Das ist für produktive Verkettung wichtiger als sprachliche Eleganz.

Bei der Werkzeugwahl zeigt das Modell aber nur begrenzte operative Intelligenz. Im Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erreicht es zwar brauchbare Ausführung, aber die nachgelagerte Qualität bricht stark ein. Das spricht nicht für robuste Situationsdiagnose, sondern eher für funktionales Abarbeiten. Beim Test URL Construction & Fetch, der die korrekte URL-Ableitung aus eigenem Wissen misst, arbeitet es ebenfalls brauchbar. Das Muster ist klar: Wenn der Pfad erkennbar ist, liefert es. Wenn die Wahl des richtigen Werkzeugs selbst Teil der Aufgabe ist, sinkt die Verlässlichkeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist der Schwachpunkt des Modells. Sehr gut ist HTTP Fetch & Extract, also strukturierte Extraktion aus realem Seiteninhalt. Schwach ist dagegen die eigentliche Verdichtung in offenen Rechercheaufgaben. Besonders Web Search & Tool Selection und Multilingual Search & Synthesis zeigen, dass das Modell gefundene Inhalte nicht stabil in präzise, entscheidungstaugliche Antworten überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, halluziniert es nicht. Das ist ein positives Vertrauenssignal. Gleichzeitig bleibt der Content-Verification-State nur auf B2 bei P2 40. Das Modell bleibt also eher innerhalb des abgerufenen Materials, verdichtet es aber nicht präzise genug. Der gesetzte Halluzinationsbefund im Gesamtlauf ist deshalb als Sicherheitsrisiko zu lesen: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Ergebnisrahmen ausgibt, wird die Infrastruktur als Ganzes fraglich.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlschlagende Tool-Calls misst, erfindet GPT-4o Mini keinen Seiteninhalt. Das ist akzeptables Produktionsverhalten. Die Kommunikation des Fehlschlags ist nicht optimal verdichtet, aber sie bleibt ehrlich. Für Betriebspipelines ist das deutlich wichtiger als eine glatte Antwort.

**Betriebsprofil**

Total 39.51s. Einzelaufrufe 1.87s und 3.56s. MCP-Latenz 1.16s. Schnell genug für interaktive Tool-Pipelines, nicht für enge Echtzeitketten. Kosten pro Run: $0.001794. Sehr günstig im Verhältnis zur gebotenen Tool-Execution, aber nur angemessen bei tolerierbarer Syntheseunsicherheit.

**Fazit & Empfehlung**

Geeignet für kostensensitive MCP-Pipelines mit klaren Werkzeugpfaden, extraktiver Verarbeitung und nachgelagerter Validierung. Nicht geeignet als alleinige Instanz für Compliance, mehrsprachige Recherche-Synthese oder dynamische Agentenflüsse, in denen das Modell selbst Werkzeugwahl und Ergebnisverdichtung zuverlässig beherrschen muss. Wenn Sie GPT-4o Mini einsetzen, dann als günstigen Executor mit enger Guardrail-Führung, nicht als vertrauenswürdigen Synthese-Kern.