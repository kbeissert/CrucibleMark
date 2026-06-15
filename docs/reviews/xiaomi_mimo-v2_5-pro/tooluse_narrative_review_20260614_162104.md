**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:21:04


Bedingt deploy, weil die Tool-Ausführung stark wirkt, das Modell aber mit erkannter Halluzination und ungültigem Tool-Call kein hinreichend verlässliches Fundament für unbeaufsichtigte MCP-Pipelines bietet.

**Tool-Execution-Profil**

Xiaomi MiMo V2.5 Pro zeigt grundsätzlich brauchbare Tool-Fähigkeit. Der P1-Wert von 90.00 spricht dafür, dass es Werkzeuge aktiv einbezieht und Aufgaben nicht reflexhaft aus dem Parametergedächtnis beantwortet. Für den Produktionseinsatz zählt aber nicht nur die Nutzungsbereitschaft, sondern Protokolltreue. Genau dort liegt der Bruch: Der Tool-Call war nicht valide, obwohl kein Retry nötig war. Das deutet weniger auf ein vorübergehendes Formatproblem als auf unzuverlässige Call-Erzeugung im ersten Versuch.

Zu den Tests Web Search & Tool Selection und URL Construction & Fetch liegen keine Einzelwerte vor. Deshalb lässt sich nicht sauber trennen, ob die hohe P1-Leistung aus guter Werkzeugwahl oder aus starker Ausführung nach korrektem Prompting stammt. Für Architekten ist das relevant: Aktuell gibt es kein belastbares Signal, dass das Modell in dynamischen Pipelines selbstständig zwischen Suche und direktem Fetch unterscheidet, statt einem festen Muster zu folgen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. Der P2-Wert von 44.17 ist für ein Frontier-Reasoning-Modell zu niedrig, wenn aus mehreren Tool-Rückgaben belastbare, knappe und faktentreue Antworten entstehen sollen. Das Modell kann also offenbar Daten beschaffen, verliert aber beim Zusammenführen und Verdichten an Präzision. Genau das ist in produktiven Tool-Ketten oft der eigentliche Engpass.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist positiv. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Pipeline ausgibt, beschädigt es die Vertrauenskette der gesamten Infrastruktur, unabhängig von seiner allgemeinen Antwortqualität.

**Fehlerresilienz**

Im 404-Test Tool Failure Handling, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, halluzinierte das Modell keinen Seiteninhalt. Das ist produktionsreif. Es signalisiert, dass MiMo V2.5 Pro bei offensichtlichem Werkzeugfehler nicht automatisch Ersatzfakten konstruiert. Für robuste Orchestrierung ist das ein klarer Pluspunkt.

**Betriebsprofil**

Total: 135.30s. Langsam.  
MCP-Latenz: 0.75s. Tool-Schicht ist nicht der Engpass.  
Modell-Calls: 5.92s und 15.88s. Der Rest der Laufzeit spricht für zähe End-to-End-Orchestrierung.  
Kosten/Run: local. Günstig betreibbar, aber die Zeitkosten sind im Verhältnis zur nur moderaten Gesamtleistung hoch.

**Fazit & Empfehlung**

Geeignet für überwachte Research- und Engineering-Pipelines, in denen ein nachgelagerter Validator Tool-Calls und Endsynthese prüft. Nicht geeignet für autonome Compliance-, URL-sensitive oder kundennahe Antwortsysteme, in denen jeder Tool-Call formal korrekt und jede Zusammenfassung strikt quellentreu sein muss. Wer MiMo V2.5 Pro einsetzt, sollte es als starken Beschaffer unter Kontrolle behandeln, nicht als vertrauenswürdigen letzten Entscheider.