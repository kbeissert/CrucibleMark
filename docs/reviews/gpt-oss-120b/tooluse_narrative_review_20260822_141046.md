**Deployment-Urteil**

> **Erstellt am:** 22.08.2026, 14:10:46


Bedingt deploy, weil die Tool-Ausführung stark ist, das Modell aber mit erkannter Halluzination im Honeypot und einem nicht durchgängig validen Tool-Call das Grundvertrauen für kritische MCP-Pipelines nicht durchgehend hält.

**Tool-Execution-Profil**

GPT-OSS 120B erkennt Werkzeuge grundsätzlich gut und agiert nicht bloß nach starrem Muster. Beim Test Web Search & Tool Selection, der ohne Hinweis die Wahl zwischen Suche und direktem Fetch verlangt, wählt es das richtige Tool sicher. Das spricht für echte Werkzeugselektion in offenen Pipelines. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar, aber nicht präzise genug für deterministische Pipelines. Genau dort zeigt sich die Grenze: Das Modell versteht den Arbeitsgang, produziert aber nicht immer einen formal belastbaren Aufruf.

Der P1-Wert ist insgesamt stark, aber der Befund „Tool-Call valide: False“ ist produktionsrelevant. Nicht weil das Modell kein Tooling kann, sondern weil einzelne Aufrufe Protokoll- oder Strukturfehler tragen können. Positiv ist, dass kein Retry erforderlich war. Das wirkt eher wie ein Präzisionsproblem im Call selbst als wie ein grundlegendes Missverständnis des MCP-Ablaufs.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die Synthesis Quality liegt klar unter dem Ausführungsniveau. Bei HTTP Fetch & Extract und Multilingual Search & Synthesis zieht es Informationen zwar aus den Quellen, verdichtet sie aber ungleichmäßig und verliert Details. Für zusammenfassende Assistenz ist das noch nutzbar. Für Compliance, Regulatorik oder präzise Extraktionsketten ist es zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier liegt das eigentliche Risiko. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell und erreicht nur P2=15. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene Fakten als scheinbar toolgestützte Antwort ausgibt, unterminiert es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call prüft, bleibt das Modell akzeptabel. Es erfindet keinen Seiteninhalt und kommuniziert den Fehler grundsätzlich offen. Diese Eigenschaft ist für Produktion wichtig. Ein Tool-Ausfall eskaliert damit nicht sofort zu Falschinformation. Die Fehlerkommunikation ist nicht exzellent, aber brauchbar.

**Betriebsprofil**

Call 1: 4.99s. MCP-Latenz: 1.17s. Call 2: 31.44s. Total: 225.58s.  
Kosten/Run: local.  
Direkte Aussage: lokal günstig, aber langsam für die gelieferte Antworttreue.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Orchestrationspipelines, in denen Tool-Wahl wichtiger ist als präzise Endverdichtung und in denen ein nachgelagerter Verifier jede Antwort gegen Rohquellen prüft. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere High-Trust-Pipelines, in denen das Modell Tool-Ergebnisse strikt wiedergeben muss. Wer GPT-OSS 120B einsetzt, sollte es als Tool-Operator mit externer Verifikation behandeln, nicht als vertrauenswürdige Syntheseinstanz.