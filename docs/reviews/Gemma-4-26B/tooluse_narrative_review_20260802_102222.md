**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:22:22


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesequalität mit Combined 72.62 nur dann tragfähig ist, wenn nachgelagerte Validierung oder enge Antwortformate die Verdichtung absichern. Halluzination wurde nicht erkannt, aber der Tool-Call war nicht durchgehend valide.

**Tool-Execution-Profil**

Gemma 4 26B-A4B Instruct zeigt echte Werkzeugwahl statt bloßer Schablonen-Nutzung. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch erkannt wird, liegt es mit P1 95 klar auf produktionsfähigem Niveau. Das spricht für brauchbare Situationsdiagnose in dynamischen MCP-Pipelines. Beim Test URL Construction & Fetch, der die präzise Ableitung einer Ziel-URL aus Eigenwissen misst, fällt es auf P1 75 zurück. Das ist kein Auswahlproblem, sondern ein Präzisionsproblem bei der konkreten Ausführung. Es weiß oft, welches Werkzeug gebraucht wird, liefert aber nicht immer den deterministisch korrekten Aufruf. Dass tool_call_valid insgesamt false ist, bleibt der zentrale operative Vorbehalt.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt zuverlässig. P2 56.67 ist für produktive Retrieval- oder Compliance-Strecken zu niedrig, wenn das Modell längere Web-Inhalte eigenständig zusammenziehen soll. Die Schwäche zeigt sich besonders bei EU License Research mit P2 40, also genau dort, wo aktuelle Restriktionen aus Quellen sauber in Entscheidungssprache überführt werden müssen. Besser wirkt es bei Web Search & Tool Selection mit P2 80, schwächer bei den meisten Fetch-nahen Aufgaben mit P2 60.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, wurde keine Halluzination erkannt. Das ist das wichtige Vertrauenssignal. Es verdichtet schlecht, aber es erfindet hier keine regulatorischen Fakten. Für Produktionsbetrieb ist das deutlich besser als ein sprachlich glatter, aber faktenunsicherer Synthesizer.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der Transparenz bei scheiternden Tool-Calls gegen erfundenen Ersatzinhalt misst, reagiert das Modell akzeptabel. P2 60 ist nicht elegant, aber entscheidend ist: Es halluziniert trotz 404 keinen Seiteninhalt. Damit bleibt die Fehleroberfläche sichtbar. Für produktive Pipelines ist das brauchbar, weil Orchestrierung und Retry-Logik auf explizite Fehlerinformationen aufsetzen können.

**Souveränitätsprofil**

Voll lokal betreibbar unter Apache-2.0 und damit für souveräne Deployments praktisch gut geeignet. Leistungsseitig liegt es mit einem Sovereignty Gap von -1.22 Punkten unter dem Fleet-Ø von 66.87 also nahezu auf Fleet-Niveau, ohne Cloud-Zwang.

**Fazit & Empfehlung**

Geeignet für lokale, MCP-gestützte Pipelines mit klaren Tool-Verträgen, knappen Antwortformaten und externer Ergebnisprüfung. Besonders sinnvoll ist es für Such-, Routing- und Vorverarbeitungsstufen, in denen Werkzeugwahl wichtiger ist als feinpolierte Endsynthese. Nicht die erste Wahl für Compliance-Briefings, entscheidungsreife Research-Memos oder andere Endpunkte, an denen die Modellantwort selbst den finalen Fachtext bildet.