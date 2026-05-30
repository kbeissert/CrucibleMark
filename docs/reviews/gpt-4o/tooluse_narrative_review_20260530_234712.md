**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:47:12


Bedingt deploy, weil GPT-4o valide Tool-Calls erzeugt und operativ sicher genug für MCP-Pipelines wirkt, aber die Synthesetreue mit Combined 66.83 und erkanntem Halluzinationssignal nicht stabil genug für faktenkritische Ausgaben ist.

**Tool-Execution-Profil**

Bei der Tool-Ausführung arbeitet GPT-4o klar über Mindestniveau. Die Calls sind valide, MCP-protokollkonform und ohne Retry lauffähig. Das wichtigste Signal ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der prüft ob das Modell ohne Hinweis erkennt, dass statt fetch eine Suche nötig ist, erreicht es P1 100. Das spricht für echte Situationsanpassung statt starrem Call-Muster. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus eigenem Wissen misst, landet es bei P1 80. Es kann also bekannte Pfade oft brauchbar konstruieren, aber nicht präzise genug für strikt deterministische Fetch-Pipelines. Insgesamt ist das Tool-Verhalten produktionsreif, solange nachgelagerte Validierung fehlerhafte oder unvollständige Retrieval-Pfade abfängt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt zuverlässig. P2 48.33 ist der eigentliche Engpass dieses Modells im Tool-Stack. Besonders schwach ist Multilingual Search & Synthesis, also grenzüberschreitende Recherche mit deutscher Ausgabe, mit P2 15. Auch HTTP Fetch & Extract bleibt mit P2 35 deutlich unter dem, was man für belastbare Extraktion aus Seiteninhalten erwartet. GPT-4o holt Daten oft korrekt ab, reduziert sie dann aber zu grob, lässt relevante Details fallen oder verdichtet zu frei.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, bleibt es formal im abgerufenen Material. Halluzination wurde dort nicht erkannt. Das ist ein wichtiges Vertrauenssignal. Gleichzeitig bleibt das globale Halluzinationsflag ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnis ausgibt, wird nicht nur die Antwort, sondern die gesamte Infrastruktur unglaubwürdig.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei scheiternden Tool-Aufrufen misst, reagiert GPT-4o akzeptabel. P2 80 und keine halluzinierten Seiteninhalte zeigen: Es meldet den Fehlschlag statt Ersatzinhalt zu erfinden. Das ist für Produktion entscheidend, weil Fehler sichtbar bleiben und orchestrierende Systeme sauber weiterentscheiden können.

**Betriebsprofil**

Total 23.68s pro Run. Call-Latenzen 0.71s und 2.19s, MCP-Latenz 1.05s. Eher langsam für den gemessenen Qualitätsgrad. Kosten pro Run: $0.032734. Günstig bis moderat, aber nicht klar unterpreisig relativ zur Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für allgemeine MCP-Pipelines, in denen das Modell Tools auswählen, Aufrufe sauber ausführen und Fehler transparent zurückgeben soll. Nicht geeignet als letzte Instanz für Compliance, mehrsprachige Recherche-Synthese oder präzise Faktenverdichtung ohne zusätzliche Verifikation. Empfehlung: als Retrieval- und Orchestrierungsmodell mit striktem Guardrail-Setup einsetzen, nicht als vertrauenswürdige Endredaktion für toolgestützte Faktenausgaben.