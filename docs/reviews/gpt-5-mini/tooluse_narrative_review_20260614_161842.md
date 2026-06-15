**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:18:42


Bedingt deploy, weil GPT-5 Mini zuverlässig gültige Tool-Calls produziert und nicht halluziniert, aber die Synthesetreue mit Combined 73.17 und P2 56.67 zu schwach für strikt evidenzgebundene Ausgabeschichten ist.

**Tool-Execution-Profil**

Die operative Seite ist stark. Das Modell wählt Werkzeuge meist korrekt, erzeugt valide MCP-konforme Aufrufe und brauchte keinen Retry. Besonders wichtig: Beim Web Search & Tool Selection-Test, der prüft, ob ohne Hinweis search statt fetch gewählt wird, traf es die Werkzeugentscheidung sauber. Das spricht gegen ein starres Abrufmuster und für echte Situationsanpassung.

Schwächer ist die Präzision in der zweiten Hälfte der Kette. Beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL aus Vorwissen prüft, war die Ausführung brauchbar, aber nicht deterministisch genug für fragile Fetch-Pipelines. Das Muster ist klar: gute Tool-Intelligenz bei der Auswahl, etwas weniger Verlässlichkeit bei selbst konstruierten Zugriffspfaden.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ausreichend. Die P2-Leistung bleibt klar hinter der Tool-Ausführung zurück. In HTTP Fetch & Extract und Tool Failure Handling (404) hält es den Inhalt noch ordentlich zusammen, aber EU License Research und Multilingual Search & Synthesis zeigen, dass die Verdichtung aktueller oder sprachübergreifender Befunde an Präzision verliert. Für Nutzer mit eigener Nachprüfung ist das tragbar. Für Outputs, die direkt in Tickets, Compliance-Notizen oder Kundenantworten laufen, ist es zu locker.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Fehler provoziert, blieb es formal im Web-Arbeitsmodus. Halluzination wurde nicht erkannt, Content-Verification-State A ist ein starkes Vertrauenssignal. Das Modell ist also eher ein komprimierender als ein erfindender Fehlerfall.

**Fehlerresilienz**

Beim 404-Test, der misst, ob nach einem fehlgeschlagenen Tool-Call transparenter Fehlerstatus statt erfundenem Seiteninhalt kommt, reagierte das Modell akzeptabel. Es halluzinierte keinen Ersatzinhalt. P2 60 zeigt aber, dass die Kommunikation des Fehlers nicht maximal klar oder handlungsleitend war. Für Produktion ist das dennoch brauchbar, weil die Vertrauenskette intakt bleibt.

**Betriebsprofil**

3.56s erster Call, 20.33s zweiter Call, 148.69s total. MCP-Latenz 0.89s. Im End-to-End-Lauf nicht schnell. Kosten pro Run 0.011345. Günstig für API-Betrieb, gemessen an der soliden Tool-Ausführung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klarer Tool-Governance, vor allem Recherche, Routing, Vorstrukturierung und fail-safe Tool-Orchestrierung. Nicht die erste Wahl für Pipelines, in denen die Modellantwort selbst als belastbare Endverdichtung gilt, etwa Compliance-Summaries, mehrsprachige Entscheidungsnotizen oder präzise Faktenextraktion ohne menschliche Kontrolle. Empfehlung: als ausführendes Tool-Modell einsetzen, aber die finale Synthese entweder stärker validieren oder an ein präziseres Ausgabemodell übergeben.