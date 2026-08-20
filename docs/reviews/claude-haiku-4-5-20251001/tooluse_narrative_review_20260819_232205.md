**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:22:05


Bedingt deploy, weil die Tool-Nutzung operativ meist funktioniert, aber ein invalider Tool-Call und das Halluzinationssignal bei nur moderater Gesamtleistung das Vertrauen in eine produktive MCP-Pipeline begrenzen.

**Tool-Execution-Profil**

Claude Haiku 4.5 wählt Werkzeuge grundsätzlich intelligent statt rein schematisch. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis zwischen Suche und direktem Abruf unterschieden wird, erkennt es den Bedarf für web_search sauber. Das spricht für brauchbare Werkzeugwahl in offenen Aufgaben. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, arbeitet es nur teilweise präzise. Die URL-Konstruktion ist brauchbar, aber nicht deterministisch genug für Pipelines, in denen der erste Call sitzen muss. Kritisch ist der Befund, dass der Tool-Call insgesamt nicht durchgängig valide war. Das ist kein Retry-Thema, sondern ein Protokoll- und Ausführungsrisiko: Das Modell versteht offenbar die Tool-Form grundsätzlich, produziert sie aber nicht stabil genug für unbeaufsichtigte Übergabe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. Die Verdichtungsqualität liegt sichtbar unter der Ausführungsqualität. Das sieht man an EU License Research, URL Construction & Fetch und Multilingual Search & Synthesis: Das Modell holt die Informationen oft an, komprimiert sie aber unpräzise, lässt Relevantes weg oder zieht zu schwache Schlussfolgerungen. Für produktive Tool-Pipelines ist das problematisch, weil der Mehrwert der Infrastruktur erst in der sauberen Verarbeitung der Ergebnisse entsteht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert es nicht. Das ist der wichtigste Vertrauenspunkt. Gleichzeitig steht auf Run-Ebene ein Halluzinationssignal im Befund. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Pipeline.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, erfindet Claude Haiku 4.5 keinen Seiteninhalt. Das ist die Mindestanforderung für Produktion und hier erfüllt. Die Kommunikation des Fehlschlags bleibt jedoch nur mäßig klar. Akzeptabel für überwachte Workflows, aber nicht stark genug für autonome Ketten mit harten Folgeentscheidungen.

**Betriebsprofil**

Call 1: 5.26s. MCP-Latenz: 1.18s. Call 2: 3.67s. Total: 60.68s.  
Preis: $1.0/M Input, $5.0/M Output.  
Direkte Einordnung: günstiges Modell, aber die End-to-End-Laufzeit ist für die gelieferte Zuverlässigkeit nicht überzeugend schnell.

**Fazit & Empfehlung**

Geeignet für kostenbewusste, überwachte Assistenz- und Recherchepipelines, in denen Tool-Auswahl wichtiger ist als präzise Endverdichtung und ein Mensch die Antwort prüft. Nicht geeignet für Compliance-, Retrieval- oder Entscheidungsstrecken, die protokollstabile Tool-Calls und strikte Treue zu Tool-Ergebnissen verlangen. Wenn Sie es einsetzen, dann mit strikter Schema-Validierung, Output-Checks und einer zweiten Verifikationsstufe nach jedem kritischen Tool-Ergebnis.