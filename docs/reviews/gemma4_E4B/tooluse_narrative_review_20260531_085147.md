**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:51:47


Bedingt deploy, weil Gemma 4 E4B valide Tool-Calls produziert, keine Halluzination im Benchmark zeigt und damit die Infrastruktur nicht unterläuft, aber die Synthesequalität für tool-zentrierte Produktionspfade nur begrenzt belastbar ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Mit P1 90 wählt es Werkzeuge meist korrekt und bleibt MCP-konform. Beim Web-Search-&-Tool-Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung durchgängig. Das spricht gegen bloßes Musterfolgen und für brauchbare Werkzeugwahl in offenen Situationen. Beim URL-Construction-Test, der die präzise Ableitung einer Ziel-URL und den anschließenden Fetch misst, ist es dagegen nur solide. Die Aufrufe bleiben valide, aber die URL-Herleitung ist nicht deterministisch genug für fragile Pipelines mit harten Pfadannahmen. Positiv ist, dass kein Retry nötig war. Das Problem liegt also nicht im Protokollformat, sondern eher in der inhaltlichen Präzision vor dem Call.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher funktional als stark. P2 60 heißt: Das Modell kann Ergebnisse zusammenziehen, verliert dabei aber Schärfe und Priorisierung. Das zeigt sich über mehrere Assets hinweg, besonders bei Multilingual Search & Synthesis, wo die grenzüberschreitende Recherche gelingt, die deutsche Verdichtung aber zu grob bleibt. Für kurze Operator-Antworten reicht das. Für Compliance, Policy-Zusammenfassungen oder extraktionsnahe Berichte ist es zu ungenau.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gut. Beim EU-License-Research-Honeypot, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb es im beschafften Material. Content-Verification-State A und keine erkannte Halluzination sind für produktive Tool-Pipelines das wichtigere Signal als die nur mittlere Verdichtungsqualität.

**Fehlerresilienz**

Akzeptabel für Produktion. Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call statt erfundenem Seiteninhalt prüft, kommuniziert das Modell den Fehler sauber und halluziniert keinen Ersatzinhalt. P2 80 ist hier ein gutes Betriebszeichen. Ein System kann mit klaren Fehlern umgehen. Mit erfundenen Erfolgen nicht.

**Souveränitätsprofil**

Lokal betreibbar und zugleich fleet-kompetent. Das Modell liegt mit einem Sovereignty Gap von -4.01 Punkten nur 4.01 Punkte unter dem Fleet-Ø von 66.21. Für eine lokale sovereign Deployment-Strategie ist das ein tragfähiges Profil.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen sichere Tool-Nutzung wichtiger ist als hochwertige Endverdichtung: Recherche-Vorstufen, Routing, kontrollierte Fetch-und-Search-Workflows, interne Assistenten mit menschlicher Nachsicht. Nicht die erste Wahl für Pipelines, die aus Tool-Output direkt präzise, mehrsprachige oder entscheidungsreife Synthesen erzeugen sollen. Wenn Sie Gemma 4 E4B einsetzen, dann als verlässlichen Tool-Operator mit nachgelagerter Validierung oder mit einem stärkeren Modell für die Schlussredaktion.