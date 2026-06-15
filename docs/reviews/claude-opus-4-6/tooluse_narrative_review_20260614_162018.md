**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:20:18


Bedingt deploy, weil die Tool-Ausführung stark und protokolltreu ist, aber die erkannte Halluzination im Honeypot das Vertrauen in faktenkritischen MCP-Betrieb begrenzt.

**Tool-Execution-Profil**

Claude Opus 4.6 arbeitet auf der Ausführungsseite klar über Produktionsniveau. Tool-Calls waren valide, Retry war nicht nötig, und der P1-Wert zeigt ein belastbares MCP-Verhalten. Entscheidend ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Fetch unterscheiden lässt, wählte das Modell das richtige Tool durchgängig. Das spricht für echte Orchestrierungsintelligenz und nicht nur für starres Fetch-First-Verhalten. Beim URL-Construction-Test, der korrekte Ziel-URLs aus Eigenwissen verlangt, war die Leistung brauchbar, aber nicht vollständig deterministisch. Das Muster ist damit klar: starke Entscheidung, welches Werkzeug gebraucht wird, etwas weniger Präzision bei der eigenständigen Zieladressierung. Für dynamische Tool-Pipelines ist das ein gutes Profil.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht konsistent genug für High-Trust-Workloads. Starke Verdichtung bei HTTP Fetch & Extract und bei Multilingual Search & Synthesis zeigt, dass das Modell strukturierte Web-Inhalte sauber zusammenziehen kann. Der Gesamtwert auf P2 wird aber durch deutliche Ausreißer gedrückt. Vor allem bei EU License Research und bei Web Search & Tool Selection fiel die inhaltliche Zusammenführung spürbar ab.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das zentrale Risiko. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, wich das Modell auf nicht verifizierten Inhalt aus. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vorwissensbasierte Aussagen als Ergebnis einer Tool-Kette ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell produktionsgerecht. Im 404-Test, der transparentes Fehlermanagement statt erfundenem Ersatzinhalt prüft, kommunizierte es den Ausfall sauber und halluzinierte keinen Seiteninhalt. Das ist für reale MCP-Pipelines ein wichtiger positiver Befund.

**Betriebsprofil**

14.39s und 16.63s auf den Haupt-Calls, 1.17s MCP-Latenz, 193.11s pro Run gesamt. Das ist langsam.  
0.273305 USD pro Run. Das ist teuer.  
Gemessen an der Ausführungsstärke vertretbar. Gemessen an der Synthesetreue in faktenkritischen Pfaden anspruchsvoll.

**Fazit & Empfehlung**

Geeignet für agentische Pipelines mit starker Tool-Orchestrierung, mehrstufiger Web-Recherche, multilingualer Verarbeitung und transparenter Fehlerbehandlung. Nicht geeignet als unkontrollierte Endinstanz in Compliance-, Policy-, Lizenz- oder anderen faktenkritischen Flows, in denen Tool-Ergebnisse strikt belegt bleiben müssen. Deploy nur mit harten Guardrails: Quellenbindung, Antwort auf Tool-Belege beschränken, und nachgelagerte Verifikation für jede normative oder aktuelle Aussage.