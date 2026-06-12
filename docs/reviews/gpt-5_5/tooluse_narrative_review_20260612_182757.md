**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:27:57


Bedingt deploy, weil die Gesamtausbeute mit 77.50 solide ist und keine Halluzination erkannt wurde, aber der Tool-Call nicht durchgängig valide war und damit das zentrale Vertrauenssignal für MCP-Pipelines fehlt.

**Tool-Execution-Profil**

GPT-5.5 zeigt mit P1 90.00 grundsätzlich starke Tool-Nutzung. Das spricht für gute Schrittplanung und dafür, dass das Modell werkzeuggestützte Aufgaben nicht reflexhaft aus dem Parametergedächtnis beantwortet. Für den Produktionseinsatz bleibt aber der Befund „Tool-Call valide: false“ der entscheidende Vorbehalt. Das ist kein kosmetischer Makel, sondern ein Protokollrisiko: Ein stark planendes Modell hilft wenig, wenn einzelne Aufrufe nicht sauber im erwarteten MCP-Format landen.

Zu Web Search & Tool Selection und URL Construction & Fetch liegen keine Einzelscores vor. Deshalb lässt sich nicht belastbar sagen, ob GPT-5.5 aktiv zwischen Suche und direktem Abruf differenziert oder oft einem festen Fetch-Muster folgt. Der hohe P1-Wert deutet auf Werkzeugintelligenz hin, der Validitätsfehler verhindert aber ein uneingeschränktes Urteil über deterministische Orchestrierung. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein dauerhaftes Verständnisproblem und eher für punktuelle Protokoll- oder Formatinstabilität.

**Synthesetreue**

Wie gut verdichtet es? Mit P2 66.67 arbeitet GPT-5.5 in der Verdichtung brauchbar, aber nicht auf dem Niveau, auf dem Architekten Tool-Ergebnisse ohne Nachkontrolle weiterreichen sollten. Für Zusammenfassungen, Recherche-Notizen und operatorunterstützte Workflows reicht das. Für faktendichte Übergaben zwischen Pipeline-Stufen ist die Kompressionsqualität zu uneinheitlich.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist das wichtigere Vertrauenssignal. GPT-5.5 hat hier die Tool-Grenze respektiert.

**Fehlerresilienz**

Im Test Tool Failure Handling (404), der prüft ob ein Modell bei einem gescheiterten Abruf transparent bleibt statt Seiteninhalt zu erfinden, halluzinierte GPT-5.5 keinen Ersatzinhalt. Das ist produktionsgerecht. Ein Tool-Fehler bleibt damit ein behandelbarer Betriebsfehler und wird nicht zum stillen Datenfehler.

**Betriebsprofil**

Call 1: 32.20s  
MCP-Latenz: 0.94s  
Call 2: 19.36s  
Total: 314.99s  

Langsam. Für diese Leistungsklasse operativ teuer in Zeit. Preis: nicht lokal, API-Modell mit $5.0 pro 1M Input und $30.0 pro 1M Output. Monetär Frontier-typisch teuer.

**Fazit & Empfehlung**

Geeignet für recherchierende, mehrstufige Pipelines mit menschlicher Abnahme, für agentische Vorplanung und für Kontexte mit langen Eingaben. Nicht die erste Wahl für strikt deterministische MCP-Strecken, in denen jeder Tool-Call formal korrekt sein muss und verdichtete Ausgaben direkt maschinell weiterverarbeitet werden. Wenn Sie GPT-5.5 einsetzen, dann mit Schema-Validierung, Guardrails auf Tool-Aufrufe und einer Prüfschicht zwischen Tool-Ergebnis und finaler Synthesis.