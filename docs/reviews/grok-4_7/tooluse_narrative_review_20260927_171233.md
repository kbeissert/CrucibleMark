**Deployment-Urteil**

> **Erstellt am:** 27.09.2026, 17:12:33


Bedingt deploy, weil Grok 4.7 die Tool-Schicht meist korrekt bedient, aber die Synthesequalität mit Combined 71.50 und ungültigem Tool-Call-Signal nicht stabil genug für vertrauenssensible Endausgaben ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist klar die stärkere Seite. Mit P1 90 zeigt das Modell, dass es in einer MCP-gestützten Pipeline meist das richtige Werkzeug auswählt und Aufrufe formal brauchbar strukturiert. Besonders stark ist der Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird: Hier handelt Grok 4.7 intelligent und nicht rein schematisch. Das spricht für echte Werkzeugwahl statt starrem Muster.

Weniger sauber ist der URL-Construction-and-Fetch-Test, der prüft, ob das Modell eine Ziel-URL selbst ableitet und dann korrekt abruft. P1 80 ist brauchbar, aber nicht präzise genug für deterministische Pipelines mit engen Erfolgsbedingungen. Das globale Signal „Tool-Call valide: false“ bleibt daher relevant. Es gibt keine Hinweise auf ein Retry-Problem oder Formatkollaps, eher auf punktuelle Ausführungsunschärfe bei konkreten Calls.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt zuverlässig. P2 53.33 ist für ein Frontier-Modell im Produktionskontext zu niedrig, vor allem weil sich die Schwäche durch mehrere Aufgaben zieht: EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis bleiben jeweils bei P2 40. Das Modell holt Informationen also oft korrekt per Tool, verdichtet sie danach aber nicht präzise genug in eine belastbare Antwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde keine Halluzination erkannt. Das ist das zentrale Vertrauenssignal. Grok 4.7 erfindet hier nichts, aber es nutzt die beschafften Inhalte nicht diszipliniert genug aus.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Calls prüft, bleibt das Modell auf der sicheren Seite. Es halluziniert keinen Seiteninhalt trotz Fehler. P2 60 zeigt keine elegante Fehlerbehandlung, aber eine akzeptable für Produktion: lieber Lücke offenlegen als Ersatzinhalt erfinden. Das ist für Tool-Pipelines wichtiger als sprachliche Glätte.

**Betriebsprofil**

Total 112.71s pro Run. Call 1: 1.87s. MCP-Latenz: 1.25s. Call 2: 15.67s. Für die gezeigte Syntheseleistung langsam. Preis laut Modellprofil 2.0 USD pro 1M Input und 6.0 USD pro 1M Output, bei Langkontext teurer. Damit nicht günstig im Verhältnis zur gezeigten Endqualität.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen Tool-Wahl, Web-Zugriff und vorsichtiger Umgang mit Fehlern wichtiger sind als die erste Endformulierung. Nicht geeignet für Compliance-, Policy- oder Executive-Output-Stufen, in denen die Antwort direkt ohne nachgelagerte Verifikation an Menschen oder Systeme geht. Sinnvoll ist Grok 4.7 als beschaffender und planender Zwischenschritt mit nachgeschaltetem Validator oder einer zweiten Syntheseinstanz.