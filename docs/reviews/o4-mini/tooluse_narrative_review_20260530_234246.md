**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:46


Bedingt deploy, weil o4-mini valide Tool-Calls erzeugt, aber mit erkannter Halluzination und nur moderater Gesamtsicherheit kein vertrauenswürdiger Default für faktensensitive MCP-Pipelines ist.

**Tool-Execution-Profil**

Auf der Ausführungsebene arbeitet das Modell solide. Der Tool-Call war valide, und die P1-Leistung von 85 zeigt, dass es MCP-konform agieren kann. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis statt fetch eine Suche nötig ist, wählt es das richtige Werkzeug sicher. Das spricht gegen bloßes Schema-Fahren und für echte Werkzeugwahl unter Kontext. Beim Test URL Construction & Fetch, der korrekte URL-Ableitung und anschließendes Fetch misst, bleibt es brauchbar, aber nicht deterministisch präzise. Das Muster ist klar: gute Auswahl des Werkzeugtyps, etwas weniger Verlässlichkeit bei der exakten Parametrisierung. Dass ein Retry nötig war, wirkt hier eher wie ein Robustheits- oder Formatproblem im Ablauf als ein grundsätzliches Verständnisproblem der Tool-Infrastruktur.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. Die P2-Leistung von 40.83 ist der Kernbefund dieses Runs. In HTTP Fetch & Extract verdichtet es extrahierte Fakten nur begrenzt präzise, und in Multilingual Search & Synthesis fällt die Überführung gefundener Inhalte in eine belastbare deutsche Antwort deutlich ab. Das Modell kann Daten holen, aber es hält die semantische Präzision beim Zusammenziehen nicht stabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, liegt P2 bei 15 bei erkanntem Halluzinationsbefund. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell in einer Tool-Pipeline erfundene oder vorab gelernte Fakten als Ergebnis einer Recherche ausgibt, untergräbt es die Vertrauenskette der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Aufrufen misst, reagiert o4-mini akzeptabel. Es halluziniert keinen Seiteninhalt nach dem Fehler. P2 60 ist nicht stark, aber produktionstauglich, weil die zentrale Anforderung erfüllt ist: Das Modell benennt den Ausfall statt Ersatzinhalt zu erfinden.

**Betriebsprofil**

Total 73.58s: langsam.  
Call 1 4.42s, Call 2 6.85s, MCP-Latenz 1.00s.  
Kosten pro Run 0.047125 USD: günstig bis moderat.  
Im Verhältnis zur Leistung ist die Laufzeit zu hoch für breit skalierte Echtzeit-Pipelines.

**Fazit & Empfehlung**

Geeignet für interne Assistenz- oder Analysepipelines, in denen Tool-Nutzung wichtig ist, Ergebnisse aber durch nachgelagerte Validatoren, Schema-Prüfung oder Human-in-the-loop abgesichert werden. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere faktensensitive Retrieval-Pipelines, in denen Tool-Ausgaben als belastbare Quelle gelten müssen. Wer o4-mini einsetzt, sollte es als ausführungsstarken, aber synthetisch unsicheren Tool-Operator behandeln, nicht als vertrauenswürdige letzte Instanz.