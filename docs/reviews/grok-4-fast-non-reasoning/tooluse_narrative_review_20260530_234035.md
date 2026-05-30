**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:35


Bedingt deploy, weil Grok 4 Fast (Non-Reasoning) zuverlässig valide Tool-Calls liefert und nicht halluziniert, aber die Synthesequalität mit Combined 72.50 und besonders P2 60.00 für belastbare Wissenspipelines zu ungleichmäßig bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist der klare Produktionsanker dieses Modells. Tool-Calls waren valide, MCP-konform und ohne Retry lauffähig. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erkennt das Modell den richtigen Zugriffspfad sauber und zeigt damit echte Werkzeugwahl statt bloßes Schema-Folgen. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen misst, arbeitet es brauchbar, aber weniger deterministisch. Das P1-Signal von 80 zeigt: Es kann die URL oft korrekt konstruieren und fetch ausführen, ist dabei aber nicht präzise genug für Pipelines, in denen URL-Bildung fehlerfrei sein muss. Für agentische Abläufe mit klaren Tool-Grenzen ist das gut. Für fragile Fetch-Ketten mit exakter Pfadbildung braucht es Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur solide. Die P2-Leistung ist der begrenzende Faktor. HTTP Fetch & Extract liegt bei 60, EU License Research bei 40 und Multilingual Search & Synthesis bei 20. Das Muster ist klar: Das Modell kann Ergebnisse zusammenziehen, verliert aber bei verdichteter, mehrsprachiger oder compliance-naher Zusammenfassung zu viel Präzision. Für einfache Ergebnisaufbereitung reicht das. Für belastbare Entscheidungsgrundlagen nicht durchgehend.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil besser als die Formulierungsqualität. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Content-Verification-State A und hallucination_flag false sprechen dafür, dass das Modell am abgerufenen Material bleibt, selbst wenn die Verdichtung schwach ist. Das ist für produktive Tool-Pipelines wichtiger als stilistische Stärke.

**Fehlerresilienz**

Im 404-Test, der den Umgang mit einem scheiternden Tool-Aufruf misst, kommuniziert das Modell den Fehler transparent und erfindet keinen Ersatzinhalt. P2 80 ist hier ein gutes Produktionssignal. Ein fehlgeschlagener Fetch bleibt als Fehler sichtbar. Genau das ist akzeptables Verhalten in einer Tool-Infrastruktur.

**Betriebsprofil**

Call 1: 2.00s. MCP-Latenz: 1.12s. Call 2: 1.99s. Total: 30.67s. Schnell auf Modellebene, aber die Gesamtlaufzeit ist für den erzielten Qualitätsgrad nicht besonders effizient. Kosten pro Run: $0.018736. Günstig bis moderat.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen sichere Tool-Nutzung, korrekte Fehlerbehandlung und niedrige Antwortlatenz wichtiger sind als hochwertige Verdichtung. Gute Passung für Such-Orchestrierung, Fetch-gestützte Assistenz und überwachte Agentenpfade. Nicht die richtige Wahl für Compliance-Auswertung, mehrsprachige Recherche-Synthese oder Pipelines, in denen das Modell Tool-Ergebnisse präzise zusammenfassen und als belastbare Endantwort ausgeben muss. Empfohlen mit nachgelagerter Validierung oder einem stärkeren Synthese-Modell im zweiten Schritt.