**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:26:02


Bedingt deploy, weil Gemma 3 4B valide Tool-Calls produziert und in der Ausführung stark ist, aber mit erkannter Halluzination in der Ergebnissynthese das Vertrauensmodell einer Tool-Pipeline verletzt. Der kombinierte Wert liegt nur im moderaten Bereich, und das Risiko sitzt nicht im Aufruf, sondern in der Darstellung der Resultate.

**Tool-Execution-Profil**

Bei der Tool-Nutzung wirkt das Modell überraschend diszipliniert. Es produziert valide Calls, bleibt MCP-konform und brauchte keinen Retry. Das ist für ein Nano-Modell ein belastbares Signal. Besonders stark ist es im Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis das richtige Recherche-Tool statt eines direkten Fetch gewählt wird. Dort zeigt es echte Werkzeugwahl und nicht nur starres Schema-Folgen. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Fetch misst, bleibt es brauchbar, aber nicht präzise genug für vollständig deterministische Abläufe. Das Profil lautet daher: gute Tool-Intelligenz bei der Auswahl, etwas weniger Präzision bei der selbst konstruierten Eingabe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist mit 40.83 klar der schwache Teil des Profils. Besonders die Tests EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis zeigen, dass aus korrekt beschafften Quellen keine verlässlich dichte, faktennahe Zusammenführung entsteht. Das Modell kommt an Daten heran, hält sie aber in der Verdichtung nicht stabil genug fest.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, und das ist der kritische Befund. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt statt aus Trainingswissen ergänzt werden, wurde Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Aussagen als Tool-Ergebnis ausgibt, verliert die gesamte Infrastruktur ihre Nachprüfbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, bleibt das Modell auf der akzeptablen Seite. Es halluziniert keinen Seiteninhalt trotz Fehler. Die P2 ist auch hier nicht stark, aber der entscheidende Punkt ist erfüllt: Es ersetzt fehlende Daten nicht durch erfundene Fakten. Für Produktion ist genau diese Transparenz wichtiger als sprachliche Eleganz.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Umgebungen attraktiv. Leistungsseitig bleibt es jedoch 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist konkurrenzfähig für einfache lokale Tool-Strecken, aber nicht stark genug, um Qualitätsrisiken durch reine Betriebsnähe zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, kostenarme Pipelines mit enger Aufgabengrenze: Tool-Auswahl, Fetch-Ausführung, einfache Routing- oder Vorverarbeitungsschritte mit nachgelagerter Validierung. Nicht geeignet für Compliance-, Research- oder Entscheidungs-Pipelines, in denen die sprachliche Zusammenfassung bereits als verlässliches Endprodukt dienen soll. Wenn Sie es einsetzen, dann als ausführendes Frontend mit hartem Guardrail auf die Ausgabe und mit einem zweiten Prüfschritt für jede inhaltliche Synthese.