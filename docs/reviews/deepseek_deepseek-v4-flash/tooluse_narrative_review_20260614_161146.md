**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:11:46


Bedingt deploy, weil die Tool-Nutzung verlässlich und protokollsauber ist, die Synthese aber nicht konstant präzise genug für hochkritische Ausgabepfade ausfällt. Das Gesamtbild ist mit validen Tool-Calls, keiner Halluzination und solidem Combined-Score produktionsfähig, aber nicht ohne Guardrails.

**Tool-Execution-Profil**

DeepSeek V4 Flash zeigt echte Werkzeugintelligenz statt bloßem Schema-Folgen. Beim Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung vollständig. Das spricht für brauchbare Situationsdiagnose in dynamischen MCP-Pipelines. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus eigenem Wissen plus anschließendes Fetch misst, bleibt es brauchbar, aber nicht deterministisch genug. P1 80 heißt hier: Es kann die Strecke oft korrekt schließen, ist aber nicht präzise genug für fragile URL-Schemata oder harte Automationspfade. Wichtig ist, dass die Tool-Calls valide waren und kein Retry nötig war. Das ist ein gutes Signal für Protokollkonformität und reduziert operativen Aufwand in der Orchestrierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht stark. P2 66.67 und die Ausschläge zwischen HTTP Fetch & Extract mit 80 und EU License Research mit 40 zeigen, dass das Modell gefundene Informationen meist brauchbar zusammenzieht, jedoch nicht konsistent sauber priorisiert, verifiziert und komprimiert. Für Nutzerantworten ist das akzeptabel. Für Compliance, Policy oder andere textkritische Endausgaben ist es zu schwankend.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Überwiegend ja, und das ist der wichtigere Befund. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das Vertrauenssignal ist damit besser als der niedrige P2-Wert vermuten lässt. Das Modell driftet also eher in schwächere Verdichtung als in erfundene Fakten.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Call misst, reagiert das Modell produktionsgerecht. Es halluziniert keinen Seiteninhalt trotz Fehler und kommuniziert den Ausfall nachvollziehbar. Genau dieses Verhalten braucht eine Tool-Pipeline: Fehler offenlegen, nicht kaschieren.

**Betriebsprofil**

Call 1: 3.37s. MCP-Latenz: 1.19s. Call 2: 6.24s. Total: 64.78s.  
Kosten pro Run: 0.000895.  
Direkte Einordnung: günstig, aber für einen Flash-Ableger im End-to-End-Lauf nicht schnell. Das Preisniveau ist klar produktionsfreundlich. Die Gesamtlaufzeit ist nur dann akzeptabel, wenn die Pipeline nicht interaktiv unter enger Latenzgrenze steht.

**Fazit & Empfehlung**

Geeignet für recherchegestützte MCP-Pipelines mit Tool-Zwang, Fehlertoleranz und nachgelagerter Validierung. Dazu zählen Web-Recherche, mehrstufige Informationsbeschaffung und mehrsprachige Voranalysen. Nicht die erste Wahl für Compliance-nahe Endausgaben, regulatorische Zusammenfassungen oder andere Pfade, in denen die Verdichtung selbst belastbar und nahezu revisionsfest sein muss. Wenn Sie ein günstiges Modell suchen, dem Sie Tools anvertrauen können, ist es ein brauchbarer Worker. Wenn Sie der finalen Formulierung ohne zweite Prüfung vertrauen müssen, reicht es nicht.