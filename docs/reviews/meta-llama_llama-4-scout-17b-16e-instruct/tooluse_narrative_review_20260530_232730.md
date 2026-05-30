**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:30


Nicht deploy für MCP-gestützte Tool-Pipelines, weil der kombinierte Befund schwach ist, der Tool-Call nicht valide war und ein Retry nötig wurde.

**Tool-Execution-Profil**

Llama 4 Scout 17B zeigt kein belastbares Tool-Verhalten. P1 liegt durchgängig bei 35, auch dort, wo das Modell ohne expliziten Hinweis erkennen muss, ob Websuche oder direkter Fetch nötig ist. Das spricht nicht für saubere Werkzeugwahl, sondern eher für ein starres Antwortmuster mit unzuverlässiger Protokollausführung. Beim Test Web Search & Tool Selection, der genau diese Entscheidung unter Unsicherheit prüft, entsteht kein Hinweis auf echte Tool-Intelligenz. Beim URL-Construction-Test, der die Ableitung der Ziel-URL und den anschließenden Fetch misst, bleibt das Bild identisch: nicht katastrophal, aber zu unpräzise für deterministische Pipelines. Dass ein Retry erforderlich war, wirkt hier eher wie ein Format- oder MCP-Konformitätsproblem als wie reines Wissensversagen. Für den Betrieb zählt das trotzdem als Ausfallursache.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Außerhalb des Honeypots liefert es mehrfach P2=40 und kann gefundene Inhalte grundsätzlich knapp zusammenführen. Der Gesamteindruck bleibt aber fragil, weil die Verdichtung nicht konsistent genug ist, um Produktionsantworten verlässlich an Tool-Output zu binden.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Genau hier fällt das Modell durch. Beim Test EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Webquellen statt aus dem Trainingswissen beantwortet werden, erreicht es P2=0. Es halluziniert dabei nicht offen, aber der Vertrauensbefund ist dennoch negativ: Das Modell hält sich nicht belastbar an den verifizierten Recherchepfad. Für Compliance-, Policy- oder Regulatorik-Pipelines ist das ein Ausschlusskriterium.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel. Im Test Tool Failure Handling (404), der prüft, ob nach einem fehlgeschlagenen Abruf transparent kommuniziert wird statt Seiteninhalt zu erfinden, bleibt es sauber und halluziniert keinen Ersatzinhalt. Das ist der stärkste produktionsrelevante Teil des Profils. Es schützt die Pipeline im Fehlerfall, kompensiert aber nicht die schwache Tool-Ausführung im Normalfall.

**Souveränitätsprofil**

Lokal betreibbar in der Gruppe local_sovereign, aber nicht fleet-kompetitiv. Der Befund liegt 5.32 Punkte unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet höchstens für lokale, kostenkritische Assistenten mit menschlicher Aufsicht, bei denen Tool-Aufrufe optional sind und Fehler sichtbar abgefangen werden. Nicht geeignet für MCP-Pipelines mit automatischer Tool-Orchestrierung, Compliance-Recherche, URL-Ableitung ohne Guardrails oder jede Kette, in der Tool-Output strikt befolgt werden muss. Wenn Sie dieses Modell einsetzen, dann nur hinter einem harten Tool-Validator und mit erzwungener Post-Execution-Prüfung.