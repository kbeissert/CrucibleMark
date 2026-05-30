**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:49:39


Nicht deploy, weil der kombinierte Befund schwach ist, Tool-Calls nicht valide waren und Retries nötig wurden. Dass keine Halluzination markiert wurde, rettet den Einsatz in einer MCP-Pipeline nicht, wenn das Modell die Infrastruktur nicht zuverlässig korrekt ansteuert.

**Tool-Execution-Profil**

Magistral Medium zeigt kein belastbares Tool-Verhalten für Produktion. P1 von 41.67 steht hier für einen wiederkehrenden operativen Mangel, nicht nur für einzelne Ausreißer. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, bleibt das Modell bei 35. Das spricht nicht für echte Werkzeugwahl, sondern für ein starres Muster. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL aus Modellwissen misst, liegt es ebenfalls bei 35. Das Modell scheitert also sowohl an der Auswahl des richtigen Werkzeugs als auch an der korrekten Parametrisierung des Aufrufs.

Weil Retry erforderlich war und die Tool-Calls zugleich als invalide markiert wurden, wirkt das primär wie ein Protokoll- und Ausführungsproblem, nicht wie ein einzelner Denkfehler. Für MCP-gestützte Systeme ist das kritisch, da Orchestrierung nur funktioniert, wenn Calls formal und semantisch sitzen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 von 26.67 zeigt, dass Magistral Medium aus abgerufenen Quellen keine konsistent belastbare Arbeitsantwort formt. Das sieht man besonders an EU License Research mit P2=0 und an Multilingual Search & Synthesis ebenfalls mit P2=0. Nur bei HTTP Fetch & Extract erreicht es brauchbare 40, also eher Extraktion als belastbare Verdichtung über mehrere Schritte.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot-Befund ist widersprüchlich. Bei EU License Research, das prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, liegt P2 bei 0 bei Content-Verification-State B2, aber ohne erkannte Halluzination. Das heißt: Es erfindet nichts offen, bleibt aber auch nicht verlässlich in verifizierbaren Tool-Ergebnissen. Für Compliance-nahe Recherche ist das kein tragfähiges Vertrauensprofil.

**Fehlerresilienz**

Hier liegt die klare Stärke. Beim 404-Test, der misst ob ein gescheiterter Tool-Call transparent behandelt wird, erreicht das Modell P2=80 und halluziniert keinen Seiteninhalt. Das ist produktionsgerecht. Ein fehlerhaftes Werkzeug wird als Fehler kommuniziert, nicht mit erfundenem Ersatz kaschiert.

**Souveränitätsprofil**

Open-weights und souverän einsetzbar, aber nicht fleet-kompetitiv. Das Modell liegt 5.32 Punkte unter dem Fleet-Ø von 66.76. Für souveräne Deployments ist das nur dann attraktiv, wenn Governance wichtiger ist als Tool-Zuverlässigkeit.

**Fazit & Empfehlung**

Geeignet allenfalls für überwachte Pipelines mit einfacher Extraktion, explizit vorgegebenem Tool-Pfad und hartem Validator vor jeder Ausführung. Nicht geeignet für autonome Rechercheketten, Compliance-Workflows, dynamische Tool-Auswahl oder mehrsprachige Web-Synthese. Wer dem Modell eine MCP-Infrastruktur übergeben will, braucht deterministische Guardrails und sollte es nicht als selbstständig werkzeugfähigen Agenten behandeln.