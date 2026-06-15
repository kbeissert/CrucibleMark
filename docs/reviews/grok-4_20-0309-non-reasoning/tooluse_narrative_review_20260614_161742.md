**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:17:42


Bedingt deploy, weil die Tool-Calls überwiegend valide sind und die Tool-Ausführung belastbar wirkt, das Modell aber nachweislich Tool-Ergebnisse mit erfundenem Wissen überlagert und damit für vertrauenskritische Pipelines ausfällt.

**Tool-Execution-Profil**

Grok 4 (Non-Reasoning) zeigt eine klare operative Stärke in der Werkzeugnutzung. Die Tool-Calls sind valide, MCP-konform und die Ausführungsseite ist mit P1 82.50 solide. Besonders wichtig: Beim Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erkennt das Modell den nötigen Werkzeugtyp sehr sicher. Das spricht gegen reines Schema-Folgen und für echte Tool-Selection-Kompetenz. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und anschließendes Fetch misst, arbeitet es ebenfalls brauchbar, aber weniger präzise. Das Muster ist konsistent: Es versteht, wann Suche nötig ist, ist aber bei der direkten Konstruktion konkreter Endpunkte nicht deterministisch genug.

Der erforderliche Retry wirkt hier nicht wie ein Protokollbruch, sondern eher wie ein Stabilitätsproblem in der Ausführungskette. Das ist operativ beherrschbar, erhöht aber Orchestrierungsaufwand und Latenz.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung von 54.17 ist für eine produktive Tool-Pipeline zu schwach, weil sie stark streut. Bei HTTP Fetch & Extract verdichtet es extrahierte Fakten sauber. Bei Multilingual Search & Synthesis und besonders bei EU License Research bricht die Qualität jedoch deutlich ein. Das Modell kann also Rohdaten ziehen, aber nicht durchgehend präzise und quellengebunden zusammenführen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, und genau das ist das Sicherheitsrisiko. Beim EU-License-Research-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, fällt das Modell mit P2 15 und erkannter Halluzination durch. Ein Modell, das in einer MCP-Pipeline erfundene oder vortrainierte Fakten als Tool-Ergebnis ausgibt, beschädigt die Vertrauenskette der gesamten Infrastruktur. Für Compliance-, Regulatorik- oder Policy-Workflows ist das ein harter Ausschlussgrund.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell produktionsgerecht. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Abruf misst, kommuniziert es den Fehler offen und halluziniert keinen Seiteninhalt. Das ist akzeptabel für Produktion und deutlich wichtiger als reine Antwortglätte.

**Betriebsprofil**

Call 1: 5.44s. MCP-Latenz: 1.18s. Call 2: 3.69s. Total: 61.88s.  
Kosten pro Run: $0.029169.  
Fazit: bei Einzellauf moderat schnell, im Gesamtdurchlauf zu lang; günstig bis moderat bepreist, aber nur dann wirtschaftlich, wenn die Pipeline Synthesefehler extern absichert.

**Fazit & Empfehlung**

Geeignet für Tool-first-Pipelines, in denen das Modell primär suchen, abrufen und Fehler transparent melden soll und in denen eine nachgelagerte Validierung die finale Antwort prüft. Nicht geeignet für Compliance-, Rechts-, Lizenz-, Policy- oder mehrsprachige Research-Pipelines, in denen die Antwort strikt an Tool-Befunde gebunden bleiben muss. Wer Grok 4 (Non-Reasoning) einsetzt, sollte es als ausführendes Frontend für Tools behandeln, nicht als vertrauenswürdige letzte Instanz für Synthese.