**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:15:46


Bedingt deploy, weil Gemini 3.5 Flash valide Tool-Calls liefert, keine Halluzination im Lauf zeigte und mit solidem Gesamtbild zuverlässig in die Infrastruktur greift, die Synthesequalität aber für entscheidungsrelevante Outputs zu uneinheitlich bleibt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Mit P1 90 wählt es Werkzeuge meist richtig, erzeugt valide Calls und bleibt MCP-konform. Entscheidend ist, dass es beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, sauber auf web_search schaltet. Das spricht gegen reines Schema-Folgen und für echte Werkzeugwahl anhand der Aufgabe.

Beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen ableiten und dann korrekt abrufen kann, fällt es auf P1 80 zurück. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, in denen URL-Bildung präzise sitzen muss. Retry war nicht erforderlich. Das Problem liegt also nicht im Protokollformat, sondern in der inhaltlichen Präzision einzelner Ausführungsschritte. Als vision-language MoE-Modell sollte man den Text-only-Befund zudem nicht überdehnen. Er zeigt nur den sprachlichen Tool-Use-Teil, nicht die multimodale Hauptstärke.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. P2 56.67 zeigt, dass Gemini 3.5 Flash gefundene Inhalte oft korrekt aufnimmt, aber nicht stabil genug in belastbare, knappe Ergebnistexte überführt. Das sieht man besonders bei EU License Research und Multilingual Search & Synthesis, wo die Verdichtung auf 40 fällt. Dagegen ist HTTP Fetch & Extract mit 80 deutlich sauberer. Kuratierte Extraktion liegt ihm mehr als mehrquellige Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser als die P2-Werte vermuten lassen. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Content-Verification-State A stützt dieses Urteil. Das Modell paraphrasiert schwach, aber es erfindet nicht.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem scheiternden Tool-Call misst, bleibt das Modell transparent und halluziniert keinen Ersatzinhalt. P2 60 ist kein Qualitätswert für elegante Fehlerberichte, aber produktiv ist der entscheidende Punkt erfüllt: Es bricht Vertrauen nicht durch erfundene Seitendaten.

**Betriebsprofil**

Call 1: 1.56s. MCP-Latenz: 0.88s. Call 2: 6.99s. Total: 56.58s.  
Kosten/Run: 0.022908 USD.  
Direkte Einordnung: Tool-Aufrufe schnell, Gesamtlauf lang, Kosten moderat. Für die gezeigte Leistung wirtschaftlich vertretbar, aber nicht aggressiv günstig.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klarer Tool-Orchestrierung, Web-Recherche, Fetch-Extraktion und robustem Fehlerpfad, besonders wenn Nicht-Halluzinieren wichtiger ist als sprachlich starke Endverdichtung. Nicht die erste Wahl für Compliance-, Policy- oder Executive-Reporting-Strecken, in denen mehrquellige Synthese präzise und formstabil sein muss. Empfehlenswert als ausführendes Recherche- und Retrieval-Modell hinter einer nachgelagerten Validierungs- oder Redaktionsstufe.