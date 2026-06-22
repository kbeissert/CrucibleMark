**Deployment-Urteil**

> **Erstellt am:** 22.06.2026, 21:36:04


Bedingt deploy, weil das Modell keine Halluzination gezeigt hat, aber mindestens ein Tool-Call nicht valide war und die Gesamtleistung damit unter Produktionsniveau für strikt deterministische Tool-Pipelines bleibt.

**Tool-Execution-Profil**

Gemini 3.1 Pro Preview zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Test Web Search & Tool Selection erkennt es ohne expliziten Hinweis, dass eine Suche statt eines direkten Fetchs nötig ist, und trifft diese Entscheidung sauber. Das ist ein starkes Signal für orchestrierte MCP-Umgebungen mit wechselnden Informationsquellen. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar und führt den Fetch meist korrekt aus, aber nicht präzise genug für vollständig deterministische Pipelines. Der zentrale operative Makel bleibt die ungültige Tool-Ausführung im Lauf. Das spricht weniger für ein Verständnisproblem als für eine verbleibende Protokoll- oder Formatfragilität, die man in produktiven Flows nicht ignorieren darf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung zeigt, dass das Modell Ergebnisse meist sinnvoll zusammenführt, aber nicht mit der Präzision, die man für belastbare Extraktion, Compliance-Zusammenfassungen oder auditierbare Entscheidungsgrundlagen braucht. Besonders bei EU License Research, HTTP Fetch & Extract und URL Construction & Fetch bleibt die Verdichtung zu grob.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser als die reine Textqualität. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, hat das Modell nicht halluziniert. Das ist für produktive Recherche- und Compliance-Pipelines wichtiger als stilistische Stärke.

**Fehlerresilienz**

Beim 404-Test, der die Reaktion auf einen scheiternden Tool-Aufruf misst, erfindet Gemini 3.1 Pro Preview keinen Seiteninhalt. Das ist der richtige Produktionsreflex. Die Antwort bleibt jedoch nur mäßig hilfreich, weil die Fehlerkommunikation nicht stark genug in einen klaren nächsten Schritt oder eine saubere Begrenzung der Aussage überführt wird. Akzeptabel, aber nicht robust.

**Betriebsprofil**

Total: 99.08s. Call 1: 4.14s. Call 2: 11.58s. MCP-Latenz: 0.79s. Für die gezeigte Leistung langsam. Preis: $2.0/1M Input, $12.0/1M Output. Für Preview-Frontier nicht billig.

**Fazit & Empfehlung**

Geeignet für agentische Recherche-Pipelines mit menschlicher Nachkontrolle, für mehrsprachige Web-Aufgaben und für Orchestrierung, bei der die Tool-Wahl wichtiger ist als punktgenaue Extraktion. Nicht geeignet für streng automatisierte MCP-Pipelines, die valide Tool-Calls, präzise URL-Bildung und verlässliche Verdichtung ohne Nacharbeit verlangen. Wer es einsetzt, sollte Tool-Call-Validation, Antwortschema-Prüfung und enge Guardrails vor die produktive Freigabe setzen.