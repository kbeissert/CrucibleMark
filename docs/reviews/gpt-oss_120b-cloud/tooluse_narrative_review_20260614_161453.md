**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:14:53


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Synthesetreue aber für produktive Wissens- und Compliance-Pipelines nicht ausreicht. Der kombinierte Befund ist nur moderat, obwohl die Tool-Calls valide waren und kein Retry nötig war.

**Tool-Execution-Profil**

Das Modell kann mit MCP-gestützten Werkzeugen arbeiten. Die Calls sind valide, protokollkonform und ohne Wiederholung durchgelaufen. Das ist die zentrale Eintrittskarte für produktive Tool-Pipelines.

Bei **Web Search & Tool Selection**, also dem Test, ob ohne Hinweis web_search statt fetch gewählt wird, erkennt das Modell den richtigen Werkzeugtyp sicher. Das spricht gegen bloßes Schema-Folgen und für echte Werkzeugwahl im Kontext. Beim **URL Construction & Fetch**, also dem Test, ob es eine Ziel-URL selbst herleiten und dann korrekt abrufen kann, bleibt es brauchbar, aber nicht durchgehend präzise genug für deterministische Flows. Das Muster ist klar: gute Auswahl des Werkzeugtyps, etwas weniger Verlässlichkeit bei der letzten Meile der Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Genau hier liegt das Hauptproblem. **HTTP Fetch & Extract** ist noch solide, und beim **URL Construction & Fetch** erreicht es auch in der Verdichtung ein gutes Niveau. Aber **EU License Research** fällt mit P2=0 vollständig aus, **Tool Failure Handling (404)** bleibt schwach, und **Multilingual Search & Synthesis** verdichtet nur unsauber. Für Architekturen, in denen das Modell Tool-Ergebnisse knapp, korrekt und überprüfbar zusammenführen muss, ist das ein harter Grenzwert.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist negativ. Im **EU License Research**-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, ist der Content-Verification-State nur B2 bei P2=0. Zusätzlich ist global eine Halluzination erkannt worden. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene oder nicht sauber belegte Fakten als Tool-Ergebnis ausgibt, verliert die Pipeline ihre Auditierbarkeit.

**Fehlerresilienz**

Beim **Tool Failure Handling (404)**, also dem Test auf transparenten Umgang mit fehlgeschlagenem Abruf, halluziniert das Modell keinen Seiteninhalt. Das ist produktionsrelevant positiv. Die Antwortqualität bleibt mit P2=20 schwach, aber das entscheidende Verhalten stimmt: Es erfindet keinen Ersatzinhalt, wenn das Tool scheitert.

**Betriebsprofil**

Total 72.82s. Langsam.  
MCP-Latenz 1.24s, Call 1 3.37s, Call 2 7.52s.  
Kosten pro Run 0.002596. Günstig.  
Im Verhältnis zur Leistung: ökonomisch attraktiv, aber zeitlich schwer für interaktive oder hochvolumige Pipelines.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines, in denen das Modell primär Werkzeuge auswählt, Calls korrekt absetzt und Ergebnisse an nachgelagerte Validatoren oder strukturierte Parser übergibt. Nicht geeignet für Compliance-, Research- oder Executive-Summary-Pipelines, in denen die vom Modell formulierte Synthese selbst als vertrauenswürdiges Endprodukt dienen soll. Wenn Sie es einsetzen, dann nur mit strikter Ergebnisprüfung, Quellenbindung und einem zweiten Kontrollschritt vor jeder fachlichen Ausgabe.