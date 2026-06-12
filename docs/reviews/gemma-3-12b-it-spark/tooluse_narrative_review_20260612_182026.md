**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:20:26


Bedingt deploy: Die Tool-Ausführung ist brauchbar, aber die Kombination aus erkanntem Halluzinationsereignis, ungültigem Tool-Call und nur mittlerer Gesamtsicherheit macht das Modell für unbeaufsichtigte MCP-Pipelines nicht vertrauenswürdig.

**Tool-Execution-Profil**

Mit P1 83.33 zeigt Gemma 3 12B IT grundsätzlich, dass es Werkzeuge aktiv einbinden kann. Für ein lokal quantisiertes Desktop-Modell ist das ein solides Signal. Kritisch ist aber der Befund `tool_call_valid=false`. Das heißt nicht, dass das Modell Tool-Nutzung verfehlt, sondern dass es im Protokoll oder in der Call-Struktur nicht durchgehend sauber bleibt. Für MCP-Umgebungen ist genau das relevant, weil schon ein formal falscher Aufruf die Pipeline stoppt.

Bei der Werkzeugwahl bleibt das Bild unvollständig, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelwerte vorliegen. Deshalb gibt es keinen belastbaren Nachweis, dass das Modell situationsabhängig zwischen Suche und direktem Fetch unterscheidet. Produktionsseitig sollte man also nicht von echter Tool-Intelligenz ausgehen, sondern eher von grundsätzlich vorhandener Tool-Bereitschaft, die durch enge Prompt- und Schema-Führung stabilisiert werden muss. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein reines Formatflattern und eher für einen einmalig nicht validen, aber abgeschlossenen Lauf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Mit P2 48.33 ist die Antwort klar: nur eingeschränkt. Das Modell kann Ergebnisse zusammenführen, verliert dabei aber zu viel Präzision, um extrahierte Fakten ohne Nachkontrolle in nachgelagerte Schritte zu geben. Für produktive Synthesis braucht man mehr Bindung an Quellinhalte.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist das stärkere Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell auch nur punktuell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Tool-Infrastruktur.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call prüft, hat das Modell keinen Seiteninhalt erfunden. Das ist produktionsfähig. Es kommuniziert Fehler also eher offen, statt stillschweigend Ersatzinhalt zu erzeugen. Dieser Befund entlastet das Modell deutlich, weil Ausfallpfade in realen MCP-Systemen häufiger auftreten als ideale Calls.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist nah genug am Durchschnitt, um den lokalen Betrieb nicht als starken Qualitätskompromiss erscheinen zu lassen.

**Fazit & Empfehlung**

Geeignet für lokale, datensensible Pipelines mit engem Guardrailing, festen Tool-Schemata und menschlicher oder programmatischer Ergebnisprüfung vor dem Commit. Nicht geeignet für autonome Recherche-, Compliance- oder Faktenpipelines, in denen Tool-Calls strikt valide sein müssen und Synthese ohne Kontrollschicht weiterverarbeitet wird. Wenn Sie dieses Modell einsetzen, dann als kostenarmes lokales Ausführungsmodell mit enger Führung, nicht als vertrauenswürdigen Agenten.