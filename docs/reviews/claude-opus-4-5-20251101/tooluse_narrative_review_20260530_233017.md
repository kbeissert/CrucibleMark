**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:30:17


Bedingt deploy, weil Claude Opus 4.5 valide Tool-Calls produziert und im Ablauf zuverlässig bleibt, aber die Synthesetreue mit Combined 72.79 und erkannten Halluzinationssignalen nicht durchgehend produktionsfest ist.

**Tool-Execution-Profil**

Auf der Ausführungsebene ist das Modell klar brauchbar. Tool-Call valide: true und Retry erforderlich: false sprechen dafür, dass es MCP-konform arbeitet und keine nachträgliche Reparatur durch die Orchestrierung braucht. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die richtige Wahl zwischen web_search und fetch verlangt, erreicht es P1=100. Das zeigt echte Werkzeugwahl statt starrem Schema-Following. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann fetch korrekt ausführen lässt, bleibt es mit P1=80 solide, aber nicht deterministisch genug für Pfade, in denen URL-Präzision geschäftskritisch ist. Insgesamt wirkt das Modell wie ein intelligenter Orchestrator mit guter Tool-Heuristik, nicht wie ein reiner Call-Emitter.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. P2=59.17 ist für ein Frontier-Agentenmodell der eigentliche Warnwert. Die Extraktion aus vorhandenem Material funktioniert in klaren Fällen wie HTTP Fetch & Extract und URL Construction & Fetch mit P2=80 gut. Sobald mehrere Quellen, Sprachwechsel oder offene Recherche ins Spiel kommen, fällt die Verdichtung sichtbar ab: Web Search & Tool Selection P2=35, Multilingual Search & Synthesis P2=40, EU License Research P2=40. Das Risiko liegt nicht in fehlender Tool-Nutzung, sondern in der letzten Meile der Ergebniszusammenführung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nicht stabil genug für Hochvertrauens-Pipelines. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, liegt der Content-Verification-State nur bei B1 und P2 bei 40. Halluzination wurde dort nicht explizit erkannt, aber der globale Halluzinationsbefund macht das zu einem Sicherheitsrisiko. Wenn ein Modell in einer Tool-Pipeline Inhalte formuliert, die wie Tool-Ergebnisse klingen, aber nicht sauber daran gebunden sind, verliert die gesamte Infrastruktur ihre Prüfbarkeit.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparente Kommunikation bei fehlschlagendem Tool-Call verlangt, erreicht das Modell P2=80 und halluziniert keinen Seiteninhalt. Es meldet den Fehler also ausreichend klar, statt Ersatzfakten zu erfinden. Das ist für robuste Pipelines deutlich wichtiger als elegante Formulierungen.

**Betriebsprofil**

Total 71.45s pro Run. Call 1: 2.08s, MCP-Latenz: 1.04s, Call 2: 8.79s. Langsam. Kosten/Run: $0.1119. Teuer. Für diese Leistung nur dann vertretbar, wenn Tool-Planung wichtiger ist als knappe, streng verifizierte Synthese.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit starker externer Validierung, klaren Tool-Grenzen und nachgelagerter Ergebnisprüfung, etwa Recherche-Orchestrierung, Multi-Step-Planung und fehlertolerante Analysten-Workflows. Nicht geeignet für Compliance-, Policy-, Lizenz- oder andere Hochvertrauens-Pipelines, in denen die textliche Synthese selbst als belastbares Endprodukt gilt. Wenn Sie Claude Opus 4.5 einsetzen, dann als Planer und Tool-Nutzer mit striktem Guardrail um die abschließende Verdichtung.