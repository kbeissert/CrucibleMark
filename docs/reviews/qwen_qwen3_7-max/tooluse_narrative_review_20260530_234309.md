**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:43:09


Nicht deploy. Der kombinierte Score von 0.00 ist schwach, und zugleich liegt kein valider Tool-Call-Nachweis vor. Für eine MCP-gestützte Tool-Pipeline fehlt damit die grundlegende Produktionsbasis.

**Tool-Execution-Profil**

Das Kernproblem ist nicht ein einzelner Fehltritt, sondern fehlende belastbare Ausführungssignale. P1 ist durchgängig n/a, und der Status „Tool-Call valide: false“ bedeutet, dass sich weder korrekte Werkzeugwahl noch Protokolltreue bestätigen lassen. Für produktive Tool-Infrastrukturen ist das ein Ausschlusskriterium.

Bei Web Search & Tool Selection, also dem Test, ob das Modell ohne Hinweis zwischen Suche und direktem Fetch unterscheidet, gibt es keine verwertbare Evidenz. Dasselbe gilt für URL Construction & Fetch, also die Ableitung einer Ziel-URL aus Weltwissen und den anschließenden Abruf. Man kann daher weder von Werkzeugintelligenz noch von einem stabilen festen Muster sprechen. Es ist schlicht nicht belegt, dass das Modell in einer offenen Tool-Umgebung verlässlich handelt.

Retry war nicht erforderlich. Das entlastet das Modell aber nicht. Ohne valide Calls bleibt offen, ob das Problem im Format, in der Tool-Auswahl oder im grundsätzlichen Ausführungsverständnis liegt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es keine belastbare Aussage. P2 ist in allen Assets n/a. Für einen Generalisten in der Frontier-Klasse ist das kritisch, weil gerade die Verdichtung fremder Tool-Ausgaben der eigentliche Wertbeitrag in einer MCP-Pipeline ist.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Honeypot-Ergebnis aus EU License Research ist vorsichtig positiv: Es wurde keine Halluzination erkannt, obwohl der Test genau prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden. Das ist ein Vertrauenssignal, aber nur ein negatives Risikosignal, kein positiver Leistungsnachweis.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf prüft, wurde keine Halluzination erkannt. Das ist produktionsseitig relevant. Ein Modell, das bei Fehlern keinen Seiteninhalt erfindet, schützt die Integrität der Pipeline. Dennoch ersetzt sauberes Fehlerverhalten keine fehlende Tool-Ausführungsfähigkeit.

**Fazit & Empfehlung**

qwen3.7-max ist derzeit nicht für produktive MCP-Pipelines zu empfehlen, in denen das Modell selbst Tools auswählen, Calls erzeugen und Ergebnisse verdichten muss. Vertretbar wäre allenfalls ein stark eingehegter Einsatz als textuelles Nachbearbeitungsmodell hinter einer extern kontrollierten Orchestrierung, die Tool-Wahl, Parameter und Ergebnisvalidierung vollständig übernimmt. Für agentische Recherche-, Fetch-, Compliance- oder Web-Workflows fehlt die notwendige Nachweisbarkeit.