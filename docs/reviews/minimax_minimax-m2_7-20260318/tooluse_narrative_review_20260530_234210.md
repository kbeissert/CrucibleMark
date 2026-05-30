**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:42:10


Nicht deploy für autonome MCP-Pipelines, weil die Tool-Calls nicht zuverlässig valide sind, ein Retry nötig war und das Gesamtbild mit 50.96 zu schwach für produktionsnahe Übergabe ausfällt.

**Tool-Execution-Profil**

MiniMax M2.7 zeigt kein stabiles Werkzeugurteil. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, fällt es mit P1 35 deutlich ab. Beim Test URL Construction & Fetch, der die Ableitung einer bekannten Ziel-URL und den anschließenden Fetch misst, erreicht es dagegen P1 80. Das spricht nicht für flexible Tool-Intelligenz, sondern eher für ein festes Muster: Wenn die URL implizit aus Weltwissen rekonstruierbar ist, arbeitet es brauchbar; wenn erst entschieden werden muss, welches Tool zur Informationsbeschaffung nötig ist, wird es unsicher. Dass der Tool-Call insgesamt als nicht valide markiert ist und ein Retry erforderlich war, wirkt hier eher wie ein Protokoll- oder Formatproblem unter Tool-Druck als wie reines Wissensdefizit. Für MCP-Orchestrierung ist das trotzdem kritisch, weil schon kleine Call-Formfehler Ketten brechen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher unzuverlässig. P2 43.33 ist für produktive Synthesis zu niedrig, und die Einzelergebnisse bestätigen das: EU License Research nur 20, Multilingual Search & Synthesis nur 20, Web Search & Tool Selection sogar 0. Das Modell extrahiert einfache Fetch-Inhalte solide, verdichtet aber mehrschrittige oder mehrsprachige Rechercheergebnisse nicht stabil genug für belastbare Ausgabe.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der genau dieses Verhalten auf aktuelle Web-Quellen prüft, zeigt keinen harten Halluzinationsbefund. Das ist der wichtigste Entlastungspunkt. Gleichzeitig ist der Content-Verification-State B1 bei P2 20 kein Vertrauenssignal, sondern eher ein Hinweis auf lockere Bindung an die Quelle. Es erfindet hier nicht offen, aber es hält sich auch nicht präzise genug an den recherchierten Befund.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlgeschlagenen Tool-Calls gegen erfundenen Ersatzinhalt abgrenzt, reagiert MiniMax M2.7 akzeptabel. P2 60 ist nicht stark, aber entscheidend ist: Es halluziniert trotz Fehler keinen Seiteninhalt. Das genügt für sichere Fehlerkommunikation, nicht jedoch für robuste Recovery-Strategien.

**Betriebsprofil**

Call 1: 3.92s. Call 2: 6.71s. MCP-Latenz: 0.20s. Total: 65.05s. Damit klar langsam. Kosten pro Run: 0.004800. Damit günstig. Im Verhältnis zur gezeigten Leistung ist es preislich attraktiv, operativ aber zu träge und zu schwankend.

**Fazit & Empfehlung**

Geeignet höchstens für assistive Pipelines mit enger Führung, festen URL-Mustern und nachgelagerter Validierung der Tool-Ausgaben. Nicht geeignet für autonome Rechercheketten, dynamische Tool-Auswahl, Compliance-nahe Web-Abfragen oder mehrsprachige Synthesis mit Entscheidungsanteil. Wenn Sie dem Modell Infrastruktur übergeben wollen, dann nur in stark eingehegten Pfaden mit Retry-Logik, Schema-Validierung und einem zweiten Prüfschritt für die Endantwort.