**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:10


Bedingt deploy, weil Gemma 3 12B valide Tool-Calls erzeugt, nicht halluziniert und mit 74.67 insgesamt produktionsnah arbeitet, die Synthesequalität aber sichtbar hinter der Ausführungssicherheit zurückbleibt.

**Tool-Execution-Profil**

Das Modell ist als Tool-Operator belastbar. P1 liegt mit 90 sehr hoch, der Tool-Call war valide und ein Retry war nicht nötig. Das spricht für saubere MCP-konforme Aufrufe ohne Formatdrift. Besonders wichtig: Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis das richtige Recherchewerkzeug gewählt wird, entscheidet es korrekt für Suche statt blindem Fetch. Das ist ein Signal für echte Werkzeugwahl und nicht nur starres Call-Muster.

Weniger stark ist die Präzision beim URL-Construction-Test, der prüft ob das Modell eine Ziel-URL selbst herleiten und dann korrekt abrufen kann. Hier reicht es nur zu 80. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, in denen URL-Ableitung selbst ein kritischer Schritt ist. Für orchestrierte Flows mit vorgelagerter Suche wirkt das Modell klar stärker als für direkte Zieladressierung aus implizitem Wissen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur solide. P2 von 60 zeigt: Das Modell fasst Befunde meist korrekt zusammen, verliert aber bei Verdichtung Details, Nuancen oder Priorisierung. Das sieht man auch an HTTP Fetch & Extract und URL Construction & Fetch, wo die Ausführung hält, die nachgelagerte Verdichtung aber nicht auf gleichem Niveau bleibt. Kritisch ist vor allem Multilingual Search & Synthesis: Die sprachübergreifende Recherche funktioniert, die deutsche Endsynthese fällt mit P2 40 aber zu flach für anspruchsvolle Analysten-Outputs aus.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen geholt werden, bleibt das Modell im Ergebnisraum der Tools. Content-Verification-State A, keine Halluzination. Das ist das zentrale Vertrauenssignal dieses Laufs.

**Fehlerresilienz**

Bei Tool-Ausfall reagiert das Modell produktionsgerecht. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Seiteninhalt prüft, halluziniert es nicht und erreicht P2 80. Das ist akzeptabel für reale Pipelines: Der Fehler wird als Fehler behandelt, nicht mit erfundenem Ersatz verdeckt.

**Souveränitätsprofil**

Lokal betreibbar und dennoch fleet-kompetitiv. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Für ein Desktop-Dense-Modell ist das ein gutes Profil, wenn lokale Ausführung, Datenhoheit und kontrollierbarer Betrieb wichtiger sind als maximale Synthesetiefe.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen verlässliche Tool-Nutzung, korrekte Werkzeugwahl und transparente Fehlerbehandlung wichtiger sind als exzellente Endredaktion. Gut passend für interne Recherche-Flows, Retrieval-gestützte Compliance-Vorprüfungen und lokale Assistenten mit menschlicher Abnahme. Nicht die richtige Wahl für Pipelines, die aus Tool-Ergebnissen bereits publikationsreife, mehrsprachig saubere oder analytisch dichte Synthesen erwarten. Für solche Strecken sollte Gemma 3 12B eher als robuster Tool-Ausführer vor einem stärkeren Synthese-Modell eingesetzt werden.