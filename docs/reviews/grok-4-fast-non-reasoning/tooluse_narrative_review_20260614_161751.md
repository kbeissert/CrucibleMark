**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:17:51


Bedingt deploy, weil die Tool-Nutzung verlässlich ist und keine Halluzination erkannt wurde, die Synthesetreue aber für produktive Wissensverdichtung zu ungleichmäßig bleibt.

**Tool-Execution-Profil**

Grok 4 Fast Non-Reasoning arbeitet auf der MCP-Ebene sauber. Die Tool-Calls waren valide, ein Retry war nicht nötig, und der P1-Wert zeigt: Das Modell kann einer bestehenden Tool-Infrastruktur grundsätzlich anvertraut werden. Besonders stark ist es beim Web Search & Tool Selection-Test, der ohne expliziten Hinweis prüft, ob statt fetch erst web_search nötig ist. Dort zeigt es echte Werkzeugwahl und nicht nur starres Schema-Folgen. Beim URL-Construction-Test, der die korrekte Ziel-URL aus eigenem Wissen ableitet und dann fetch ausführt, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines mit exakten URL-Erwartungen. Das Muster ist klar: gute Tool-Intelligenz bei der Wahl des Pfads, etwas weniger Präzision bei der letzten operativen Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Der P2-Wert von 60 zeigt ein Modell, das Ergebnisse häufig korrekt zusammenzieht, aber nicht stabil auf dem Niveau arbeitet, das man für Compliance-, Policy- oder mehrsprachige Rechercheketten verlangt. Das sieht man direkt an EU License Research mit schwacher Verdichtung und an Multilingual Search & Synthesis, wo die deutschsprachige Zusammenführung über Sprachgrenzen klar abfällt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Eher ja, und das ist der wichtigere Produktionsbefund. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Content-Verification-State A bei P2 40 heißt: Es bleibt grundsätzlich an der Quelle, verdichtet diese aber nicht präzise genug. Das ist ein Qualitätsproblem, kein Vertrauensbruch.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Tool Failure Handling (404)-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call misst, hat das Modell keinen Seiteninhalt erfunden. P2 80 bedeutet: Es kommuniziert den Fehler hinreichend klar und ersetzt fehlende Daten nicht durch geratenen Inhalt. Genau dieses Verhalten hält eine Tool-Pipeline stabil.

**Betriebsprofil**

Call 1: 2.00s. MCP-Latenz: 1.12s. Call 2: 1.99s. Total: 30.67s.  
Schnell in der Einzelinferenz, aber kein kurzer End-to-End-Run.  
Kosten pro Run: $0.018736. Günstig für Frontier-Betrieb, gemessen an der gezeigten Leistung fair.

**Fazit & Empfehlung**

Geeignet für Such-, Fetch- und Orchestrierungs-Pipelines, in denen korrektes Tool-Verhalten wichtiger ist als hochpräzise Verdichtung. Gut einsetzbar für aktuelle Web-Recherche, Vorstrukturierung und transparente Fehlerbehandlung. Nicht die erste Wahl für Compliance-nahe Auswertung, mehrsprachige Synthese oder Pipelines, in denen aus Tool-Output unmittelbar belastbare Entscheidungsgrundlagen werden. Setzen Sie es als schnellen Operator vor einem stärkeren Prüfschritt ein, nicht als letzte Instanz der Ergebnisverdichtung.