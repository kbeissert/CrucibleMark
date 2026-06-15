**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:08:50


Bedingt deploy, weil die Tool-Ausführung stark und protokolltreu ist, die Synthesequalität aber zu oft unpräzise bleibt und eine erkannte Halluzination das Vertrauen in inhaltlich kritischen Pipelines begrenzt.

**Tool-Execution-Profil**

Gemma 3 12B IT verhält sich auf der MCP-Ebene zuverlässig. Tool-Calls waren valide, ein Retry war nicht nötig. Das spricht gegen ein Formatproblem und für stabile Protokollkonformität im laufenden Betrieb. Beim Web Search & Tool Selection-Test, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erreicht das Modell volle Ausführungssicherheit. Das ist ein starkes Signal für echte Werkzeugwahl statt bloßem Schema-Following.

Weniger robust ist es beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableiten und dann fetch ausführen lässt. Hier reicht es nur zu brauchbarer, nicht deterministischer Präzision. Das Muster ist klar: Wenn die Werkzeugentscheidung offen ist, wählt das Modell oft richtig. Wenn es selbst die exakte Zieladresse konstruieren muss, steigt das Fehlerrisiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt verlässlich. Der P2-Wert von 49.17 passt zum Asset-Bild: starke Tool-Nutzung, aber schwache Extraktion im HTTP Fetch & Extract-Test, der präzise Jahreszahlen, Namen und Versionen aus realem Content verlangt. Das Modell findet Quellen, verdichtet sie aber nicht konsistent in belastbare, strukturtreue Antworten. Für produktive Pipelines ist das kein Schönheitsfehler, sondern ein Übergaberisiko an nachgelagerte Systeme.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im EU License Research-Honeypot, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingswissen erzwingen soll, bleibt es grundsätzlich auf dem Tool-Pfad und halluziniert nicht. Das ist positiv. Gleichzeitig ist der Verifikationszustand B2 bei P2=40 zu schwach für Compliance-nahe Nutzung. Zusätzlich gilt: Die global erkannte Halluzination ist als Sicherheitsrisiko zu werten. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgeben kann, verliert die Tool-Infrastruktur ihre Vertrauensbasis.

**Fehlerresilienz**

Beim Tool Failure Handling (404)-Test reagiert das Modell akzeptabel. Es kommuniziert den Fehlschlag transparent und erfindet keinen Seiteninhalt. Das ist für Produktion der Mindeststandard und hier erfüllt. Die P2-Qualität von 60 zeigt, dass die Fehlerkommunikation nicht elegant, aber ausreichend kontrolliert ist.

**Souveränitätsprofil**

Lokal betreibbar und praktisch souverän einsetzbar. Mit einem Sovereignty Gap von -1.37 Punkten liegt es nur 1.37 Punkte unter dem Fleet-Ø von 67.84. Für eine lokale GGUF-Ausführung ist das konkurrenzfähig.

**Fazit & Empfehlung**

Geeignet für lokale, datensensible MCP-Pipelines mit klaren Guardrails, in denen Tool-Aufruf, Suche, einfache Recherche und transparente Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Nicht geeignet als unbeaufsichtigte letzte Instanz für Compliance, faktenkritische Extraktion oder Pipelines, in denen die Antwort direkt in Berichte, Tickets oder Entscheidungen einfließt. Empfehlung: als Tool-Orchestrator oder Vorstufe einsetzen, nicht als finale Synthese-Schicht.