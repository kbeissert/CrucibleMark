**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:47:24


Bedingt deploy, weil GPT-5 Mini valide Tool-Calls erzeugt, nicht halluziniert und mit 73.17 insgesamt produktionsfähig wirkt, aber die Synthesequalität für verlässliche Endantworten zu ungleich bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke. Mit P1 90 produziert das Modell protokollkonforme Aufrufe, der Tool-Call war valide und ein Retry war nicht nötig. Das spricht für stabile MCP-Integration ohne offensichtliche Formatbrüche.

Bei der Werkzeugwahl zeigt es echte Situationsanpassung statt bloßem Standardmuster. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erreicht es P1 100. Es erkennt also, wann erst Suchraum geöffnet werden muss. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließendes Fetch prüft, landet es bei P1 80. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen exakt die richtige Zieladresse erwarten. Kurz: gute Tool-Intelligenz, schwächer bei präziser Adresskonstruktion.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur solide. P2 56.67 ist der eigentliche Bremsfaktor dieses Runs. Besonders sichtbar wird das bei EU License Research und Multilingual Search & Synthesis mit jeweils P2 40. Das Modell holt Informationen aus Tools, komprimiert sie dann aber zu grob. Für Entscheidungsunterlagen, Compliance-Memos oder mehrsprachige Rechercheausgaben reicht diese Verdichtung ohne Nachkontrolle nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist gut. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen tatsächlich aus Web-Quellen statt aus dem Modellgedächtnis kommen, wurde keine Halluzination erkannt. Content-Verification-State A und ein valider Abruf sprechen dafür, dass das Modell die Infrastruktur respektiert, auch wenn es die Resultate anschließend nicht stark genug aufbereitet.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Call misst, hat GPT-5 Mini keinen Seiteninhalt erfunden. P2 60 zeigt keine perfekte Fehlermoderation, aber der wichtige Punkt ist erfüllt: Es kommuniziert den Fehlschlag, statt Ersatzfakten zu produzieren.

**Betriebsprofil**

Call 1 3.56s. MCP-Latenz 0.89s. Call 2 20.33s. Total 148.69s. Für die gezeigte Leistung langsam. Kosten pro Run 0.011345. Preislich günstig bis moderat.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Auswahl, Abrufdisziplin und sichere Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung: Retrieval, Web-gestützte Assistenten, Vorstufen für nachgelagerte Reviewer. Nicht die richtige Wahl für Pipelines, die aus einem einzelnen Modelllauf präzise, belastbare Synthesen erzeugen müssen, etwa Compliance-Zusammenfassungen, Management-Briefings oder mehrsprachige Research-Digests ohne menschliche Kontrolle.