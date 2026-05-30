**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:42


Bedingt deploy, weil Kimi K2.6 valide Tool-Calls liefert, keine Halluzination im Lauf zeigte und mit 74.50 insgesamt produktionsfähig wirkt, aber die Verdichtung der Tool-Ergebnisse sichtbar hinter der Ausführungsqualität zurückbleibt.

**Tool-Execution-Profil**

Das Modell arbeitet MCP-konform. Der Tool-Call war valide, ein Retry war nicht nötig. Das ist für agentische Pipelines der erste harte Vertrauensbeleg. In den Werkzeugtests zeigt Kimi K2.6 brauchbare, aber nicht überragende Auswahlintelligenz. Beim Web-Search-&-Tool-Selection-Test, der ohne Hinweis zwischen Suche und direktem Fetch unterscheiden lässt, erkennt es den Bedarf für web_search solide, aber nicht deterministisch genug für hochstrikte Router. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus eigenem Wissen verlangt, konstruiert es die URL brauchbar und führt fetch korrekt aus, bleibt aber ebenfalls bei 80 in P1. Das spricht nicht für stumpfes Musterfolgen. Es zeigt echte Werkzeugwahl. Nur die Präzision ist nicht auf dem Niveau, auf dem man es ohne Guardrails frei in verzweigte Tool-Ketten laufen lassen würde.

**Synthesetreue**

Wie gut verdichtet es? Nur ordentlich. P2 von 63.33 heißt: Die Zusammenführung der gefundenen Inhalte ist meist brauchbar, aber oft zu grob, zu knapp oder nicht präzise genug in der Priorisierung von Details. Das sieht man konsistent über mehrere Assets mit wiederkehrenden 60er-Werten in EU License Research, HTTP Fetch & Extract, Web Search & Tool Selection, URL Construction & Fetch und Multilingual Search & Synthesis.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil deutlich besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb Kimi K2.6 im verifizierten Tool-Kontext. Content-Verification-State A bei ausbleibender Halluzination ist für Compliance-nahe Recherchepfade ein belastbares Signal.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der das Verhalten bei fehlschlagendem Tool-Aufruf misst, kommunizierte das Modell den Fehler transparent und erfand keinen Seiteninhalt. P2 von 80 ist hier wichtiger als Stil. Die Infrastruktur bleibt vertrauenswürdig, wenn das Modell Scheitern als Scheitern ausweist.

**Betriebsprofil**

Call 1: 9.77s. MCP-Latenz: 1.54s. Call 2: 26.39s. Total: 226.23s.  
Kosten pro Run: 0.008944 USD.  
Direktes Urteil: langsam im Gesamtlauf, aber günstig für die gezeigte Tool-Leistung.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Fetch- und Fehlerbehandlungs-Pipelines, in denen korrekte Tool-Nutzung wichtiger ist als elegante oder stark verdichtete Endsynthese. Nicht die erste Wahl für Executive Summaries, Compliance-Memos mit hoher Formulierungspräzision oder Pipelines, in denen die letzte Antwort ohne nachgelagerte Validierung direkt an Fachentscheider geht. Empfehlung: als Orchestrator mit enger Ausgabe-Schablone, Extraktionsschema und optionalem nachgelagerten Reviewer-Modell einsetzen.