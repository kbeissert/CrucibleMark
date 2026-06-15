**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:10:01


Bedingt deploy, weil die Tool-Aufrufe valide und ohne Halluzinationsbefund bleiben, die Synthesequalität mit Combined 63.21 aber nicht stabil genug für vertrauenskritische Auswertungspipelines ist.

**Tool-Execution-Profil**

Auf der Ausführungsseite arbeitet das Modell brauchbar. Es erzeugt valide Tool-Calls und zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, liegt es mit P1 95 sehr stark. Das spricht dafür, dass es dynamische Informationslücken erkennt und nicht reflexhaft fetch auf bekannte Muster ansetzt. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Abruf misst, fällt es mit P1 80 etwas ab. Das ist noch produktionsfähig, aber nicht deterministisch genug für fragile URL-basierte Workflows.

Dass ein Retry erforderlich war, wirkt hier eher wie ein Robustheits- oder Formatproblem im Ablauf als wie ein fundamentales Verständnisdefizit. Die Protokollseite bricht nicht. Für MCP-gestützte Pipelines ist das akzeptabel, solange ein automatischer Wiederholungsmechanismus vorhanden ist.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 46.67 ist der klare Schwachpunkt dieses Laufs. Das Modell kann gefundene Informationen zusammenführen, verliert dabei aber Präzision und Priorisierung. Das sieht man auch an den stark auseinanderlaufenden Asset-Werten: HTTP Fetch & Extract und URL Construction & Fetch sind mit P2 60 brauchbar, EU License Research fällt mit P2 20 deutlich ab. Für reine Retrieval- und Routing-Aufgaben genügt das. Für Compliance, Lizenzbewertung oder entscheidungsnahe Zusammenfassungen genügt es nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Vertrauenssignal positiv. P2 20 ist inhaltlich schwach, aber Halluzination wurde nicht erkannt und der Verifikationsstatus ist sauber. Das Modell dichtet also nicht frei hinzu. Es verdichtet nur zu unzuverlässig.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlschlagende Tool-Aufrufe prüft, halluziniert das Modell keinen Ersatzinhalt. Das ist der entscheidende Punkt. P2 40 zeigt, dass die Fehlerkommunikation nicht besonders nützlich oder vollständig ist, aber sie bleibt ehrlich. Für Produktion ist das akzeptabel. Ein System kann auf dürre Fehlermeldungen reagieren. Es kann nicht sicher auf erfundene Inhalte reagieren.

**Souveränitätsprofil**

Lokal betreibbar und damit operativ attraktiv für souveräne Umgebungen. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist kein Ausreißer nach unten. Für ein lokales Desktop-Modell ist es damit konkurrenzfähig, aber nicht überdurchschnittlich.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen das Modell Tools auswählen, Web-Inhalte abrufen und Ergebnisse vorsichtig weiterreichen soll. Gut passend für Recherche-Vorstufen, mehrsprachige Suche und assistive Orchestrierung mit menschlicher oder regelbasierter Nachprüfung. Nicht geeignet als letzte Instanz für Compliance, Lizenzinterpretation, Executive Summaries oder andere Pipelines, in denen die Verdichtung der Tool-Ergebnisse selbst entscheidungstragend ist. Wer dieses Modell einsetzt, sollte Retrieval und Synthesis strikt trennen und die Endauswertung außerhalb des Modells absichern.