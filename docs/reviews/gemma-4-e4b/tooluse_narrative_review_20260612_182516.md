**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:25:16


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination im Lauf erkannt wurde, die Synthesetreue aber nur knapp produktionsfest wirkt. Das Modell kann man an eine Tool-Infrastruktur hängen, aber nicht als letzte Instanz für verdichtete Sachausgaben.

**Tool-Execution-Profil**

Das stärkste Signal ist die Ausführungsebene. Gemma 4 E4B produziert valide Tool-Calls, bleibt MCP-konform und brauchte keinen Retry. Das spricht nicht für bloßes Format-Glück, sondern für ein stabiles Verständnis der Aufrufstruktur.

Bei Web Search & Tool Selection, also dem Test ob ohne expliziten Hinweis das Such- statt das Fetch-Werkzeug gewählt wird, handelt das Modell sauber und zeigt echte Werkzeugwahl statt starrem Standardpfad. Das Ergebnis beim URL-Construction-Test ist schwächer: Es kann Ziel-URLs oft aus Vorwissen ableiten und den Fetch ausführen, aber nicht mit der Präzision, die man für strikt deterministische Pipelines erwarten würde. Das Muster ist klar: gute Auswahl des Werkzeugtyps, etwas weniger Verlässlichkeit bei der konkreten Adresskonstruktion.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung zeigt, dass das Modell gefundene Inhalte meist brauchbar zusammenzieht, aber bei Präzision, Priorisierung und faktischer Verdichtung sichtbar Reserven hat. Das sieht man besonders bei EU License Research, wo die Recherche korrekt angestoßen wird, die Endzusammenfassung aber zu grob bleibt. Für produktive Retrieval-Pipelines reicht das für Arbeitsnotizen, nicht für freizugebende Fachantworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal besser als die Verdichtungsqualität. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das Modell bleibt also grundsätzlich an der Tool-Spur, auch wenn es die Ergebnisse anschließend nicht scharf genug verdichtet.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Call prüft, erfindet das Modell keinen Ersatzinhalt. Das ist der entscheidende Punkt. Die Fehlerkommunikation ist akzeptabel für Produktion, auch wenn die Antwort nicht besonders stark weiterhilft. Für orchestrierte Systeme ist diese Form der Ehrlichkeit wichtiger als sprachliche Eleganz.

**Souveränitätsprofil**

Lokal betreibbar und damit für sensible Umgebungen praktisch. Die Gesamtleistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist nah genug am Flottenniveau, um lokale Souveränität ohne deutlichen Qualitätsbruch zu rechtfertigen.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen Tool-Aufrufe robust sein müssen und die Endantwort noch durch Policy, Validierung oder einen stärkeren Reviewer läuft. Gut für Recherche-Anstoß, Such-/Fetch-Orchestrierung und transparente Fehlerpfade. Nicht die richtige Wahl für Compliance-nahe Freitextausgaben, präzise Entscheidungszusammenfassungen oder Pipelines, in denen die erste Modellantwort bereits veröffentlichungsreif sein muss.