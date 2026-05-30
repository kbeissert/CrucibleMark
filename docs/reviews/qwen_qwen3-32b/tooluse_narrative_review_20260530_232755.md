**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:27:55


Bedingt deploy: Qwen 3 32B kann eine MCP-Toolkette formal bedienen, ist wegen erkannter Halluzinationen bei insgesamt nur moderater Gesamtleistung aber nicht als vertrauenswürdiger End-Synthesizer für produktive Faktenpipelines geeignet.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke. Mit P1 86.67 erzeugt das Modell valide Calls, bleibt protokollkonform und brauchte keinen Retry. Das spricht gegen ein Formatproblem und für grundsätzlich sauberes MCP-Verhalten.

Bei der Werkzeugwahl zeigt es echte Situationsanpassung, nicht nur ein starres Muster. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählt es das passende Werkzeug sicher. Das ist ein gutes Signal für dynamische Pipelines. Beim URL-Construction-Test, der die Ziel-URL aus Vorwissen ableiten und dann korrekt abrufen lässt, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Fetch-Flows. Insgesamt kann man ihm Tool-Zugriff technisch anvertrauen. Man kann ihm nicht ohne weiteres die inhaltliche Letztverantwortung anvertrauen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. P2 43.33 ist für ein Workstation-Generalist-Modell zu niedrig, und die Asset-Werte zeigen ein klares Muster: gute Auswahl und Ausführung der Tools, dann Verlust an Präzision bei der Zusammenführung. Besonders kritisch sind EU License Research und Multilingual Search & Synthesis mit jeweils nur 15 Punkten in der Verdichtung. Das Modell holt Informationen, verdichtet sie aber nicht belastbar genug für Compliance-, Policy- oder Recherche-Outputs.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, und das ist das eigentliche Sicherheitsproblem. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde Halluzination erkannt. Sobald ein Modell erfundene oder vorab gelernte Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Tool-Infrastruktur ihren Vertrauensanker.

**Fehlerresilienz**

Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Ersatzinhalt verlangt, halluziniert Qwen 3 32B trotz fehlgeschlagenem Tool-Call Seiteninhalt. Das ist produktionskritisch ohne Ausnahme. Ein brauchbares Produktionsmodell darf bei einem Abruffehler unvollständig sein. Es darf nicht so tun, als lägen Inhalte vor.

**Souveränitätsprofil**

Lokal betreibbar und sehr günstig: 0.002685 pro Run. Laufzeit 31.49s gesamt bei 1.97s und 2.14s Modell-Calls plus 1.14s MCP-Latenz. Damit wirtschaftlich attraktiv, aber leistungsmäßig 5.32 Punkte unter dem Fleet-Ø von 66.76.

**Fazit & Empfehlung**

Geeignet ist das Modell für lokale, souveräne Tool-Pipelines mit menschlicher Abnahme, etwa Vorrecherche, Such-Orchestrierung, URL-Ermittlung und nicht-kritische Automationsschritte. Nicht geeignet ist es als autonomer Antwortgenerator für Compliance, Regulatorik, Incident-Analyse oder jede Pipeline, in der Tool-Ergebnisse als belastbare Fakten ausgegeben werden. Wenn Sie Qwen 3 32B einsetzen, dann als Tool-Bediener unter strikter Output-Verifikation, nicht als vertrauenswürdige Syntheseinstanz.