**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:17:16


Nicht deploy für autonome MCP-Pipelines, weil der kombinierte Befund schwach ist, der Tool-Call nicht valide war und Retries erforderlich waren, obwohl keine offene Halluzination erkannt wurde.

**Tool-Execution-Profil**

Magistral Medium zeigt kein belastbares Tool-Verhalten für Produktion. Der P1-Wert von 41.67 ist nicht nur niedrig, sondern verteilt sich auch auf die kritischen Steuerungsaufgaben. Beim Test Web Search & Tool Selection, der prüft, ob das Modell ohne Hinweis zwischen Suche und direktem Abruf unterscheidet, erreicht es nur 35. Das spricht gegen echte Werkzeugintelligenz. Beim Test URL Construction & Fetch, der die korrekte Ziel-URL aus Vorwissen ableiten und dann sauber abrufen soll, bleibt es ebenfalls bei 35. Das Muster wirkt daher nicht wie adaptive Tool-Wahl, sondern wie unsichere Standardisierung auf einen unpassenden Ablauf.

Der 404-Fall mit P1 75 zeigt, dass es Tool-Fehler grundsätzlich verarbeiten kann. Das kompensiert aber nicht die schwache Trefferquote bei Auswahl und Aufrufform. Da Retry erforderlich war und der Tool-Call als nicht valide markiert ist, liegt das Problem eher bei Protokoll- und Formatreife als bei reinem Aufgabenverständnis. Für MCP heißt das: Orchestrierung muss korrigierend eingreifen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Insgesamt schwach. Der P2-Wert von 26.67 zeigt, dass aus abgerufenen Daten keine verlässliche, knappe Arbeitsantwort entsteht. Positiv ist nur HTTP Fetch & Extract mit P2 40 und Tool Failure Handling (404) mit P2 80. Kritische Ausfälle bleiben aber bestehen: EU License Research und Multilingual Search & Synthesis liegen bei P2 0, also genau dort, wo Quellentreue und Verdichtung zentral sind.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist negativ. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Modellwissen kommen, endet die Aufgabe mit P2 0 bei Content-Verification-State B2. Das ist keine harte Halluzination im Flagging, aber es ist ein Verifikationsversagen. Für Compliance-, Policy- und Research-Pipelines reicht das nicht.

**Fehlerresilienz**

Hier ist das Modell brauchbarer. Im 404-Test, der transparenten Umgang mit fehlschlagenden Aufrufen statt erfundenem Seiteninhalt misst, liefert es P2 80 und halluziniert nicht. Das ist produktionsgerecht. Wenn ein Tool scheitert, bleibt die Antwort zumindest ehrlich.

**Betriebsprofil**

Call 1: 40.28s. Call 2: 11.05s. Total: 308.48s. Langsam.  
Kosten pro Run: $0.033517. Nicht teuer, aber für diese Leistung klar zu hoch.

**Fazit & Empfehlung**

Geeignet höchstens für assistive, menschlich überwachte Pipelines, in denen Tool-Fehler offen kommuniziert werden sollen und ein Operator die Ergebnisse prüft. Nicht geeignet für autonome Rechercheketten, Compliance-Workflows, mehrsprachige Wissenssynthese oder jede MCP-Umgebung, die valide Tool-Aufrufe und quellentreue Verdichtung deterministisch erwartet. Das Modell argumentiert eher, als dass es zuverlässig mit Werkzeugen arbeitet.