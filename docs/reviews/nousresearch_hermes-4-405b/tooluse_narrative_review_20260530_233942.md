**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:39:42


Bedingt deploy, weil Hermes 4 405B valide Tool-Calls ohne Halluzinationssignal liefert, die Synthesequalität mit 63.33 aber nicht stark genug für unbeaufsichtigte, entscheidungskritische Auswertung ist.

**Tool-Execution-Profil**

Das stärkste Signal ist P1 90.00 bei zugleich validem Tool-Call und ohne Retry-Bedarf. Das Modell versteht also die MCP-Mechanik und produziert formal belastbare Aufrufe. Für Produktionspipelines ist das ein klares Plus, weil keine Nachkorrektur auf Protokollebene nötig war.

Die Detaildaten zur Werkzeugwahl sind dünn, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelwerte vorliegen. Deshalb lässt sich nicht sauber trennen, ob Hermes 4 405B das passende Tool aktiv auswählt oder primär einem robusten Calling-Schema folgt. Der hohe P1-Wert spricht dennoch eher für echte Ausführungsstabilität als für Zufall. Für dynamische Pipelines mit konkurrierenden Tool-Pfaden bleibt aber ein Restzweifel: Die Call-Qualität ist belegt, die Tool-Intelligenz nur indirekt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht präzise genug für hochkritische Entscheidungen ohne zweite Instanz. P2 63.33 bedeutet: Das Modell kann Ergebnisse zusammenführen, verliert dabei aber wahrscheinlich Nuancen, Prioritäten oder Belegtreue. Für Retrieval-gestützte Assistenten ist das brauchbar. Für Compliance, Vertragsauslegung oder technische Freigaben ist es zu knapp.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. Hermes 4 405B hat hier das Fundament nicht beschädigt.

**Fehlerresilienz**

Im Test Tool Failure Handling (404), der transparente Reaktion auf fehlschlagende Tool-Calls gegen erfundenen Ersatzinhalt prüft, halluzinierte das Modell keinen Seiteninhalt. Das ist für Produktion akzeptabel. Ein Tool darf scheitern. Kritisch wäre nur, wenn das Modell den Fehler verdeckt und Fakten erfindet. Genau das ist hier nicht passiert.

**Betriebsprofil**

Total 46.36s pro Run. Damit klar langsam.  
MCP-Latenz 0.90s, die Laufzeit liegt also überwiegend am Modell.  
Kosten 0.006693 pro Run. Damit günstig für Frontier-Klasse.  
Urteil: gute Tool-Stabilität zu niedrigen Kosten, aber mit spürbarer Wartezeit.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines, in denen korrekte Tool-Ausführung und transparente Fehlerbehandlung wichtiger sind als perfekte Verdichtung: Recherche-Assistenz, interne Analysten-Workflows, Vorverarbeitung vor menschlicher Prüfung. Nicht die richtige Wahl für End-to-End-Automatisierung mit hoher Folgekostenwirkung, wenn die Antwort selbst bereits entscheidungsreif sein muss. Wer deployt, sollte Retrieval und Tooling aktiv nutzen und die finale Synthese bei kritischen Fällen durch Validatoren oder Human Review absichern.