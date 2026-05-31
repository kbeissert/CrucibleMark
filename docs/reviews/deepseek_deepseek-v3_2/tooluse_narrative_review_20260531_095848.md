**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:58:48


Bedingt deploy, weil die Tool-Ausführung produktionsreif wirkt, die Synthesequalität aber nur begrenzt belastbar ist. Mit validen Tool-Calls, keiner erkannten Halluzination und 74.67 Combined ist das Modell für überwachte Tool-Pipelines tragfähig, nicht aber für unbeaufsichtigte High-Trust-Synthese.

**Tool-Execution-Profil**

DeepSeek V3.2 zeigt ein starkes Tool-Verhalten. P1 liegt bei 90, der Tool-Call war valide und ein Retry war nicht nötig. Das spricht für saubere MCP-Konformität und gegen ein Formatproblem auf Protokollebene.

Wichtig ist die Werkzeugwahl. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht das Modell 100. Das ist ein Signal für echte Tool-Intelligenz und nicht nur für starres Call-Schema. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen und anschließenden Fetch misst, fällt es auf 80. Es kann also Werkzeuge sinnvoll unterscheiden, ist aber bei der letzten Meile der URL-Präzision nicht deterministisch genug für fragile Fetch-Pipelines. Für dynamische Rechercheflüsse ist das gut. Für hart verkettete URL-Muster braucht es Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich, nicht stark. P2 liegt bei 60. Über die Aufgaben hinweg ist das Muster konsistent: brauchbare Zusammenfassung, aber begrenzte Präzision in Verdichtung und Priorisierung. Besonders sichtbar wird das bei Multilingual Search & Synthesis, wo die sprachübergreifende Recherche gelingt, die deutsche Endverdichtung aber auf 40 fällt. Für Entscheidungsgrundlagen sollte man daher Quellzitate, Schema-Outputs oder einen zweiten Prüfschritt vorsehen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell im Tool-Pfad. Content-Verification-State A und keine erkannte Halluzination sind das entscheidende Vertrauenssignal. Es ist also kein Modell, das bei aktueller Compliance-Recherche stillschweigend auf Trainingswissen zurückfällt.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Call misst, reagiert das Modell akzeptabel. P2 80 und keine Halluzination trotz Fehler zeigen: Es erfindet keinen Seiteninhalt, wenn der Fetch scheitert. Genau das ist in Produktion erforderlich. Fehler werden damit handhabbar statt gefährlich.

**Betriebsprofil**

Total 105.20s: langsam.  
Call 1 3.30s, MCP-Latenz 1.05s, Call 2 13.18s.  
Kosten pro Run 0.001770: günstig.  
Im Verhältnis zur Leistung: gute Kostenbasis, aber spürbare Laufzeit für interaktive oder hochparallele Pipelines.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und Fetch-Pipelines, in denen Tool-Wahl, Fehlertransparenz und niedrige Kosten wichtiger sind als exzellente Endverdichtung. Nicht die erste Wahl für Compliance-Briefings, Executive Summaries oder mehrsprachige Synthese ohne nachgelagerte Validierung. Empfehlung: als Tool-Operator und Informationssammler einsetzen, nicht als alleinige Instanz für die finale, entscheidungsreife Zusammenfassung.