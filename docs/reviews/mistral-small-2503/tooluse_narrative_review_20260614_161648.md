**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:16:48


Bedingt deploy, weil die Tool-Ausführung oft brauchbar ist, das Modell aber mit erkannter Halluzination, ungültigem Tool-Call und notwendigem Retry keine vertrauenswürdige Standardbesetzung für autonome MCP-Pipelines ist.

**Tool-Execution-Profil**

Mistral Small 3.1 kann Tools operativ nutzen, aber nicht durchgängig protokolltreu. Der P1-Wert von 66.67 passt zum Muster in den Assets: Beim HTTP Fetch & Extract arbeitet es sauber, und beim URL-Construction-Test, der die korrekte Ziel-URL aus Modellwissen verlangt, ist die Ausführung mit P1 80 klar brauchbar. Das spricht für solide Follow-through-Fähigkeit, sobald der Pfad im Wesentlichen feststeht.

Die Schwäche liegt in der Werkzeugwahl. Beim Web-Search-&-Tool-Selection-Test, der ohne expliziten Hinweis zwischen web_search und fetch unterscheiden lässt, fällt das Modell mit P1 35 deutlich ab. Es zeigt damit keine verlässliche Tool-Intelligenz, sondern eher ein musterhaftes Fortsetzen naheliegender Aufrufe. Dass ein Retry nötig war und der Tool-Call nicht valide war, wirkt hier eher wie ein Verständnis- und Orchestrierungsproblem als ein reines Formatproblem: Das Modell scheitert nicht nur an Syntax, sondern an der korrekten Einordnung, welches Werkzeug überhaupt gebraucht wird.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 45.83 ist für produktive Synthesis schwach, obwohl einzelne Aufgaben wie HTTP Fetch & Extract mit P2 100 zeigen, dass präzise Verdichtung aus klaren Quellen prinzipiell möglich ist. Sobald Recherche, Mehrsprachigkeit oder Auswahlunsicherheit dazukommen, fällt die Antwortqualität deutlich ab.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im EU License Research, dem Honeypot für aktuelle Lizenzrestriktionen aus Web-Quellen, erreicht es nur P2 15 bei erkanntem Halluzinationsbefund. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Tool-Pipeline ihren Verifikationswert.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call prüft, halluziniert das Modell keinen Seiteninhalt. Das ist der richtige Produktionsreflex. Die P2 von 40 zeigt jedoch, dass die Fehlerkommunikation nicht besonders klar oder hilfreich ist. Für überwachte Workflows ist das akzeptabel. Für stark autonome Ketten bleibt es zu unpräzise.

**Souveränitätsprofil**

Lokal gut einsetzbar: offene Gewichte, Apache-2.0-Lizenz, Workstation-tauglich. Gleichzeitig liegt es  -1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist nahe am Durchschnitt, aber kein Beleg für besondere Fleet-Stärke.

**Fazit & Empfehlung**

Geeignet für kosten- und souveränitätssensible Pipelines mit enger Tool-Führung, festen URL- oder Fetch-Mustern und menschlicher Abnahme der Ergebnisse. Nicht geeignet für Compliance-, Research- oder Agenten-Workflows, in denen das Modell selbstständig das richtige Tool wählen und strikt an Tool-Belege gebunden bleiben muss. Wenn Sie es einsetzen, dann mit vorgeschalteter Tool-Wahl, hartem Output-Schema und nachgelagerter Quellvalidierung.