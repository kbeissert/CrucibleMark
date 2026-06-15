**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:18:50


Bedingt deploy: GPT-4o ist für MCP-gestützte Tool-Pipelines bei Tool-Ausführung verlässlich, aber die Syntheseleistung ist zu inkonsistent, um unbeaufsichtigt faktenkritische Endausgaben zu tragen.

**Tool-Execution-Profil**

Das Modell arbeitet auf der Ausführungsebene stark. Tool-Calls waren valide, MCP-protokollkonform und ohne Retry nutzbar. Das ist für Produktion der erste notwendige Filter, und GPT-4o besteht ihn.

Bei Web Search & Tool Selection, das ohne expliziten Hinweis prüft, ob web_search statt fetch nötig ist, trifft es die Werkzeugwahl sicher. Das spricht gegen reines Musterfolgen und für brauchbare Tool-Intelligenz in dynamischen Pfaden. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und anschließendes Fetch misst, bleibt die Ausführung brauchbar, aber weniger deterministisch. Das Modell kann also den richtigen Operatortyp wählen, ist aber bei selbst konstruierten Zieladressen nicht präzise genug für fragile Fetch-Ketten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung ist der klare Schwachpunkt. Besonders bei HTTP Fetch & Extract, das strukturierte Fakten aus echtem Seiteninhalt prüft, und bei Multilingual Search & Synthesis, das sprachübergreifende Recherche mit deutscher Verdichtung misst, verliert GPT-4o Präzision und Selektionsschärfe. Für produktive Pipelines heißt das: Die Beschaffung klappt häufiger als die saubere Weiterverarbeitung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen erzwingen soll, bleibt der Vertrauensbefund akzeptabel: keine Halluzination, Content-Verification-State A. Dennoch ist das globale Halluzinationssignal aktiv. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgibt, beschädigt es das Vertrauen in die gesamte Infrastruktur.

**Fehlerresilienz**

Im 404-Test, der einen fehlschlagenden Tool-Call provoziert, reagiert GPT-4o produktionsgerecht. Es kommuniziert den Fehler transparent und erfindet keinen Seiteninhalt. Genau dieses Verhalten ist in robusten Pipelines akzeptabel, weil der Orchestrator den Fehlerzustand sauber weiterverarbeiten kann.

**Betriebsprofil**

0.71s erster Call, 1.05s MCP-Latenz, 2.19s zweiter Call, 23.68s total.  
Kosten pro Run: 0.032734.  
Direktaussage: schnell in den Einzelaufrufen, aber hoher End-to-End-Overhead; für die gezeigte Gesamtleistung eher nicht günstig.

**Fazit & Empfehlung**

Geeignet für allgemeine Recherche-Pipelines, Tool-Auswahl, Web-Navigation und überwachte Assistenzsysteme, in denen ein nachgelagerter Validator oder ein Mensch die Verdichtung prüft. Nicht geeignet als alleinige Instanz für Compliance, mehrsprachige Faktensynthese oder Extraktionsstrecken, bei denen die Antwort direkt als vertrauenswürdiges Tool-Ergebnis weitergereicht wird. Wer GPT-4o einsetzt, sollte die Tool-Ausführung nutzen, aber die Endsynthese absichern.