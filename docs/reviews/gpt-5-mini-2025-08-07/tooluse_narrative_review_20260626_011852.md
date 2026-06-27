**Deployment-Urteil**

> **Erstellt am:** 26.06.2026, 01:18:52


Nicht deploy für MCP-gestützte Tool-Pipelines, weil die Tool-Ausführung unzuverlässig ist, die Tool-Calls nicht valide waren und der Gesamteindruck trotz fehlender Halluzinationen nur schwach ausfällt.

**Tool-Execution-Profil**

Das Kernproblem ist nicht die Antwortformulierung, sondern die Werkzeugbenutzung. GPT-5 Mini hat bei **EU License Research** den Abruf korrekt ausgelöst, fällt aber in fast allen übrigen Tool-Aufgaben aus. Bei **Web Search & Tool Selection**, das ohne Hinweis die Wahl zwischen Suche und direktem Fetch prüft, zeigt es keine belastbare Tool-Intelligenz. P1 bleibt dort bei 0. Dasselbe gilt für **URL Construction & Fetch**, also den Test, ob das Modell eine Ziel-URL selbst präzise ableiten und dann korrekt abrufen kann. Auch hier P1=0.

Das spricht nicht für ein gelegentliches Formatproblem, sondern für ein strukturelles Defizit in dynamischen Tool-Ketten. Es folgt keinem verlässlichen Entscheidungsverfahren für Werkzeugwahl und produziert keine protokolltauglichen Calls über die Aufgabenbreite. Positiv ist nur: Es brach nicht in freie Halluzination aus und es brauchte keinen Retry. Für Produktion reicht das nicht, wenn die Aufrufe selbst nicht tragfähig sind.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt. Der P2-Wert von 20 zeigt, dass GPT-5 Mini gefundene Inhalte meist nur oberflächlich zusammenzieht. In **HTTP Fetch & Extract**, wo präzise Fakten wie Jahreszahlen oder Eigennamen aus echtem Seiteninhalt gezogen werden müssen, bleibt die Verdichtung zu dünn für belastbare Weiterverarbeitung. Das gleiche Muster sieht man in **Multilingual Search & Synthesis**: sprachübergreifende Recherche wird nicht sauber in eine belastbare deutsche Synthese überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im **EU License Research**-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb es auf der sicheren Seite. Keine erkannte Halluzination, kein Ausweichen auf Trainingswissen. Das ist ein Vertrauenssignal, aber kein Freifahrtschein, weil der eigentliche Toolzugriff insgesamt zu oft scheitert.

**Fehlerresilienz**

Im **Tool Failure Handling (404)**-Test reagiert das Modell akzeptabel. Es halluziniert trotz fehlschlagendem Abruf keinen Ersatzinhalt. Das ist für Produktion wichtig, weil ein offener Fehler immer besser ist als erfundener Seiteninhalt. Die Transparenz ist also vorhanden. Die operative Schwäche bleibt dennoch bestehen: Das Modell scheitert häufiger vor oder bei der eigentlichen Tool-Nutzung, als dass diese Resilienz den Gesamtpfad absichern könnte.

**Betriebsprofil**

Total 23.39s pro Run. Davon 2.58s für Call 1, 19.46s für Call 2, 1.36s MCP-Latenz. Für ein Nano-Modell langsam. Kosten lokal ausgewiesen, aber die gegebene API-Preisstruktur ist günstig. Preis passt, Leistung nicht.

**Fazit & Empfehlung**

Geeignet höchstens für streng eingehegte Single-Tool-Flows, in denen das Tool bereits vorgewählt ist und das Modell nur eine knappe, nicht-kritische Zusammenfassung liefern soll. Nicht geeignet für agentische Pipelines, dynamische Tool-Auswahl, URL-Ableitung, Web-Recherche oder mehrsprachige Retrieval-Ketten. Wer diesem Modell eine echte Tool-Infrastruktur übergibt, muss die Werkzeugwahl und Call-Erzeugung außerhalb des Modells hart deterministisch absichern.