**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:19:23


Bedingt deploy, weil die Tool-Ausführung meist stark ist, aber die Synthesetreue zu schwach und ein invalider Tool-Call in einer MCP-Pipeline ein echtes Vertrauensproblem erzeugt.

**Tool-Execution-Profil**

Qwen 3.6 27B zeigt klare Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es den Bedarf für web_search zuverlässig. Das spricht für brauchbare Planungslogik in offenen Recherchepfaden. Beim URL-Construction-Test, der prüft, ob das Modell die Ziel-URL selbst ableiten und dann fetch korrekt ausführen kann, bleibt es brauchbar, aber nicht deterministisch genug. P1 ist dort nur solide, nicht robust.

Der Kernvorbehalt ist protokollarisch: Tool-Call valide ist false. Das heißt nicht, dass das Modell Tools grundsätzlich nicht versteht. Es heißt aber, dass man den MCP-Layer nicht ohne Guardrails übergeben sollte. Für produktive Tool-Ketten braucht es Call-Validation, Schema-Prüfung und im Zweifel einen Broker, der fehlerhafte Aufrufe abfängt, bevor Seiteneffekte entstehen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert zeigt, dass Qwen 3.6 27B gefundene Inhalte oft nicht präzise genug zusammenzieht. Das sieht man besonders bei EU License Research, wo die Tool-Nutzung formal gelingt, die Verdichtung aber auf 20 fällt, und bei HTTP Fetch & Extract, das strukturierte Fakten aus echtem Seiteninhalt ziehen soll und nur auf 35 kommt. Für Compliance, Regulatorik und jede Pipeline mit exakten Detailfeldern ist das zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Honeypot-Ergebnis ist widersprüchlich: keine Halluzination im Einzelfall markiert, aber global Halluzination erkannt true. Genau das ist das Sicherheitsrisiko. Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als aus Tools stammend ausgeben kann, ist nicht nur die Antwortqualität betroffen, sondern die Beweiskraft der gesamten Infrastruktur.

**Fehlerresilienz**

Hier ist das Modell brauchbar. Beim 404-Test, der prüft, ob ein gescheiterter Tool-Aufruf transparent kommuniziert wird statt Seiteninhalt zu erfinden, bleibt Qwen 3.6 27B sauber. Es ersetzt den Fehler nicht durch Fantasieinhalt. Das ist für Produktion akzeptabel und deutlich wichtiger als stilistische Antwortqualität.

**Betriebsprofil**

Call 1: 8.91s. MCP-Latenz: 1.23s. Call 2: 85.90s. Total: 576.21s.  
Lokal betreibbar. Direkte Laufkosten pro Run: local.  
Für die gezeigte Leistung ist das langsam.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Orchestrierungs-Pipelines mit strikter Tool-Call-Validierung, Response-Checking und nachgelagerter Faktenprüfung. Nicht geeignet für Compliance-nahe, zitierpflichtige oder extraktionskritische Workflows, in denen Tool-Ergebnisse präzise verdichtet und belastbar weitergereicht werden müssen. Als Agent, der das richtige Werkzeug oft findet und Fehler transparent meldet, ist es brauchbar. Als vertrauenswürdige letzte Syntheseschicht ist es noch nicht stabil genug.