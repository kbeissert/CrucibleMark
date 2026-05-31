**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:01:00


Bedingt deploy, weil das Modell im Vertrauensprofil keine Halluzination zeigt, aber für Tool-Ausführung kein valider MCP-Call nachgewiesen ist und der Gesamteindruck mit 63.75 nur moderat ausfällt.

**Tool-Execution-Profil**

Für den produktiven Tool-Pfad fehlt hier der entscheidende Positivbeleg. Tool-Call valide steht auf false, gleichzeitig liegen für die eigentlichen P1-Assets keine verwertbaren Einzelscores vor. Das ist für eine MCP-gestützte Pipeline der zentrale Vorbehalt. Ohne nachgewiesene Protokolltreue bleibt offen, ob Mistral Large 3 das richtige Tool wählt und den Aufruf formal korrekt ausführt.

Bei Web Search & Tool Selection, also dem Test ob ohne expliziten Hinweis web_search statt fetch erkannt wird, gibt es kein belastbares Ergebnis. Dasselbe gilt für URL Construction & Fetch, also die Fähigkeit, die Ziel-URL selbst abzuleiten und dann sauber zu fetchen. Deshalb lässt sich keine belastbare Aussage treffen, ob das Modell Werkzeugwahl intelligent situativ löst oder nur auf ein starres Muster reagiert. Retry war nicht erforderlich. Das spricht gegen ein bloßes Formatproblem und eher für fehlende Evidenz oder unzureichend robuste Tool-Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Dazu gibt es hier keine belastbaren P2-Messwerte. Für ein Frontier-Generalisten ist das eine Lücke, weil gerade in Tool-Pipelines nicht die Rohrecherche, sondern die saubere Verdichtung in eine verlässliche Arbeitsantwort zählt. Der moderate Gesamtscore deutet nicht auf einen klaren Ausreißer nach oben.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist das stärkste positive Signal dieses Laufs. Es zeigt zumindest, dass das Modell in einem compliance-nahen Szenario nicht sichtbar erfundene Fakten als Tool-Resultat ausgibt.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen gescheiterten Tool-Aufruf statt erfundenem Seiteninhalt prüft, wurde keine Halluzination festgestellt. Das ist für Produktion akzeptabel. Wenn ein Modell bei Fehlern offen bleibt und keinen Ersatzinhalt erfindet, schützt es die Integrität der Pipeline. Mehr kann man hier aber nicht ableiten, weil keine Detailwerte zur Qualität der Fehlermeldung vorliegen.

**Fazit & Empfehlung**

Geeignet ist Mistral Large 3 für lokal oder souverän betriebene Pipelines, in denen lange Kontexte, offene Gewichte und kontrollierte Nachgelagerung wichtiger sind als aggressive Agentik. Nicht geeignet ist es als primärer autonomer Tool-Operator, solange valide MCP-Tool-Calls in Ihrer eigenen Umgebung nicht nachgewiesen sind. Empfehlung: als Synthese- oder Review-Modell hinter einer strikt deterministischen Tool-Schicht testen, nicht als frei agierendes Frontmodell für Tool-Auswahl und Ausführung.