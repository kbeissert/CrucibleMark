**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:18:25


Bedingt deploy, weil die Tool-Ausführung verlässlich wirkt und keine Halluzination erkannt wurde, die Synthesetreue aber zu oft hinter der Tool-Qualität zurückbleibt.

**Tool-Execution-Profil**

GPT-5.4 Mini wählt Werkzeuge grundsätzlich sinnvoll und produziert valide Calls. Das wichtigste Signal ist hier die Differenz zwischen Web Search & Tool Selection und URL Construction & Fetch: Beim Test zur Werkzeugwahl erkennt es ohne expliziten Hinweis sauber, dass erst gesucht und nicht direkt gefetcht werden muss. Das spricht gegen starres Musterverhalten und für echte Tool-Intelligenz in offenen Pipelines. Schwächer wird es, wenn es die Ziel-URL selbst aus Vorwissen ableiten muss. Beim URL-Construction-Test ist die Ausführung noch brauchbar, aber nicht präzise genug für deterministische Pfade ohne Absicherung.

Dass ein Retry erforderlich war, wirkt hier eher wie ein Ablauf- oder Formatproblem im mehrschrittigen Tooling als wie ein Verständnisfehler. Dafür spricht, dass der Tool-Call am Ende valide war und die P1-Werte über fast alle Assets stabil hoch bleiben.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die Synthese ist bei klar strukturierten Fetch-Inhalten stark, wie HTTP Fetch & Extract zeigt, fällt aber bei Recherche- und Lizenzthemen deutlich ab. Das Modell kann Daten holen, verdichtet sie aber nicht konsistent in eine präzise, entscheidungsreife Antwort. Für produktive Pipelines heißt das: Gute Extraktion ist nicht automatisch gute Übergabe an den nächsten Entscheidungsschritt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht sauber genug. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, liegt die Vertrauenslage trotz fehlender Halluzinationsflagge nur auf schwachem Niveau. P2=20 bei Content-Verification-State B2 ist kein Totalausfall, aber ein Warnsignal: Das Modell bleibt nicht strikt genug an den verifizierten Quellen, wenn Aktualität und Compliance relevant sind.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Seiteninhalt misst, halluziniert GPT-5.4 Mini keinen Ersatzinhalt. P2=60 zeigt, dass die Kommunikation nicht ideal verdichtet ist, aber das Verhalten bleibt sicher: Fehler werden nicht in scheinbare Fakten umgewandelt.

**Betriebsprofil**

Total 42.81s pro Run. Modell-Calls 2.50s und 3.28s, MCP-Latenz 1.35s. Damit insgesamt eher langsam für die gelieferte Qualität. Kosten pro Run: $0.018911. Günstig bis moderat, aber nur dann attraktiv, wenn die Pipeline die schwächere Synthese durch Validierung oder Post-Processing auffängt.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klaren Tool-Grenzen, strukturierter Extraktion und nachgelagerter Validierung. Nicht geeignet als alleinige Instanz für Compliance-, Lizenz- oder andere aktualitätskritische Syntheseaufgaben, bei denen die Antwort strikt an Web-Belegen hängen muss. Deployen, wenn Sie Tool-Ausführung priorisieren und die Endverdichtung separat absichern.