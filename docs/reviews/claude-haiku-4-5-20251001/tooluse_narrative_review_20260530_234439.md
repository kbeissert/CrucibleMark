**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:44:39


Bedingt deploy, weil Claude Haiku 4.5 valide Tool-Calls erzeugt und die Infrastruktur nicht bricht, aber die Synthesetreue mit Combined 68.92 und erkannter Halluzination nicht robust genug für hochkritische Tool-Pipelines ist.

**Tool-Execution-Profil**

Die Ausführungsseite ist belastbar. Tool-Calls waren valide, MCP-konform und ohne Retry ausführbar. Das ist für Produktion der erste notwendige Filter, und den besteht das Modell. Bei **Web Search & Tool Selection**, also der Frage, ob ohne expliziten Hinweis Suche statt direktem Fetch nötig ist, erreicht es brauchbare 80 Punkte. Bei **URL Construction & Fetch**, also der Ableitung einer Ziel-URL aus eigenem Wissen und anschließender korrekter Ausführung, liegt es ebenfalls bei 80. Das spricht nicht für starres Tool-Scripting, sondern für funktionale Werkzeugwahl mit brauchbarer situativer Anpassung. Es wirkt jedoch nicht deterministisch genug, um komplexe Verzweigungen oder streng typisierte Agentenketten ohne Guardrails zu tragen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. P2 liegt bei 52.50. Das Muster ist konsistent schwach in den Recherche- und Extraktionsaufgaben: **EU License Research** 40, **HTTP Fetch & Extract** 35, **Web Search & Tool Selection** 40, **Multilingual Search & Synthesis** 40. Das Modell holt Informationen also oft korrekt per Tool, verliert aber bei Verdichtung, Priorisierung oder präziser Rückführung auf die Quelle. Für produktive Pipelines ist das kein Schönheitsfehler, sondern ein Risiko für nachgelagerte Entscheidungen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt der Befund gemischt: Content-Verification-State A und keine Halluzination in diesem Test, aber nur P2=40. Das heißt: Es erfindet dort nichts, paraphrasiert die Tool-Lage aber nicht präzise genug. Da global eine Halluzination erkannt wurde, muss man das als Sicherheitsrisiko werten. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, sinkt das Vertrauen in die gesamte Pipeline.

**Fehlerresilienz**

Bei **Tool Failure Handling (404)**, also dem Test auf transparente Reaktion bei einem fehlgeschlagenen Aufruf, verhält sich das Modell produktionsgerecht. P2=80, keine Halluzination trotz 404. Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. Das ist akzeptabel für reale Tool-Umgebungen.

**Betriebsprofil**

Call 1: 5.43s. MCP-Latenz: 1.35s. Call 2: 3.35s. Total: 60.75s. Schnell in den Einzelaufrufen, aber als End-to-End-Run nicht kurz. Kosten pro Run: $0.034324. Günstig bis moderat, gemessen an der nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für kostensensitive Pipelines mit klaren Tools, engem Antwortformat und nachgelagerter Validierung, etwa Recherche-Vorstufen, Routing, einfache URL- oder Such-Entscheidungen und fehlertolerante Assistenten. Nicht geeignet für Compliance, regulatorische Auswertung, präzise Extraktionsstrecken oder autonome Agentenketten, in denen die textliche Synthese selbst als verlässlicher Output weiterverarbeitet wird. Wenn Sie es einsetzen, dann mit strikter Output-Prüfung, Quellenbindung und einem Verifier nach jedem Tool-Schritt.