**Deployment-Urteil**

> **Erstellt am:** 16.06.2026, 00:30:11


Bedingt deploy, weil die Tool-Ausführung belastbar ist, das Modell aber trotz validem Tool-Call halluzinierte Inhalte in die Antwortschicht einmischt und damit bei Combined 62.25 kein vertrauenswürdiges End-to-End-Verhalten zeigt.

**Tool-Execution-Profil**

Hermes 4.3 36B Q6_K verhält sich auf MCP-Ebene diszipliniert. Die Tool-Calls sind valide, protokollkonform und brauchten keinen Retry. Das ist für lokale Agent-Pipelines ein relevanter Pluspunkt. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis search statt fetch gewählt wird, erkennt das Modell den richtigen Werkzeugtyp sicher. Das spricht gegen rein schematisches Abarbeiten und für echte Werkzeugwahl. Beim URL-Construction-Test, der die Ableitung einer Zieladresse aus Eigenwissen verlangt, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 zeigt: Es kann die Fetch-Strecke bedienen, aber die Vorstufe URL-Bildung ist die schwächere Stelle. Insgesamt kann man ihm eine Tool-Infrastruktur übergeben, wenn die Pipeline das Endergebnis noch prüft.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 36.67 ist der eigentliche Engpass dieses Modells. Es holt Informationen oft korrekt ein, verliert dann aber Präzision in der Verdichtung. Das sieht man an EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis mit jeweils nur 15 oder 35 Punkten im Synthesis-Teil. Für Pipelines, in denen aus Tool-Output verlässliche Kurzbefunde entstehen sollen, ist das zu instabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, und das ist der kritische Befund. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell trotz Content-Verification-State A. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Ein Modell, das erfundene Fakten als Ergebnis einer Tool-Recherche ausgibt, unterläuft die Vertrauenskette der gesamten MCP-Pipeline.

**Fehlerresilienz**

Beim 404-Test reagiert das Modell produktionsgerecht. Es kommuniziert den Fehlschlag transparent und erfindet keinen Seiteninhalt. P2 80 in diesem Asset ist wichtiger als es auf den ersten Blick wirkt: Wenn ein Tool scheitert, bleibt das Modell innerhalb des beobachtbaren Zustands. Für produktive Orchestrierung ist dieses Verhalten akzeptabel.

**Souveränitätsprofil**

Lokal betreibbar: ja. Fleet-kompetitiv: nur eingeschränkt. Das Modell liegt 1.37 Punkte unter dem Fleet-Ø von 67.84. Der lokale Betrieb ohne externen Datentransfer ist ein klarer Vorteil, die Leistungsdelle gegenüber dem Fleet ist gering. Der Souveränitätsgewinn wird aber durch die schwache Synthesetreue teilweise neutralisiert.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Tool-Pipelines mit klarer Trennung zwischen Beschaffung und Auswertung: Recherche anstoßen, Tools auswählen, Fehler sauber melden. Nicht geeignet für Compliance, Lizenzprüfung, Policy-Zusammenfassungen oder andere Pfade, in denen die Modellantwort selbst als verlässliche Verdichtung von Tool-Ergebnissen dienen muss. Wenn Sie es einsetzen, dann nur mit nachgelagerter Verifikation auf Satzebene oder mit einem zweiten Modell als Antwortprüfer.