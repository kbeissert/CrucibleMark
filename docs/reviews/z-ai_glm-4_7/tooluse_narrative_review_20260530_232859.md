**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:28:59


Bedingt deploy, weil GLM-4.7 valide Tool-Calls erzeugt und die Tool-Ausführung stabil wirkt, aber die Synthesetreue mit Combined 62.75 und aktiv erkanntem Halluzinationssignal für vertrauenskritische Pipelines nicht ausreicht.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare stärkere Seite dieses Modells. P1 bei 83.33, valide Calls und kein Retry-Bedarf sprechen dafür, dass es MCP-konform arbeitet und keine offensichtlichen Formatprobleme erzeugt. Beim Web-Search-and-Tool-Selection-Test, der prüft ob das Modell ohne Hinweis erkennt, dass eine Suche statt eines direkten Fetch nötig ist, erreicht es P1=100. Das zeigt echte Werkzeugwahl statt bloßem Reflex auf einen Standard-Call. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließenden Fetch misst, liegt es mit P1=80 solide, aber nicht präzise genug für strikt deterministische Abläufe. Das Muster ist damit klar: GLM-4.7 versteht, welches Werkzeug gebraucht wird, ist aber bei der letzten Meile der Ausführung nicht immer exakt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. P2 liegt bei 42.50 und die Schwäche zieht sich durch mehrere Assets: EU License Research bei 20, HTTP Fetch & Extract bei 35, Multilingual Search & Synthesis bei 20. Das Modell holt Informationen also oft korrekt über Tools, verdichtet sie danach aber zu grob, zu unvollständig oder mit unsauberer Priorisierung. Für produktive Pipelines ist das kritisch, weil der Fehler nicht im Zugriff, sondern in der Übergabe an den Nutzer oder den nächsten Systemschritt entsteht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diese Trennung prüft, liegt der Content-Verification-State bei B1 und P2 bei 20, aber ohne formale Halluzination in diesem Einzelfall. Gleichzeitig ist global Halluzination erkannt=true. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgibt, verliert die gesamte Infrastruktur ihre Beweiskraft.

**Fehlerresilienz**

Akzeptabel. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf prüft, halluziniert GLM-4.7 keinen Ersatzinhalt. P2=60 zeigt keine ideale, aber brauchbare Fehlerkommunikation. Für Produktion ist das der richtige Fehlermodus: sichtbar scheitern statt Inhalte zu erfinden.

**Betriebsprofil**

Call 1: 12.90s. Call 2: 21.16s. MCP-Latenz: 1.44s. Total: 212.95s.  
Langsam für die gelieferte Qualität.  
Kosten pro Run: 0.004277 USD. Günstig.

**Fazit & Empfehlung**

Geeignet für tool-zentrierte Pipelines mit nachgelagerter Validierung, etwa Recherche-Vorstufen, Tool-Routing und nichtkritische Operator-Assistenz. Nicht geeignet für Compliance, Lizenzprüfung, mehrsprachige Wissensverdichtung oder jede Pipeline, in der die sprachliche Synthese als verlässliches Endprodukt gilt. Wenn Sie GLM-4.7 einsetzen, dann als ausführendes Tool-Modell unter enger Guardrail- und Verifikationsschicht, nicht als letzte Instanz für faktengebundene Antworten.