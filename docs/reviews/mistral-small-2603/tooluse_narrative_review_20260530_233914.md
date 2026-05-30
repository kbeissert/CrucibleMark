**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:14


Nicht deploy für MCP-gestützte Tool-Pipelines, weil das Modell bei schwachem Gesamtergebnis von 47.71 die Tool-Aufrufe nicht valide im geforderten Protokoll erzeugt und damit die Infrastruktur schon an der Schnittstelle bricht.

**Tool-Execution-Profil**

Mistral Small 4 zeigt hier kein belastbares Produktionsverhalten. Der Kernbefund ist nicht Halluzination, sondern Protokollbruch: Das Modell erzeugt das Mistral-eigene Tool-Call-Format statt MCP-kompatiblem JSON. Genau deshalb steht `tool_call_valid=false`, und genau deshalb war ein Retry nötig. Das wirkt wie ein Formatproblem, nicht wie ein reines Verständnisproblem. Für den Betrieb ist das aber kein mildernder Umstand, weil der Effekt derselbe bleibt: Die Pipeline kann Calls nicht sicher parsen.

Bei der Werkzeugwahl selbst lässt sich nur eingeschränkt Positives ableiten, weil mehrere Assets durch Parse-Fehler unbrauchbar werden. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, liegt kein verwertbarer P1-Befund vor. Dasselbe gilt für URL Construction & Fetch, also den Test, ob das Modell aus eigenem Wissen eine Ziel-URL korrekt bildet und dann sauber abruft. Damit fehlt der Nachweis, dass das Modell in dynamischen Tool-Ketten die richtige Aktion deterministisch auswählt. Für Architekten ist das ein Stoppsignal.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Der P2-Wert von 36.67 spricht gegen verlässliche Verdichtung, selbst dort, wo Tool-Nutzung grundsätzlich gelingt. Das ist zu wenig für Pipelines, die aus Rohquellen präzise Extrakte, Statuszusammenfassungen oder Compliance-taugliche Kurzbefunde erwarten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist der Befund besser. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das schützt das Vertrauensmodell teilweise. Es beweist aber nicht, dass die Inhalte gut verdichtet oder formal sauber eingebunden werden.

**Fehlerresilienz**

Akzeptabel. Beim Test Tool Failure Handling (404), der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt misst, halluziniert das Modell nicht. Das ist für Produktion wichtig: Wenn ein Abruf scheitert, erfindet es offenbar keinen Ersatzinhalt. Diese Transparenz kompensiert jedoch nicht die mangelhafte MCP-Konformität.

**Souveränitätsprofil**

Lokal betreibbar, open weights, damit organisatorisch attraktiv. Leistungseitig bleibt es aber 5.32 Punkte unter dem Fleet-Ø von 66.76. Der Souveränitätsvorteil ist real, die Fleet-Kompetenz im Tool-Betrieb derzeit nicht.

**Fazit & Empfehlung**

Geeignet ist Mistral Small 4 für lokale, souveräne Text- oder Assistenz-Pipelines ohne strikte MCP-Anbindung, etwa interne Q&A-, Drafting- oder Klassifikationsaufgaben mit begrenzter Tool-Orchestrierung. Nicht geeignet ist es für produktive MCP-Pipelines, in denen ein Modell selbstständig Tools wählen, korrekt aufrufen und Ergebnisse präzise verdichten muss. Ein Einsatz wäre nur bedingt vertretbar, wenn Sie einen robusten Adapter vor das Modell setzen, der das proprietäre Tool-Call-Format verlustfrei in MCP übersetzt und die Ausgabe zusätzlich validiert. Ohne diese Zwischenschicht sollte es nicht in die Tool-Infrastruktur.