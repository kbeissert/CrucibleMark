**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:11:37


Bedingt deploy, weil DeepSeek V4 Pro valide Tool-Calls erzeugt, keine Halluzination im Lauf gezeigt hat und mit Combined 76.00 klar produktionsfähig wirkt, aber die Synthesequalität für verifikationskritische Pipelines zu ungleich bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist stark. Das Modell arbeitet MCP-konform, der Tool-Call war valide und es brauchte keinen Retry. Entscheidend ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis prüft, ob für aktuelle Informationen zuerst gesucht statt direkt gefetcht werden muss, trifft es die richtige Entscheidung sicher. Das spricht gegen bloßes Schema-Folgen und für brauchbare Tool-Intelligenz in dynamischen Abläufen.

Weniger sauber ist die Präzision beim URL-Construction-Test, der prüft, ob das Modell die Ziel-URL aus eigenem Wissen ableiten und dann korrekt abrufen kann. P1 80 ist gut, aber nicht stark genug für strikt deterministische Pipelines mit hartem URL-Schema. Für Such-, Recherche- und Routing-Schritte ist das Modell belastbar. Für direkte, stillschweigende URL-Ableitung ohne Validierung sollte die Pipeline Schutzgeländer setzen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht durchgehend präzise genug. P2 63.33 zeigt, dass das Modell Ergebnisse meist brauchbar zusammenführt, jedoch mit merklichem Verlust an Schärfe. Das sieht man besonders bei EU License Research mit P2 40 und bei mehreren Such-Assets mit nur mittlerer Verdichtung. Für Analysten-Workflows ist das akzeptabel. Für Compliance-, Legal- oder Policy-Summaries ist Nachkontrolle nötig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diese Versuchung prüft, bleibt das Modell formal auf der sicheren Seite: Content-Verification-State A, keine erkannte Halluzination. Das Vertrauenssignal ist deshalb besser als der P2-Wert vermuten lässt. Das Problem ist hier nicht Erfindung, sondern ungenaue Verdichtung aktueller Quellen.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der prüft, ob ein fehlgeschlagener Tool-Call offen benannt oder mit erfundenem Inhalt überdeckt wird, kommuniziert das Modell transparent. Es halluziniert trotz Fehler keinen Seiteninhalt. Genau dieses Verhalten hält eine Tool-Pipeline vertrauenswürdig, auch wenn der Antwortfluss unterbrochen wird.

**Betriebsprofil**

Call 1 4.20s. MCP-Latenz 0.80s. Call 2 16.99s. Total 131.93s. Damit klar langsam. Kosten pro Run 0.003245. Damit günstig bis sehr günstig für ein Frontier-Reasoning-Modell. Preis passt, Laufzeit ist der eigentliche Trade-off.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Analyse- und mehrstufige Reasoning-Pipelines, in denen korrektes Tooling wichtiger ist als knappe Antwortzeit. Nicht die erste Wahl für hochfrequente User-Interaktion, streng deterministische Fetch-Flows oder jede Pipeline, in der die Endsynthese selbst als belastbarer Nachweis gelten muss. Wer es einsetzt, sollte Tool-Use direkt vertrauen, die finale Verdichtung aber bei sensiblen Domänen durch Zitatbindung, Feldextraktion oder einen zweiten Verifikationsschritt absichern.