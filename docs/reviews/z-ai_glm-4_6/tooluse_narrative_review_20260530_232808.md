**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:28:08


Bedingt deploy, weil GLM 4.6 valide Tool-Calls produziert und nicht halluziniert, aber die Synthesetreue für produktionsnahe Tool-Pipelines zu ungleichmäßig bleibt. Der Combined-Score von 75.92 ist tragfähig, das Vertrauensprofil ist besser als die Verdichtungsqualität.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Modells. Es wählt Werkzeuge nicht nur schematisch, sondern meist passend zur Informationslage: Im Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis statt fetch eine Websuche nötig ist, arbeitet es fehlerfrei. Das spricht für echte Werkzeugwahl statt starrem Muster. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar, aber nicht präzise genug für deterministische Pipelines; hier ist die Ausführung solide, aber nicht vollständig robust. Insgesamt ist das MCP-Verhalten protokollkonform, die Calls sind valide. Dass ein Retry nötig war, wirkt eher wie ein Ausführungs- oder Formatproblem im Ablauf als wie ein Missverständnis der Aufgabe, weil die Tool-Wahl selbst konsistent bleibt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ausreichend. P2 liegt mit 63.33 deutlich unter der Ausführungskompetenz. Das Muster in den Assets ist klar: strukturierte Extraktion aus Fetch-Content gelingt noch ordentlich, aber bei Recherche mit Verdichtung fällt das Modell ab, besonders in Multilingual Search & Synthesis. Für Architekturen, in denen das Modell nach dem Abruf belastbare Kurzfassungen oder Entscheidungsvorlagen liefern soll, ist das der Hauptvorbehalt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist GLM 4.6 deutlich vertrauenswürdiger. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert es nicht. Der Content-Verification-State A ist für Compliance-nahe Tool-Pipelines ein starkes Signal: Das Modell verlässt die Datenbasis nicht leichtfertig, auch wenn es sie nicht immer gut genug verdichtet.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich GLM 4.6 produktionstauglich. Im 404-Test, der misst, ob ein fehlgeschlagener Aufruf transparent benannt oder mit erfundenem Inhalt überspielt wird, kommuniziert es den Fehler sauber und halluziniert keinen Seiteninhalt. Das ist akzeptabel für produktive Pipelines, weil der Fehler sichtbar bleibt und die Orchestrierung korrekt reagieren kann.

**Betriebsprofil**

Call 1: 16.36s. Call 2: 33.40s. MCP-Latenz: 0.93s. Total: 304.16s. Langsam. Kosten pro Run: 0.005716. Günstig. Im Verhältnis zur Leistung ist es eher kostenattraktiv als latenzstark.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen zuverlässige Tool-Nutzung, saubere Fehleroffenlegung und kontrolliertes Grounding wichtiger sind als hochwertige Endverdichtung. Das passt zu Recherchevorstufen, Assistenz-Orchestrierung und menschlich nachgelagerter Prüfung. Nicht die erste Wahl für vollautomatische Compliance-, Policy- oder Executive-Summary-Pipelines, in denen die Antwort nach dem Tool-Aufruf bereits die finale, präzise Synthese sein muss.