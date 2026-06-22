**Deployment-Urteil**

> **Erstellt am:** 22.06.2026, 21:35:06


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit Halluzinationssignal und ungültigem Tool-Call nicht verlässlich genug für unbeaufsichtigte MCP-Pipelines ist.

**Tool-Execution-Profil**

Qwopus 3.6-27B-v2 MTP-Q8_0 zeigt echte Werkzeugwahl statt bloßem Standardmuster. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis search statt fetch gewählt wird, erreicht es P1 95. Das spricht für situative Tool-Intelligenz. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen und den anschließenden Fetch misst, ist es mit P1 80 noch brauchbar, aber nicht deterministisch genug für fragile Produktionspfade.

Der Hauptvorbehalt ist operativ: Tool-Call valide ist False. Das heißt nicht, dass das Modell keine Tools nutzen kann. Es heißt, dass es MCP-seitig nicht durchgehend protokollsauber bleibt. Für eine Pipeline mit hartem Schema und automatischer Weiterverarbeitung ist das ein reales Integrationsrisiko. Retry war nicht erforderlich. Das spricht eher gegen ein bloßes Formatproblem und eher für inkonsistente Call-Erzeugung unter Last oder in Teilfällen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 49.17 ist der schwache Teil dieses Profils. Besonders im Test HTTP Fetch & Extract, der strukturierte Fakten aus echtem Seiteninhalt verlangt, fällt die Verdichtung mit P2 15 klar ab. Das Modell ruft also häufig das richtige Werkzeug auf, überführt die Ergebnisse aber nicht stabil in präzise, belastbare Antworten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, halluziniert es nicht. Das ist ein positives Vertrauenssignal. Gleichzeitig ist global Halluzination erkannt: True. Das ist kein bloßer Qualitätsfehler, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, verliert die gesamte Tool-Infrastruktur ihren Prüfpfad.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call misst, verhält sich das Modell produktionsnah. P2 80 und keine Halluzination trotz 404 bedeuten: Es kommuniziert den Fehler statt Seiteninhalt zu erfinden. Das ist für reale Pipelines akzeptabel und deutlich wichtiger als sprachliche Eleganz.

**Souveränitätsprofil**

Lokal betreibbar und im Gesamtwert fleet-kompetitiv. Sovereignty Gap: n/a Punkte unter dem Fleet-Ø von 67.93. Operativ attraktiv für Umgebungen mit Datenhoheit, aber die Provenienz bleibt wegen der Community-Fine-Tuning-Kette ein Governance-Thema.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Assistenz- und Recherchepipelines mit menschlicher Abnahme, robuster Schema-Validierung und klarer Post-Processing-Kontrolle. Nicht geeignet für Compliance-, Vertrags-, Regulierungs- oder andere High-Trust-Pipelines, in denen Tool-Ergebnisse unverändert weiterverarbeitet werden. Wenn Sie es einsetzen, dann als toolfähigen Vorarbeiter, nicht als letzte Instanz.