**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:07:14


Bedingt deploy, weil die Tool-Ausführung stark wirkt und valide MCP-Calls liefert, das Modell aber mit erkannter Halluzination und nur mäßiger Synthesetreue kein uneingeschränkt vertrauenswürdiger Pipeline-Endpunkt ist.

**Tool-Execution-Profil**

Das stärkste Signal ist P1 90.00. Das Modell produziert valide Tool-Calls, bleibt protokollkonform und brauchte keinen Retry. Das spricht gegen ein Formatproblem und für grundsätzlich belastbare Integration in eine MCP-gestützte Laufzeit. Für Product Engineers ist das wichtig: Die Übergabe an Tools selbst ist nicht die primäre Schwachstelle.

Was fehlt, sind die entscheidenden Feindaten zur Werkzeugwahl. Für Web Search & Tool Selection, also den Test auf intelligente Wahl zwischen Suche und direktem Abruf, liegen keine Ergebnisse vor. Ebenso fehlen Daten aus URL Construction & Fetch, also dem Test auf präzise URL-Ableitung vor einem Fetch. Deshalb lässt sich nicht sicher sagen, ob ministral-3:14b Werkzeugwahl aktiv begründet oder nur ein stabiles Standardmuster abfährt. Die technische Anbindung wirkt robust. Die strategische Tool-Intelligenz bleibt offen.

**Synthesetreue**

Wie gut verdichtet es? Eher nur ausreichend. P2 50.83 ist für ein Generalist-Modell dieser Desktop-Klasse zu niedrig, wenn die Pipeline auf verlässliche Verdichtung von Tool-Ergebnissen angewiesen ist. Das Modell kann Informationen offenbar einsammeln und formal korrekt weiterreichen, aber die Umwandlung in belastbare, knappe und faktengebundene Antworten ist kein klarer Produktionsvorteil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu gibt es für EU License Research keine Detaildaten, aber der gesetzte Halluzinationsbefund ist bereits kritisch genug. In einer Tool-Pipeline ist das kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene Fakten als angebliche Tool-Ergebnisse ausgibt, verliert die gesamte Infrastruktur ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Für Tool Failure Handling, also den 404-Test auf transparenten Umgang mit fehlgeschlagenen Aufrufen, liegen keine Daten vor. Deshalb bleibt unbeantwortet, ob das Modell bei externen Fehlern sauber stoppt oder Ersatzinhalt erzeugt. Gerade wegen des Halluzinationssignals ist diese Lücke relevant. Ohne belegte Fehlertransparenz sollte man es nicht in Pfade setzen, in denen fehlende oder defekte Quellen häufig auftreten.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist nah genug am Flottenschnitt, um lokale Nutzung zu rechtfertigen, aber nicht stark genug, um die Vertrauensrisiken zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Tool-Pipelines mit menschlicher Freigabe, klaren Guardrails und begrenztem Schadensradius, etwa interne Recherchevorstufen, strukturierte Datensammlung oder Voraggregation vor einem zweiten Prüfschritt. Nicht geeignet für Compliance-, Support- oder Entscheidungs-Pipelines, in denen die Antwort als verifizierte Wiedergabe von Tool-Ergebnissen gelten muss. Wenn Sie es einsetzen, dann als ausführendes Zwischenmodell, nicht als letzte vertrauensgebende Instanz.