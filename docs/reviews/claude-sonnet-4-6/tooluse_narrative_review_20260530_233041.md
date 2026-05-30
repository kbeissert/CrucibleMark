**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:41


Bedingt deploy, weil Claude Sonnet 4.6 valide Tool-Calls erzeugt und im Ablauf stabil bleibt, aber mit erkannter Halluzination im Honeypot das Grundvertrauen in toolgestützte Antworten verletzt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist operativ solide. Mit P1 83.33 produziert das Modell gültige MCP-konforme Aufrufe, und es brauchte keinen Retry. Das spricht gegen ein Protokoll- oder Formatproblem. Besonders stark ist Web Search & Tool Selection: Im Test, der prüft, ob ohne Hinweis web_search statt fetch nötig ist, wählt es das richtige Werkzeug sicher und erreicht P1 100. Das zeigt echte Werkzeugwahl statt stumpfer Standardroutine. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und anschließenden Fetch misst, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines; P1 80 ist dafür ein passender Wert. Insgesamt kann man ihm Tool-Infrastruktur übergeben, solange die nachgelagerte Validierung streng bleibt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. HTTP Fetch & Extract ist mit P2 100 sehr stark, ebenso URL Construction & Fetch und Tool Failure Handling (404) mit jeweils P2 80. Sobald mehrere Quellen, Suchschritte oder Sprachgrenzen zusammenkommen, fällt die Verdichtungsqualität deutlich ab. EU License Research liegt bei P2 15, Multilingual Search & Synthesis ebenfalls bei 15, Web Search & Tool Selection bei 35. Das Modell extrahiert also gut aus klaren Einzelquellen, schwächelt aber bei verdichtender Synthese unter Unsicherheit.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde eine Halluzination erkannt. Content-Verification-State B1 und P2 15 sind hier kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder nicht belegte Aussagen als Ergebnis einer Tool-Recherche ausgibt, unterminiert es die Vertrauenskette der gesamten Pipeline.

**Fehlerresilienz**

Im 404-Test reagiert das Modell produktionstauglich. Der Test misst, ob es bei fehlgeschlagenem Tool-Call transparent bleibt oder Seiteninhalt erfindet. Mit P2 80 und ohne Halluzination trotz 404 kommuniziert es den Fehler sauber. Das ist für robuste Pipelines akzeptabel.

**Betriebsprofil**

Total 339.33s. Einzelschritte 38.46s und 16.51s bei 1.58s MCP-Latenz. Langsam für einen Generalisten. Kosten pro Run: $0.296922. Für die gezeigte Leistung nicht günstig.

**Fazit & Empfehlung**

Geeignet für interne Recherche- und Extraktionspipelines mit klaren Einzelquellen, guter Beobachtbarkeit und verpflichtender Quellenprüfung vor Ausgabe. Nicht geeignet für Compliance, Lizenzprüfung, mehrsprachige Recherche-Synthese oder andere Pipelines, in denen aktuelle Web-Fakten unverändert und belegbar aus Tools übernommen werden müssen. Wer Claude Sonnet 4.6 einsetzt, sollte es als gut steuerbaren Tool-Operator behandeln, nicht als vertrauenswürdige letzte Instanz für faktenkritische Synthese.