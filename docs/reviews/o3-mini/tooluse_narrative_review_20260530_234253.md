**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:53


Bedingt deploy, weil o3-mini Tool-Aufrufe zuverlässig und protokollkonform ausführt, aber die Synthesequalität mit Halluzinationssignal für produktive Tool-Pipelines noch zu oft vom belegten Tool-Ergebnis wegdriftet.

**Tool-Execution-Profil**

Bei der Werkzeugnutzung wirkt o3-mini kompetent. Der Tool-Call war valide, ein Retry war nicht nötig, und P1 von 90 zeigt eine belastbare Ausführungsebene. Besonders stark ist der Test Web Search & Tool Selection, der ohne expliziten Hinweis prüft, ob statt fetch eine Suche nötig ist: Hier erkennt das Modell die richtige Werkzeugklasse klar. Das spricht gegen starres Pattern-Matching und für echte Auswahlintelligenz.

Weniger präzise ist es beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen ableiten und dann korrekt abrufen kann. Mit P1 80 bleibt es brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen direkt URLs formen lassen. Die MCP-Seite ist damit nicht das Problem. Das Risiko liegt eher in der letzten Meile der Ableitung als im Protokollverhalten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 von 55.83 ist für produktive Synthesis-Pfade zu niedrig, vor allem weil die Schwächen genau dort auftreten, wo verdichtete Ausgabe präzise bleiben muss: Web Search & Tool Selection endet bei P2 35, Multilingual Search & Synthesis bei P2 40. Das Modell findet Informationen, komprimiert sie aber nicht stabil genug in überprüfbare, saubere Ergebnisform.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt o3-mini im akzeptablen Bereich: Content-Verification-State A, keine Halluzination. Das ist das wichtigste Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko. In einer MCP-Pipeline zählt nicht nur, ob das Modell Tools benutzt, sondern ob es ausschließlich aus deren Ergebnissen spricht. Sobald erfundene Fakten als Tool-basierte Antwort erscheinen, verliert die Infrastruktur ihre Auditierbarkeit.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit gescheiterten Tool-Calls prüft, reagiert o3-mini produktionstauglich. P2 80, keine Halluzination trotz Fehler. Es ersetzt fehlende Inhalte nicht durch erfundene Seiteninhalte. Das ist für robuste Pipelines akzeptabel.

**Betriebsprofil**

Total 67.24s pro Run. MCP-Latenz 1.51s. Modellaufrufe 2.19s und 7.51s. Insgesamt langsam. Kosten/Run 0.037873. Für die gebotene Leistung günstig bis moderat.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klarer Tool-Governance, starker Antwortvalidierung und nachgelagerter Faktenprüfung. Gut passend für Recherche-Orchestrierung, Tool-Auswahl und fehlertolerante Assistenzflüsse. Nicht passend für Compliance-, Policy-, oder Executive-Summary-Pipelines, in denen die Endantwort ohne menschliche Kontrolle direkt aus Tool-Ergebnissen abgeleitet werden muss. Wer o3-mini einsetzt, sollte es als starken Tool-Bediener behandeln, nicht als verlässliche letzte Instanz für Synthese.