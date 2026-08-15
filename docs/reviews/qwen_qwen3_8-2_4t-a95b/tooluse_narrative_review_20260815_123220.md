**Deployment-Urteil**

> **Erstellt am:** 15.08.2026, 12:32:20


Bedingt deploy, weil die Tool-Nutzung stark ist, aber die Calls nicht durchgängig valide sind und die Synthesequalität für produktionskritische Pipelines zu ungleich ausfällt. Der kombinierte Befund ist gut, das Vertrauenssignal reicht aber nicht für unbewachte Übergabe einer Tool-Infrastruktur.

**Tool-Execution-Profil**

Qwen3.8-2.4T-A95B zeigt echte Werkzeugintelligenz statt starrer Muster. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es zuverlässig, dass zuerst web_search statt fetch nötig ist. Das spricht für brauchbare Planungsfähigkeit in dynamischen MCP-Pipelines.

Weniger sauber ist die Ausführungsschicht. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch misst, arbeitet es brauchbar, aber nicht deterministisch genug für harte Automationspfade. Die invalide Tool-Call-Bewertung trotz hoher P1-Leistung zeigt: Das Modell versteht die Werkzeugrolle, produziert aber nicht in jedem Schritt protokollsaubere Aufrufe. Für produktive Nutzung heißt das: Orchestrator ja, aber mit Validator, Schema-Gate und enger Tool-Wrapping-Schicht.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht verlässlich scharf genug. Die P2-Leistung bleibt mit 66.67 klar hinter der Tool-Ausführung zurück. In HTTP Fetch & Extract und URL Construction & Fetch verdichtet es ordentlich, bei Multilingual Search & Synthesis bricht die Qualität deutlich ein. Das ist relevant, weil der Engpass hier nicht Recherche, sondern belastbare Zusammenführung ist.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja, mit Restzweifel. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert es nicht. Das ist das zentrale Vertrauenssignal. Allerdings ist die Auswertung nur mittelstark, was auf zu lockere Bindung an die Quelle statt auf freie Erfindung hindeutet.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparenten Umgang mit einem fehlgeschlagenen Tool-Aufruf gegen erfundenen Ersatzinhalt stellt, kommuniziert das Modell den Fehler ohne Halluzination. Genau dieses Verhalten braucht eine Tool-Pipeline: sichtbarer Ausfall statt stiller Falschantwort.

**Betriebsprofil**

Call 1: 3.45s. MCP-Latenz: 1.03s. Call 2: 48.51s. Total: 317.92s. Langsam.  
Kosten/Run: local. Günstig im direkten Run-Kostenbild, aber teuer in Zeit pro Aufgabe.  
Für das gezeigte Leistungsniveau ist das Betriebsprofil nur tragbar, wenn Durchsatz nicht kritisch ist.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines mit vorgeschalteter Tool-Validierung, klaren Antwortformaten und nachgelagerter Prüfung der Ergebnisverdichtung. Nicht geeignet für Compliance-, Policy- oder mehrsprachige Executive-Synthesis-Pfade, in denen die Zusammenfassung selbst das Produkt ist. Wenn Sie ein Modell suchen, das Tools klug auswählt und Fehler ehrlich meldet, ist es ein brauchbarer Steuerknoten. Wenn Sie ein Modell suchen, dem Sie auch die letzte Verdichtungsschicht ohne Kontrolle überlassen, ist es noch nicht robust genug.