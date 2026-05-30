**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:34


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, die Synthese aber zu oft vom Quellmaterial wegdriftet und damit das Vertrauen in eine MCP-Pipeline nur für eng geführte Workflows trägt.

**Tool-Execution-Profil**

Bei der Werkzeugnutzung wirkt GPT OSS 120B Cloud kompetent. Die Calls sind valide, MCP-konform und kamen ohne Retry aus. Das ist die wichtigste Eintrittskarte für produktiven Tool-Einsatz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, erkennt das Modell den Bedarf nach web_search sauber. Das spricht gegen bloßes Musterfolgen und für echte Werkzeugwahl. Beim URL-Construction-Test, der die Ziel-URL aus Vorwissen ableiten und dann korrekt abrufen lässt, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. P1 ist insgesamt stark, doch die Unterschiede zwischen Suche und URL-Ableitung zeigen: Es plant besser, als es präzise konstruiert.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist mit 39.17 der klare Schwachpunkt. Bei HTTP Fetch & Extract verdichtet es brauchbar, bei URL Construction & Fetch sogar solide. Aber bei Tool Failure Handling (404), das transparente Fehlerkommunikation statt erfundenem Ersatzinhalt misst, und bei Multilingual Search & Synthesis fällt die Verdichtung deutlich ab. Für produktive Pipelines heißt das: Das Modell kann Informationen holen, aber nicht durchgehend zuverlässig in belastbare Endantworten überführen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Genau hier liegt das Sicherheitsrisiko. Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen zwingend aus Web-Quellen statt aus Trainingswissen verlangt, erreicht es bei der inhaltlichen Verifikation P2=0. Auch ohne explizit erkannte Halluzination in diesem Einzeltest ist der Gesamtbefund mit gesetztem Halluzinationsflag kritisch: Sobald ein Modell erfundene oder unzureichend belegte Aussagen als Tool-Ergebnis ausgibt, bricht die Vertrauenskette der gesamten Infrastruktur.

**Fehlerresilienz**

Im 404-Test reagiert das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz fehlgeschlagenem Abruf. Das ist produktionsrelevant. Die Schwäche liegt nicht im Umgang mit Tool-Fehlern, sondern in der schwachen Weiterverarbeitung des Fehlzustands zur Nutzerantwort. Transparente Fehlerkommunikation ist vorhanden, aber nicht sauber genug verdichtet.

**Betriebsprofil**

3.37s bis zum ersten Call, 7.52s bis zum zweiten Call, 72.82s gesamt. Damit operativ langsam. MCP-Latenz 1.24s. Kosten pro Run 0.002596 USD. Damit günstig. Preis-Leistung nur dann gut, wenn hohe Laufzeit tolerierbar ist.

**Fazit & Empfehlung**

Geeignet für agentische Retrieval-Pipelines mit harter Nachkontrolle, strukturierter Ausgabevalidierung und möglichst wenig freier Synthese. Nicht geeignet für Compliance-, Policy-, Research- oder Executive-Summary-Pipelines, in denen die Endantwort selbst das vertrauensrelevante Artefakt ist. Wer dieses Modell einsetzt, sollte es als Tool-Operator behandeln, nicht als verlässlichen Synthese-Layer.