**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:47:52


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, aber die Synthese im produktionsrelevanten Mittelteil zu oft an Präzision verliert. Mit validen Tool-Calls, keiner erkannten Halluzination und einem guten Gesamtscore ist die Basis brauchbar, das Vertrauen in die Endverdichtung aber nicht durchgehend stark genug.

**Tool-Execution-Profil**

GPT-5.4 Mini zeigt ein belastbares Tool-Profil. Die Aufrufe sind valide, MCP-konform und die Werkzeugwahl wirkt nicht rein schematisch. Das sieht man daran, dass es beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden soll, die richtige Entscheidung sicher trifft. Beim Test URL Construction & Fetch, der korrekte Ziel-URLs aus Modellwissen ableitet, bleibt es dagegen nur ordentlich. Das spricht für echte Tool-Intelligenz bei der Wahl des Werkzeugs, aber nicht für durchgehend präzise Vorarbeit beim Bau deterministischer Fetch-Ziele.

Dass ein Retry nötig war, wirkt hier eher wie ein Ausführungs- oder Formatproblem als wie ein Verständnisfehler. Die hohe P1-Leistung über alle Aufgaben stützt diese Einordnung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht robust genug für Pipelines, in denen die Antwort selbst als verlässliches Endartefakt zählt. Die Spannweite ist groß: HTTP Fetch & Extract verdichtet sehr stark, während EU License Research und URL Construction & Fetch klar an Präzision verlieren. Das Muster ist deutlich: Wenn die Werkzeuge gute Rohdaten liefern, kann das Modell brauchbar zusammenziehen. Sobald Kontextgewichtung und vorsichtige Verdichtung wichtiger werden, sinkt die Qualität sichtbar.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, halluziniert es nicht. Das ist der zentrale Vertrauensanker. Der sehr schwache P2-Wert und der Verifikationsstatus B2 zeigen aber, dass es zwar keine freien Fakten erfindet, den abgerufenen Inhalt jedoch nicht sicher genug in eine belastbare Compliance-Antwort übersetzt.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call prüft, erfindet GPT-5.4 Mini keinen Seiteninhalt. Das ist produktionsfähig. Die Fehlerkommunikation ist nicht vorbildlich knapp und klar, aber ausreichend ehrlich. Für reale Tool-Pipelines ist das akzeptabel, weil die Infrastruktur dadurch nicht mit erfundenem Ersatzwissen kontaminiert wird.

**Betriebsprofil**

Call 1: 2.50s. MCP-Latenz: 1.35s. Call 2: 3.28s. Gesamt: 42.81s. Kosten pro Run: 0.018911 USD. Im Verhältnis zur Leistung: nicht schnell, aber günstig genug für breite Vorverarbeitung und assistierte Recherche.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und Extraktionspipelines, in denen Tools die Wahrheit liefern und nachgelagerte Systeme oder Menschen die Endfreigabe übernehmen. Nicht die erste Wahl für Compliance-, Policy- oder entscheidungsnahe Workflows, in denen die verdichtete Antwort selbst belastbar sein muss. Deploy als Tool-Operator und Vorverdichter. Nicht als autonomes Schlussmodul.