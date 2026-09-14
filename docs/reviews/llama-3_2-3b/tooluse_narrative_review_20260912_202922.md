**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:29:22


Nicht deploy für autonome MCP-Pipelines, weil das Modell bei schwacher Gesamtleistung, ungültigen Tool-Calls und erkannter Halluzination die Vertrauenskette zwischen Tool-Ausgabe und Modellantwort nicht stabil hält.

**Tool-Execution-Profil**

Das Modell zeigt punktuell Werkzeugintelligenz, aber keine verlässliche Protokolldisziplin. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, liegt die Ausführung stark bei P1 95. Das spricht dafür, dass es den Charakter einer Rechercheaufgabe oft korrekt erkennt. Diese Stärke setzt sich aber nicht in präzise Folgeausführung um. Beim Test URL Construction & Fetch, der die korrekte Ableitung einer Ziel-URL und den anschließenden Abruf misst, fällt es auf P1 35 zurück. Das ist kein bloßes Wissensproblem, sondern ein Umsetzungsproblem an der Schnittstelle zwischen Planung und gültigem Aufruf. Auch HTTP Fetch & Extract bleibt mit P1 35 schwach. Da der Tool-Call insgesamt als nicht valide gewertet wurde und kein Retry nötig war, liegt der Befund eher bei mangelnder Erstpräzision als bei einem bloßen Formatfehler, den ein zweiter Versuch beheben würde.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 31.67 ist der eigentliche Ausschlussgrund für produktive Tool-Pipelines. Das Modell kann Informationen beschaffen oder den richtigen Retrieval-Modus erkennen, verdichtet die Resultate aber oft nicht belastbar. Besonders sichtbar wird das bei Web Search & Tool Selection und Multilingual Search & Synthesis: hohe P1-Werte, aber jeweils nur P2 15. Damit bricht der Nutzen der Tool-Nutzung am letzten Schritt, nämlich der korrekten Überführung in eine verwertbare Antwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht verlässlich genug. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, ist die Halluzinationsflagge zwar nicht ausgelöst. P2 20 zeigt aber sehr geringe Bindung an die beschafften Inhalte. Da global Halluzination erkannt wurde, ist das als Sicherheitsrisiko zu werten: Wenn ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgibt, verliert die gesamte Infrastruktur ihre Prüfbarkeit.

**Fehlerresilienz**

Hier ist das Modell brauchbar. Im 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt prüft, erreicht es P2 80 und halluziniert keinen Ersatzinhalt. Das ist für Produktion die Mindestanforderung, weil der Fehler sichtbar bleibt und Downstream-Systeme darauf reagieren können.

**Souveränitätsprofil**

Voll lokal betreibbar und damit für sensible Daten attraktiv, aber nicht fleet-kompetitiv. Combined 47.83 liegt 19.92 Punkte unter dem Fleet-Ø von 67.75.

**Fazit & Empfehlung**

Geeignet für lokal souveräne Assistenzpfade mit Mensch-in-der-Schleife, einfache Tool-Router und Fehler-Weitergabe ohne hohe Anforderungen an finale Verdichtung. Nicht geeignet für Compliance-, Research-, Retrieval- oder mehrstufige MCP-Pipelines, in denen das Modell Tool-Ergebnisse präzise übernehmen, korrekt zusammenführen und ohne erfundene Zwischenfakten ausgeben muss. Für produktive Tool-Infrastruktur fehlt hier nicht primär Reichweite, sondern Verlässlichkeit im letzten Meter.