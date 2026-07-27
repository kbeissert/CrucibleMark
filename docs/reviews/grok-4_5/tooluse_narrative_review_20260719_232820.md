**Deployment-Urteil**

> **Erstellt am:** 19.07.2026, 23:28:20


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Tool-Calls nicht durchgehend valide waren und die Synthesetreue mit Combined 74.33 nur für überwachte Tool-Pipelines trägt. Halluzination wurde nicht erkannt, das hält das Vertrauensfundament intakt.

**Tool-Execution-Profil**

Grok 4.5 zeigt echte Werkzeugintelligenz statt bloßem Schema-Following. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die Werkzeugwahl sicher. Das spricht für brauchbare Orchestrierung in dynamischen MCP-Flows. Beim URL-Construction-Test, der die Ableitung einer korrekten Ziel-URL aus Vorwissen prüft, ist es dagegen nur ordentlich: Die URL wird oft brauchbar konstruiert, aber nicht präzise genug für vollständig deterministische Pipelines. Dazu kommt das formale Warnsignal, dass der Tool-Call insgesamt nicht durchgehend valide war. Retry war nicht erforderlich, daher wirkt das weniger wie ein instabiles Formatproblem und mehr wie punktuelle Ungenauigkeit in der letzten Meile des Calls.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. HTTP Fetch & Extract ist stark und zeigt, dass Grok 4.5 strukturierte Web-Inhalte sauber in Antworten überführen kann. Sobald die Aufgabe stärker verdichtend und mehrsprachig wird, fällt die Qualität sichtbar ab. Multilingual Search & Synthesis bleibt bei der Zusammenführung deutscher Ausgabe aus fremdsprachigen Quellen zu grob. Für Pipelines, in denen die Antwort selbst das Produkt ist, ist das der eigentliche Engpass.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Honeypot-Signal ist kritisch. In EU License Research, das prüfen soll, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, liegt P2 nur bei 20. Es halluziniert dabei nicht offen, aber es bleibt auch nicht verlässlich an der recherchierten Evidenz. Für Compliance-, Policy- und Rechtsnähe ist das ein klares Vertrauensdefizit.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf fehlgeschlagene Tool-Calls statt erfundenem Seiteninhalt misst, bleibt Grok 4.5 auf der sicheren Seite. Es erfindet keinen Ersatzinhalt. P2 60 heißt: kommunikativ nicht immer präzise, aber produktionsfähig. Das ist akzeptabel, weil die Pipeline den Fehlerzustand weiterverarbeiten kann.

**Betriebsprofil**

Call 1: 2.36s. MCP-Latenz: 1.32s. Call 2: 10.02s. Total: 82.15s.  
Für die gezeigte Qualität: eher langsam.  
Preis: $2.0/M Input, $6.0/M Output. Für Frontier-Cloud moderat, aber nicht günstig, wenn die Synthese nachbearbeitet werden muss.

**Fazit & Empfehlung**

Geeignet für recherchierende und orchestrierende Pipelines, in denen das Modell Tools wählen, Inhalte holen und Zwischenergebnisse an nachgelagerte Prüfschritte übergeben soll. Nicht geeignet als alleinige letzte Instanz für Compliance, Lizenzauslegung, mehrsprachige Verdichtung oder andere Fälle, in denen die textliche Synthese selbst belastbar sein muss. Deploy nur mit engem Output-Checking, vorzugsweise mit strukturierten Antworten und einem separaten Verifikationsschritt vor Freigabe.