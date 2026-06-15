**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:21:12


Bedingt deploy, weil die Ausführungskompetenz hoch wirkt, aber der Tool-Call nicht valide war und damit die Übergabe an eine MCP-Tool-Infrastruktur noch kein belastbarer Standardfall ist.

**Tool-Execution-Profil**

Xiaomi MiMo V2.5 zeigt mit P1 90 eine klare operative Stärke bei Tool-Aufgaben. Das spricht für gutes Planen und brauchbare Werkzeugansteuerung. Der kritische Gegenpunkt ist jedoch eindeutig: Der registrierte Tool-Call war nicht valide. Für Produktion heißt das nicht, dass das Modell das falsche Werkzeugprinzip wählt, sondern dass die Protokolltreue im entscheidenden Moment nicht zuverlässig genug war.

Zu Web Search & Tool Selection sowie URL Construction & Fetch liegen keine Einzelwerte vor. Deshalb lässt sich nicht sauber belegen, ob das Modell aktiv zwischen Suche und direktem Abruf unterscheidet oder ob es eher einem festen Ausführungsmuster folgt. Aus dem Gesamtbild lässt sich nur ableiten: Es hat offenbar die grundsätzliche Tool-Logik, aber noch keinen Nachweis für deterministische MCP-Konformität. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein bloßes Formatstolpern und eher für einen einmaligen Validitätsfehler innerhalb einer ansonsten kompetenten Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Mit P2 70 arbeitet das Modell brauchbar, aber nicht mit der Präzision, die man für entscheidungsrelevante Verdichtung bevorzugt. Es kann Ergebnisse zusammenführen, neigt aber nicht zu maximal straffer, belastbarer Extraktion. Für Analysten-Assistenz ist das tragbar. Für Compliance- oder Policy-Synthesen ist es noch zu weich.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Test EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das wichtigste Vertrauenssignal in diesem Lauf. Das Modell hat die Tool-Grenze also nicht sichtbar überschritten.

**Fehlerresilienz**

Im Test Tool Failure Handling (404), der die Reaktion auf fehlschlagende Abrufe prüft, hat Xiaomi MiMo V2.5 keinen Seiteninhalt erfunden. Das ist produktionsrelevant gut. Transparente Fehlerkommunikation ist in Tool-Pipelines akzeptabel. Ein Modell, das bei 404 nichts erfindet, bleibt als Orchestrator grundsätzlich vertrauensfähig.

**Betriebsprofil**

Total 75.08s. Langsam.  
Call 1: 2.35s, MCP-Latenz: 0.74s, Call 2: 9.42s.  
Kosten/Run: local. Günstig im Betrieb, aber die Laufzeit ist im Verhältnis zur nur guten Gesamtleistung hoch.

**Fazit & Empfehlung**

Geeignet für lokal betriebene, reasoning-lastige Pipelines mit menschlicher Nachkontrolle, etwa Recherche-Orchestrierung, Vorstrukturierung und mehrstufige Analyse mit großen Kontextfenstern. Nicht die erste Wahl für streng deterministische MCP-Strecken, in denen jeder Tool-Call formal valide sein muss und Synthesen ohne Nacharbeit verwertbar sein sollen. Vor produktivem Rollout braucht es eine harte Validierungsschicht für Tool-Calls und idealerweise ein Schema-Enforcement vor der Tool-Übergabe.