**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:25:35


Bedingt deploy, weil Hermes 4 70B valide Tool-Calls erzeugt und keine Halluzination im Lauf zeigte, die Gesamtausbeute mit 68.29 aber nur tragfähig ist, wenn die Pipeline Retries und enge Ergebnisprüfung bereits vorsieht.

**Tool-Execution-Profil**

Das stärkste Signal ist P1 84.17. Das Modell kann also Tool-Aufrufe grundsätzlich ausführen und bleibt MCP-konform. Der valide Tool-Call zeigt, dass die Schnittstelle technisch beherrscht wird. Das ist die Mindestvoraussetzung für produktiven Tool-Einsatz, und sie ist hier erfüllt.

Schwächer ist die Aussage zur Werkzeugwahl selbst. Für Web Search & Tool Selection sowie URL Construction & Fetch liegen keine Asset-Einzelwerte vor. Deshalb lässt sich nicht belastbar sagen, ob Hermes 4 70B situationsbezogen zwischen Suche und direktem Fetch unterscheidet oder primär einem gelernten Muster folgt. Der notwendige Retry spricht eher für ein Format- oder Ablaufproblem als für ein grundsätzliches Verständnisversagen, weil der Call am Ende valide war. Für deterministische Pipelines bleibt das dennoch relevant: Ein Modell, das erst im zweiten Anlauf sauber spricht, erhöht Orchestrierungsaufwand und Fehlerfläche.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. P2 53.33 ist der klare Schwachpunkt dieses Laufs. Das Modell kann Informationen aus Tools offenbar nicht konsistent auf das Niveau komprimieren, das Architekten für belastbare Endantworten brauchen. Für reine Ausführung reicht das, für extraktive oder mehrquellige Zusammenführung nur mit nachgelagerter Validierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist positiv. Beim EU License Research, das prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist für Compliance-nahe und zeitkritische Recherchen wichtiger als der reine Qualitätswert.

**Fehlerresilienz**

Im Tool Failure Handling (404), das transparentes Verhalten bei fehlgeschlagenem Abruf prüft, hat das Modell keinen Seiteninhalt erfunden. Das ist produktionsfähig. Ein fehlgeschlagener Tool-Call bleibt damit als Fehler sichtbar und unterwandert nicht die Pipeline mit plausibel klingendem Ersatzinhalt. Genau dieses Verhalten braucht man in robusten Agentenketten.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv, aber nicht fleet-kompetitiv auf Spitzenniveau. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Für lokale Infrastruktur ist das akzeptabel, als Leistungsargument allein reicht es nicht.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen lokaler Betrieb, direkte Tool-Nutzung und transparente Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Gut passend für Recherche-Vorstufen, Routing, Tool-Ausführung und kontrollierte Agentenschritte mit Validator dahinter. Nicht die richtige Wahl für Pipelines, in denen das Modell aus mehreren Tool-Ergebnissen selbst die finale, belastbare Antwort formulieren soll. Dafür ist die Synthesetreue zu schwach und der Retry-Bedarf operativ zu teuer.