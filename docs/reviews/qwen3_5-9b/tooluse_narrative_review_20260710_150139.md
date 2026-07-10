**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:01:39


Bedingt deploy, weil das Modell keine Halluzination im Tool-Kontext gezeigt hat, aber keine verlässlich validen Tool-Calls produziert und für stabile Ausführung einen Retry braucht. Für produktive MCP-Pipelines reicht das nur dort, wo ein Orchestrator Fehler abfängt und Tool-Nutzung stark führt.

**Tool-Execution-Profil**

Das Modell kann Tools ausführen, aber nicht robust auswählen. Der zentrale Befund liegt im Kontrast zwischen Web Search & Tool Selection und URL Construction & Fetch: Wenn die Aufgabe offen ist und das Modell selbst erkennen muss, dass erst gesucht und nicht direkt gefetcht werden sollte, fällt es deutlich ab. Wenn die Ziel-URL aus Vorwissen ableitbar ist und der Pfad dann per Fetch abgearbeitet werden kann, arbeitet es wesentlich sauberer. Das spricht nicht für echte Werkzeugintelligenz, sondern eher für ein festes Muster: bekannte oder plausible URL bilden, dann abrufen.

Dass der Tool-Call nicht valide war und ein Retry nötig wurde, wirkt hier primär wie ein Protokoll- und Formattreueproblem, nicht wie ein kompletter Verständnisbruch. Trotzdem ist genau das in MCP-Umgebungen operativ relevant. Ein Modell, das den richtigen Arbeitsschritt nur nach Korrekturschleife sauber ausführt, erhöht Komplexität im Dispatcher und verschlechtert Planbarkeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. Die Verdichtungsqualität bleibt schwach, obwohl einzelne Fetch-Aufgaben ordentlich gelöst wurden. Das sieht man besonders bei EU License Research, wo die Recherche gelang, die Zusammenführung der gefundenen Informationen aber nur teilweise präzise blieb, sowie bei Multilingual Search & Synthesis, wo die grenzüberschreitende Recherche mit deutscher Ausgabe klar einbricht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt und der Verifikationsstatus ist sauber. Das ist ein wichtiges Vertrauenssignal: Das Modell erfindet nicht einfach aktuelle Compliance-Inhalte, auch wenn es sie nur mittelstark verdichtet.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlschlagenden Tool-Aufruf prüft, bleibt das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler und kommuniziert den Fehlschlag grundsätzlich sichtbar. Das ist produktionstauglicher als die Gesamtpunktzahl vermuten lässt, weil fehlende Daten nicht in erfundene Ergebnisse umgeschrieben werden.

**Souveränitätsprofil**

Voll lokal betreibbar, Apache-2.0-lizenziert und ohne Cloud-Abfluss. Gleichzeitig bleibt die Leistung 0.75 Punkte unter dem Fleet-Ø von 66.55. Das ist ein tragfähiges Souveränitätsprofil, aber kein Leistungsargument für ungeleitete Agentik.

**Fazit & Empfehlung**

Geeignet für lokal betriebene, souveräne Pipelines mit enger Tool-Führung, festen URL- oder Fetch-Mustern und externer Validierung der Tool-Calls. Nicht geeignet für dynamische Rechercheketten, autonome Tool-Wahl oder mehrsprachige Such-Szenarien, in denen das Modell selbst den nächsten Schritt bestimmen muss. Wer einen robusten Tool-Operator sucht, sollte es nur mit hartem Routing, Retry-Logik und Antwortprüfung einsetzen.