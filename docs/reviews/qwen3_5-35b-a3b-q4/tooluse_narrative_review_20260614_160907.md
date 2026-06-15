**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:09:07


Bedingt deploy, weil die Tool-Ausführung stark ist und die Calls valide bleiben, aber die Synthesequalität mit Combined 71.75 nur dann tragfähig ist, wenn nachgelagerte Validierung erfundene oder unsauber verdichtete Aussagen abfängt.

**Tool-Execution-Profil**

Dieses Modell kann man einer MCP-Tool-Infrastruktur grundsätzlich anvertrauen. Die Tool-Calls waren valide, ein Retry war nicht nötig, und die Ausführung auf P1-Niveau ist mit 90 klar produktionsfähig. Entscheidend ist die Werkzeugwahl: Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis search statt fetch gewählt wird, erkennt das Modell den Bedarf korrekt und erreicht volle Ausführungssicherheit. Das spricht gegen bloßes Schema-Following und für echte Tool-Selektion.

Weniger sauber ist die Präzision beim URL-Construction-Test, der die eigenständige Ableitung der Ziel-URL misst. Dort funktioniert fetch, aber nicht deterministisch genug für fragile Pipelines. Das Muster ist klar: Das Modell ist stark, wenn es Suchraum erkunden und dann ein Tool ansetzen soll. Es ist schwächer, wenn es exakte Zieladressen aus internem Wissen konstruieren muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 liegt bei 55.83, und die Schwächen sind deutlich: HTTP Fetch & Extract fällt bei der strukturierten Extraktion realer Web-Inhalte auf 15, EU License Research und Multilingual Search & Synthesis bleiben ebenfalls bei 40. Das Modell holt die Daten oft korrekt, verdichtet sie aber nicht präzise genug für Compliance-, Fakten- oder Dokumentationspfade.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diese Trennung prüft, bleibt es formal auf dem Tool-Pfad. Halluzination wurde dort nicht erkannt. Das ist das positive Signal. Gleichzeitig ist global Halluzination erkannt: true gesetzt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als angebliche Tool-Ergebnisse ausgeben kann, wird die Tool-Kette als Vertrauensanker beschädigt.

**Fehlerresilienz**

Hier verhält sich das Modell produktionsgerecht. Im Tool Failure Handling (404)-Test, der transparenten Umgang mit fehlschlagenden Tool-Calls prüft, kommuniziert es den Fehler offen und halluziniert keinen Ersatzinhalt. P2=100 ist in diesem Fall wichtiger als Stilfragen. Für reale MCP-Pipelines ist das ein hartes positives Signal.

**Souveränitätsprofil**

Lokal betreibbar und fleet-kompetent genug für souveräne Setups. Der Sovereignty Gap liegt bei -1.37 Punkten unter dem Fleet-Ø von 67.84. Das ist nah genug am Flottenschnitt, um den lokalen Betrieb nicht als klare Qualitätsstrafe werten zu müssen.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Tool-Pipelines mit Search, Fetch, Fehlerbehandlung und menschlich oder regelbasiert abgesicherter Endausgabe. Nicht geeignet als unbeaufsichtigter End-Synthesizer in Compliance-, Policy-, Research- oder Extraktionsstrecken, in denen jede verdichtete Aussage als belastbarer Fakt weitergereicht wird. Wer es einsetzt, sollte das Modell als Tool-Operator nutzen, nicht als letzte Instanz für Wahrheit.