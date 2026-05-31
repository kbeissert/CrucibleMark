**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:53:17


Bedingt deploy, weil die Tool-Ausführung belastbar ist, die Verdichtung der Tool-Ergebnisse aber zu oft an Präzision und Belegtreue verliert. Der kombinierte Eindruck ist brauchbar, aber nicht vertrauensstark genug für unüberwachte High-Stakes-Pipelines.

**Tool-Execution-Profil**

DeepSeek V3.1 671B nutzt die MCP-Toolschicht kompetent. Die Calls waren valide, ein Retry war nicht nötig, und P1=90 bestätigt, dass das Modell die Infrastruktur grundsätzlich beherrscht. Besonders stark ist Web Search & Tool Selection: In dem Test, der prüft, ob ohne expliziten Hinweis statt fetch ein web_search nötig ist, erkennt es die richtige Werkzeugklasse sicher. Das spricht für echte Werkzeugwahl und nicht nur für starres Schema-Verhalten.

Weniger sauber ist URL Construction & Fetch. In dem Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetch ausführt, erreicht es nur solide, nicht deterministische Präzision. Für Pipelines mit bekannten Zielsystemen ist das akzeptabel. Für Systeme, die aus freier Aufgabenformulierung belastbare URL-Konstruktion erwarten, bleibt Aufsicht nötig.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2=52.5 ist der eigentliche Risikowert dieses Modells. Bei HTTP Fetch & Extract und Multilingual Search & Synthesis zeigt sich, dass es gefundene Informationen nicht stabil genug in belastbare, knappe Ausgaben überführt. Es findet oft den richtigen Stoff, verliert aber bei Priorisierung, Genauigkeit oder sprachübergreifender Zusammenführung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt das Bild gemischt. Positiv ist, dass keine Halluzination erkannt wurde und der Content-Verification-State sauber ist. Kritisch ist aber P2=20 in genau dem Test, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden. Das ist ein Sicherheitsrisiko, weil eine Pipeline dann formal korrekt Tools nutzt, aber in der Endantwort den belegten Inhalt nicht präzise genug transportiert. Der globale Halluzinationsbefund verschärft das: Nicht als Stilproblem, sondern als Vertrauensbruch gegenüber der Tool-Infrastruktur.

**Fehlerresilienz**

Bei Tool Failure Handling (404), also dem Test auf transparenten Umgang mit fehlgeschlagenen Tool-Calls, reagiert das Modell produktionstauglich. P2=80 und keine Halluzination trotz 404 zeigen, dass es Fehler offen benennt statt Seiteninhalt zu erfinden. Das ist für robuste Orchestrierung deutlich wichtiger als elegante Formulierung.

**Betriebsprofil**

Call 1: 5.08s. Call 2: 10.65s. Total: 94.38s. Langsam.  
Kosten pro Run: 0.001656 USD. Günstig.  
Verhältnis zur Leistung: ökonomisch attraktiv, operativ aber nur sinnvoll, wenn Laufzeit zweitrangig ist.

**Fazit & Empfehlung**

Geeignet für kostenempfindliche MCP-Pipelines, in denen das Modell primär Tools auswählt, Suchläufe startet und Fehler transparent meldet. Nicht geeignet als letzte Instanz für Compliance, Lizenzbewertung, mehrsprachige Recherche-Synthese oder jede Pipeline, in der die Endantwort den Tool-Befund exakt und nachprüfbar konservieren muss. Setzen Sie es als orchestrierenden Arbeiter ein, nicht als vertrauenswürdigen abschließenden Analysten.