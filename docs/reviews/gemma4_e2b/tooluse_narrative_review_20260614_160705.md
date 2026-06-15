**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:07:05


Bedingt deploy, weil die Tool-Ausführung stark ist und valide MCP-Calls erzeugt, das Modell aber mit erkannter Halluzination und schwacher Synthesetreue kein verlässlicher Endpunkt für faktenkritische Pipelines ist.

**Tool-Execution-Profil**

Beim eigentlichen Tool-Handling hinterlässt gemma4:e2b einen brauchbaren Produktionseindruck. P1 mit 90.00 ist für ein Nano-Generalist-Modell klar stark. Der Tool-Call war valide, ein Retry war nicht nötig, und es gibt keinen Hinweis auf Protokollbruch im MCP-Ablauf. Das spricht für saubere Formatdisziplin und dafür, dass das Modell Aufrufe technisch korrekt absetzen kann.

Was fehlt, ist der wichtigere zweite Teil der Bewertung: Es liegen keine Daten zu Web Search & Tool Selection und keine Daten zum URL-Construction-Test vor. Damit lässt sich nicht belastbar sagen, ob das Modell Werkzeuge situativ auswählt oder nur dann gut aussieht, wenn das richtige Tool bereits implizit vorgegeben ist. Für Architekturen mit freier Tool-Wahl bleibt genau dort ein offenes Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. P2 mit 45.83 zeigt, dass die Ausgabe nach erfolgreichem Tool-Einsatz nicht stabil genug in präzise, belastbare Ergebnistexte überführt wird. Für produktive Pipelines ist das kein Schönheitsfehler. Der eigentliche Wert von Tool-Nutzung entsteht erst dann, wenn das Modell das gefundene Material korrekt zusammenfasst, einordnet und ohne semantische Drift ausgibt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Dazu gibt es für EU License Research, den Honeypot für aktuelle Web-Recherche statt Trainingswissen, keine Einzeldaten. Gleichzeitig ist Halluzination erkannt worden. Das muss als Sicherheitsrisiko gelesen werden, nicht als bloße Qualitätsschwäche. Sobald ein Modell erfundene Fakten als scheinbare Tool-Ergebnisse ausgibt, verliert die gesamte Tool-Infrastruktur ihren Vertrauenswert.

**Fehlerresilienz**

Für Tool Failure Handling, den 404-Test auf transparentes Scheitern statt erfundenen Ersatzinhalt, liegen keine Daten vor. Deshalb gibt es hier kein positives Produktionssignal. In der Praxis bedeutet das: Fehlerpfade müssen außerhalb des Modells abgesichert werden. Ohne nachgewiesene saubere Fehlerkommunikation sollte es nicht autonom letzte Nutzerantworten nach fehlgeschlagenen Fetches formulieren.

**Souveränitätsprofil**

Lokal betreibbar, aber nicht fleet-kompetitiv. Der Combined Score liegt 1.37 Punkte unter dem Fleet-Ø von 67.84. Für souveräne Deployments ist das akzeptabel, wenn lokaler Betrieb Vorrang vor Antworttreue hat.

**Fazit & Empfehlung**

Geeignet für lokal betriebene, kostenunempfindliche Assistenz- oder Vorverarbeitungsstufen, in denen das Modell Tools korrekt anstößt und ein nachgelagerter Guardrail die Endausgabe prüft. Nicht geeignet für Compliance-, Research-, Support- oder Entscheidungs-Pipelines, in denen die Modellantwort selbst als verlässliche Repräsentation der Tool-Ergebnisse gelten muss. Wenn Sie es einsetzen, dann als Werkzeugbediener unter strikter Ergebnisvalidierung, nicht als vertrauenswürdigen Synthese-Endpunkt.