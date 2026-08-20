**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:22:16


Bedingt deploy, weil die Tool-Nutzung insgesamt tragfähig ist, aber ungültige Tool-Calls und eine nur mäßig verlässliche Synthese das Vertrauen in eine MCP-Pipeline begrenzen.

**Tool-Execution-Profil**

Qwen 3.5 27B zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, arbeitet es sicher und erkennt den richtigen Zugriffspfad. Auch bei Multilingual Search & Synthesis und EU License Research ruft es die benötigten Quellen zuverlässig ab. Das spricht für agentisches Grundverständnis.

Schwächer ist die Protokolltreue im Detail. Der globale Befund „Tool-Call valide: false“ ist für Produktion relevanter als der ordentliche P1-Wert. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und dann fetch korrekt ausführen lässt, ist die Ausführung brauchbar, aber nicht deterministisch genug. Das Modell wirkt also intelligent bei der Wahl des Werkzeugs, aber weniger präzise bei der letzten Meile des Calls. Retry war nicht nötig. Das deutet eher auf Ausführungsgenauigkeit als auf Verständnisfehler.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. Die P2-Leistung liegt deutlich unter der Tool-Ausführung. Besonders bei HTTP Fetch & Extract, also bei strukturierter Extraktion realer Seiteninhalte, fällt die Verdichtung zu unsauber aus. Das Muster lautet: Es findet Informationen häufiger, als es sie korrekt und knapp in nutzbare Antworten überführt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen erzwingen soll, bleibt das Vertrauenssignal gemischt. Es halluziniert dort nicht offen, aber P2 20 zeigt, dass die Antwort die abgefragten Web-Inhalte kaum sauber in belastbare Aussageform bringt. Da im Gesamtlauf Halluzination erkannt wurde, ist das ein Sicherheitsrisiko. In einer Tool-Pipeline zählt nicht nur, ob das Modell Tools benutzt, sondern ob ausgegebene Fakten eindeutig auf Tool-Ergebnissen beruhen.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlschlagenden Tool-Calls misst, reagiert das Modell akzeptabel. Es erfindet keinen Seiteninhalt trotz Fehler. P2 60 ist kein starker Wert, aber für Produktion deutlich wichtiger ist hier die Transparenz: Fehler werden eher stehen gelassen als verdeckt überschrieben. Das ist ein brauchbares Fundament für Orchestrierung mit externem Retry oder Fallback.

**Betriebsprofil**

Total 764.95s: langsam.  
Call 1 7.55s, Call 2 117.62s, MCP-Latenz 2.32s.  
Kosten/Run: local. Günstig im Geld, teuer in Laufzeit gemessen an der Leistung.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkontrollierte Pipelines mit menschlicher Nachkontrolle, klaren Tool-Schemas und externer Validierung der Endantwort. Besonders brauchbar dort, wo Werkzeugwahl wichtiger ist als präzise Verdichtung, etwa Recherche-Vorstufen, Sammelagenten oder mehrstufige Routing-Aufgaben. Nicht geeignet für Compliance-, Fakten- oder Extract-Transform-Report-Pipelines, in denen die finale Antwort strikt aus Tool-Output abgeleitet und formal verlässlich sein muss.