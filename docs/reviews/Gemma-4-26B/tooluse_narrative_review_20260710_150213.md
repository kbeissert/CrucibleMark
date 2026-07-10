**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:02:13


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue für produktionsnahe Wissens- und Compliance-Pipelines nicht stabil genug wirkt. Der Combined-Score ist gut, doch der invalide Tool-Call verhindert ein uneingeschränktes Freigabesignal.

**Tool-Execution-Profil**

Gemma 4 26B-A4B Instruct zeigt echte Werkzeugwahl-Kompetenz, nicht nur starres Ablaufmuster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search sehr zuverlässig. Das spricht für brauchbare Planungslogik in dynamischen MCP-Pipelines. Beim Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden fetch misst, arbeitet es brauchbar, aber weniger deterministisch. Genau dort sieht man die Grenze: gute Werkzeugintelligenz, aber keine durchgehend präzise Call-Erzeugung. Dass der Tool-Call insgesamt als nicht valide markiert wurde, ist für produktive Orchestrierung relevant. Es ist kein Retry nötig gewesen, also eher kein bloßes Formatproblem unter Last, sondern ein punktuelles Zuverlässigkeitsdefizit in der Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung bleibt mit 56.67 klar hinter der Tool-Ausführung zurück. Über die sechs Aufgaben hinweg extrahiert es Informationen meist korrekt genug, verdichtet sie aber oft zu grob. Besonders bei EU License Research, also dem Test auf aktuelle Lizenzrestriktionen aus Web-Quellen, fällt die Verdichtung deutlich ab. Für reine Retrieval- und Weiterleitungsaufgaben ist das noch tragbar. Für Entscheider-Outputs, die präzise Einschränkungen, Versionen oder Ausnahmen sauber zusammenfassen müssen, ist es zu unscharf.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist besser als die P2-Note vermuten lässt. Im Honeypot EU License Research halluziniert es nicht und erfindet keine aktuellen Web-Befunde aus dem Training. Das ist wichtig. Das Modell wirkt also eher komprimierend und ungenau als frei erfindend. Für Produktionsvertrauen ist das deutlich besser als ein kreatives Modell mit höherem Halluzinationsrisiko.

**Fehlerresilienz**

Bei Tool-Fehlern bleibt das Modell akzeptabel. Im 404-Test, der transparenten Umgang mit fehlgeschlagenen Abrufen statt erfundenem Ersatzinhalt misst, halluziniert es keinen Seiteninhalt. Die Fehlerkommunikation ist damit produktionsfähig. P2 60 zeigt aber auch hier, dass die Einordnung des Fehlers nicht immer maximal präzise oder handlungsleitend ausfällt.

**Betriebsprofil**

Call 1: 2.16s. MCP-Latenz: 1.05s. Call 2: 8.45s. Total: 69.95s.  
Lokal. Keine Laufkosten pro Run.  
Für die gebotene Leistung günstig, aber insgesamt langsam.

**Fazit & Empfehlung**

Geeignet für lokal betriebene MCP-Pipelines, in denen Tool-Wahl, Web-Recherche und robuste Fehleroffenlegung wichtiger sind als hochwertige Endverdichtung. Gut passend für Operator-Assists, Recherche-Vorstufen, mehrstufige Agenten mit nachgelagerter Verifikation und souveräne Deployments mit Apache-2.0-Anforderungen. Nicht die erste Wahl für Compliance-Ausgaben, Executive Summaries oder Systeme, in denen der Modelltext selbst als belastbares Endartefakt dient. Wer es einsetzt, sollte Tool-Calls strikt validieren und die finale Synthese durch Regeln, Reranking oder ein stärkeres Prüfmodell absichern.