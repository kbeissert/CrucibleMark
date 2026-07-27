**Deployment-Urteil**

> **Erstellt am:** 19.07.2026, 23:28:10


Bedingt deploy, weil die Tool-Ausführung oft stark ist, das Modell aber mit ungültigen Tool-Calls und schwacher Synthesetreue das Vertrauen in eine MCP-Pipeline noch nicht stabil genug absichert. Der Combined-Score von 60.17 ist dafür nur ein Warnsignal, nicht die Hauptursache.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz, aber keine verlässliche Protokolldisziplin. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es P1 95. Das spricht gegen bloßes Schema-Folgen. Es erkennt also häufig, welches Werkzeug zur Aufgabe passt. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL und den anschließenden Fetch misst, landet es bei P1 80. Das ist brauchbar, aber nicht deterministisch genug für produktive Automationsketten.

Kritisch bleibt der globale Befund Tool-Call valide: false. Damit ist nicht die Werkzeugwahl das Hauptproblem, sondern die Übergabe an die Infrastruktur. In einer MCP-Pipeline zählt genau dieser letzte Meter. Ohne valide Calls helfen gute Absichten bei der Tool-Selektion wenig. Positiv ist, dass kein Retry erforderlich war. Das sieht daher eher nach punktueller Format- oder Ausführungsunsauberkeit aus als nach grundlegendem Aufgabenmissverständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 49.17 zeigt, dass aus abgerufenen Quellen oft keine belastbare, präzise Zusammenfassung entsteht. Das sieht man besonders bei EU License Research mit P2 20 und bei Web Search & Tool Selection mit P2 35. Besser ist es bei URL Construction & Fetch und Multilingual Search & Synthesis mit jeweils P2 80 beziehungsweise 60, aber die Gesamtlinie bleibt uneinheitlich.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Bild widersprüchlich und sicherheitsrelevant. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination markiert. Gleichzeitig steht global Halluzination erkannt: true. Für den Produktionseinsatz ist das kein Qualitätsmangel, sondern ein Vertrauensbruch. Wenn ein Modell erfundene Fakten als Tool-Ergebnis erscheinen lässt, verliert die gesamte Tool-Infrastruktur ihre Nachweisbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlschlagenden Tool-Call misst, halluziniert das Modell keinen Ersatzinhalt. Das ist der richtige Grundreflex. P2 40 zeigt aber, dass die Fehlerkommunikation nicht sauber genug verdichtet wird. Für Produktion ist das akzeptabel, solange die Orchestrierung solche Fehler explizit abfängt und an den Nutzer weiterreicht.

**Fazit & Empfehlung**

Geeignet für assistierte Recherche-Pipelines mit Human-in-the-Loop, explorative Agentenläufe und mehrsprachige Suchaufgaben, bei denen gute Werkzeugwahl wichtiger ist als perfekte Ergebnisverdichtung. Nicht geeignet für Compliance-, Lizenz-, Governance- oder andere Nachweispipelines, in denen jeder Tool-Call valide sein und jede Antwort streng an den abgerufenen Inhalt gebunden bleiben muss. Vor produktivem Einsatz braucht dieses Modell harte Schema-Validierung, Output-Guardrails und eine nachgelagerte Verifikation der Synthese.