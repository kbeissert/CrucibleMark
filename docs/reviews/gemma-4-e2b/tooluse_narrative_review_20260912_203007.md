**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:30:07


Bedingt deploy: Das Modell zeigt brauchbare Tool-Orientierung, ist aber wegen ungültiger Tool-Calls und schwacher Synthesetreue nicht vertrauenswürdig genug für autonome MCP-Pipelines.

**Tool-Execution-Profil**

Gemma 4 E2B erkennt Werkzeugbedarf nicht nur schematisch, sondern mit echter Situationsanpassung. Beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis search statt fetch gewählt wird, trifft es die Werkzeugwahl sicher. Auch beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, arbeitet es grundsätzlich korrekt, aber nicht präzise genug für strikt deterministische Abläufe. Das Gesamtbild ist damit besser als der Rohwert vermuten lässt: Das Modell versteht, wann Suche nötig ist und wann direkter Abruf reicht.

Der operative Haken liegt nicht in der Auswahl, sondern in der Protokolltreue. Tool-Call valide steht auf false. Für Produktionsbetrieb heißt das: Die Planungslogik ist brauchbar, die Übergabe an die MCP-Infrastruktur aber nicht stabil genug. Da kein Retry erforderlich war, spricht das eher für unzuverlässige Ausführungsausgabe als für ein bloßes Formatproblem nach dem ersten Versuch.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung ist der Hauptgrund gegen einen breiten Einsatz. Solide Werte bei HTTP Fetch & Extract sowie bei URL Construction & Fetch zeigen, dass das Modell einzelne Tool-Ergebnisse noch ordentlich zusammenziehen kann. Sobald die Aufgabe aber mehr Auswahl, Grenzfälle oder Mehrsprachigkeit verlangt, bricht die Verdichtungsqualität sichtbar ein.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gemischt. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, erzielt das Modell P2=0. Positiv ist nur, dass keine Halluzination markiert wurde. Negativ ist das eigentliche Produktionssignal: Es liefert keine belastbare, quellengebundene Verdichtung genau dort, wo Compliance-nahe Aktualität entscheidend ist.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt prüft, halluziniert es keinen Seiteninhalt. Das ist für Produktion wichtig. Ein fehlgeschlagener Call beschädigt damit nicht automatisch die Faktengrundlage der gesamten Antwort. Die Fehlerkommunikation ist nicht stark, aber ausreichend sicher.

**Souveränitätsprofil**

Lokal betreibbar mit Apache-2.0-Gewichten und damit souverän einsetzbar. Mit 59.25 Combined liegt es 8.50 Punkte unter dem Fleet-Ø von 67.75. Der Vorteil ist Kontrolle über Laufzeit und Datenpfad, nicht fleet-kompetitive Tool-Leistung.

**Fazit & Empfehlung**

Geeignet für lokale, datensensible Pipelines mit Mensch-in-der-Schleife, klaren Werkzeugpfaden und geringer Compliance-Last. Nicht geeignet für autonome Recherchestrecken, mehrsprachige Synthese, Lizenz- oder Policy-Prüfungen und allgemein für Pipelines, in denen MCP-Calls strikt valide und inhaltlich belastbar verdichtet werden müssen. Wenn Sie es einsetzen, dann als kostengünstigen lokalen Executor unter enger Guardrail- und Post-Validation-Schicht.