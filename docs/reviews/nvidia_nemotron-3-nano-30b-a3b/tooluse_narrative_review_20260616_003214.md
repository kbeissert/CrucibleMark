**Deployment-Urteil**

> **Erstellt am:** 16.06.2026, 00:32:14


Bedingt deploy: Die Tool-Ausführung ist oft brauchbar, aber der ungültige Tool-Call und die erkannte Halluzination schließen einen unkontrollierten Einsatz in produktiven MCP-Pipelines aus.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt reinem Musterfolgen. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung zuverlässig. Das spricht für brauchbare Tool-Intelligenz in dynamischen Retrieval-Schritten. Auch beim Test URL Construction & Fetch, der die eigenständige Ableitung der Ziel-URL misst, arbeitet es überwiegend korrekt, aber nicht deterministisch genug für harte Produktionspfade.

Der Hauptvorbehalt ist nicht die Auswahl, sondern die Protokolltreue. P1 von 82.50 ist solide, aber tool_call_valid=false ist ein klarer Betriebsbefund. Ein Modell darf das richtige Tool nicht nur konzeptuell kennen, sondern muss den Call auch formal gültig erzeugen. Da kein Retry erforderlich war, liegt das Problem eher in der Erstgenauigkeit als in einem behebbaren Formatdrift unter Wiederholung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 51.67 zeigt, dass das Modell gefundene Inhalte oft nicht präzise genug in belastbare Ergebnistexte überführt. Das sieht man besonders bei Multilingual Search & Synthesis, wo die sprachübergreifende Recherche in der deutschen Zusammenfassung stark an Genauigkeit verliert. Dagegen ist URL Construction & Fetch mit P2 100 ein Ausreißer nach oben, also eher ein enger Erfolgsfall als ein breites Muster.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Modell auf dem beschafften Material. Das ist ein gutes Vertrauenssignal. Gleichzeitig gilt: hallucination_flag=true ist ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-Kette ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der transparente Reaktion auf einen fehlschlagenden Abruf misst, bleibt das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz 404-Fehler und kommuniziert den Fehlschlag erkennbar. Das ist produktionsfähig. Die niedrige Ausführungsbewertung in diesem Asset zeigt aber, dass der Umgang mit Fehlerpfaden operativ unsauber bleibt.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Mit 65.96 Combined liegt es 1.88 Punkte unter dem Fleet-Ø von 67.84. Das ist nah genug am Durchschnitt, um lokale Nutzung zu rechtfertigen, aber nicht stark genug, um Qualitätsrisiken durch Souveränität allein zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische Pipelines mit Mensch-im-Loop, klaren Guardrails und nachgelagerter Validierung von Tool-Outputs. Sinnvoll für Recherche-Anstoß, URL-Ableitung und einfache Fetch-Workflows. Nicht geeignet für Compliance, autonome Agentenpfade oder jede Pipeline, in der formale Tool-Korrektheit und synthesegetreue Verdichtung ohne Gegenkontrolle zwingend sind.