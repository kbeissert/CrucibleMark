**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:07:24


Bedingt deploy, weil die Tool-Ausführung stark ist, aber Halluzination erkannt wurde und die Syntheseleistung mit Combined 63.75 nur für eng geführte Pipelines tragfähig wirkt.

**Tool-Execution-Profil**

ministral-3:8b liefert ein grundsätzlich belastbares Tool-Execution-Profil. Der Tool-Call war valide, und der P1-Wert von 89.17 spricht dafür, dass das Modell MCP-konforme Aufrufe erzeugen kann und an der Schnittstelle nicht der primäre Ausfallpunkt ist. Für eine produktive Tool-Pipeline ist das ein relevantes Plus.

Die Einordnung bleibt aber unvollständig, weil weder für Web Search & Tool Selection noch für URL Construction & Fetch konkrete Testdaten vorliegen. Damit lässt sich nicht belegen, ob das Modell Werkzeuge situativ auswählt oder nur ein stabiles Standardmuster abspult. Für Architekturen mit dynamischer Tool-Routing-Logik ist das eine echte Lücke.

Dass ein Retry erforderlich war, wirkt hier eher wie ein Robustheitsproblem im Ablauf als ein grundsätzlicher Protokollbruch. Da der finale Tool-Call valide war, spricht das eher für Format- oder Sequenzinstabilität als für fehlendes Tool-Verständnis. In produktiven Ketten erhöht das trotzdem Orchestrierungsaufwand und Laufzeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Der P2-Wert von 40.00 ist für ein Generalist-Modell im Produktionseinsatz zu niedrig, wenn aus mehreren Tool-Antworten verlässliche, knappe und präzise Endausgaben entstehen sollen. Das Modell kann offenbar abrufen, aber nicht konsistent stark zusammenführen. Genau dort entstehen in realen Pipelines die Folgekosten: falsche Priorisierung, weiche Formulierungen und unklare Faktentrennung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu fehlen für EU License Research die Detaildaten, aber der gesetzte Halluzinationsbefund ist bereits ausreichend kritisch. Das ist kein Schönheitsfehler, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene Fakten als Ergebnis einer Tool-gestützten Recherche ausgibt, verliert die gesamte Pipeline ihre Vertrauensbasis.

**Fehlerresilienz**

Für Tool Failure Handling beim 404-Test liegen keine Detaildaten vor. Deshalb ist die Robustheit gegen fehlschlagende Aufrufe nicht verifiziert. Im Produktionsmaßstab ist das relevant, weil gerade an Fehlerpfaden sichtbar wird, ob ein Modell sauber zwischen „keine Daten“ und „vermuteter Inhalt“ trennt. Wegen des Halluzinationssignals sollte man hier konservativ urteilen und explizite Guardrails für Fehlerfälle vorsehen.

**Souveränitätsprofil**

Lokal betreibbar und damit souveränitätsstark. Gleichzeitig liegt das Modell 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist nah genug am Durchschnitt, um für lokale Umgebungen interessant zu bleiben, aber nicht stark genug, um Qualitätsrisiken durch den On-Prem-Vorteil allein zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkontrollierte Pipelines mit enger Aufgabenführung, festem Tool-Schema und nachgelagerter Validierung. Nicht geeignet für Compliance-nahe Recherche, autonome Tool-Auswahl oder Workflows, in denen die Endantwort unmittelbar als verlässliche Darstellung von Tool-Ergebnissen gilt. Wenn Sie es einsetzen, dann als ausführendes Edge-Modell unter strikter Aufsicht, nicht als vertrauenswürdige Syntheseinstanz.