**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 09:01:37


Bedingt deploy, weil das Modell im vorliegenden Lauf kein Halluzinationssignal gezeigt hat, aber die Tool-Ausführung nicht als valide bestätigt ist und damit die zentrale Produktionsfrage offen bleibt. Der Combined-Score von 71.00 ist brauchbar, ersetzt aber keinen belastbaren Nachweis für protokolltreue Tool-Nutzung.

**Tool-Execution-Profil**

Das schwächste Signal hier ist nicht ein dokumentierter Fehlgriff, sondern fehlende Verifizierbarkeit. Für Tool Execution, Web Search & Tool Selection sowie URL Construction & Fetch liegen jeweils keine belastbaren P1-Werte vor. Damit lässt sich nicht belegen, ob Gemini 3.5 Flash das passende Werkzeug situativ auswählt oder nur einem generischen Muster folgt. Gerade für MCP-Pipelines ist das entscheidend: Ein Modell darf nicht nur sinnvoll wirken, sondern muss korrekte Calls erzeugen und das Protokoll sauber bedienen. Positiv ist nur, dass kein Retry erforderlich war. Das spricht gegen einen offensichtlichen Formatkollaps, sagt aber wenig über echtes Tool-Verständnis aus.

**Synthesetreue**

Zur Frage, wie gut es Tool-Ergebnisse verdichtet, gibt dieser Lauf kaum harte Evidenz. Für die eigentliche Synthesequalität fehlen P2-Werte über alle Assets hinweg. Deshalb ist weder die Präzision bei Faktenverdichtung noch die Stabilität bei mehrschrittiger Zusammenführung belastbar quantifiziert. Für produktive Architekturen bleibt die Verdichtungsleistung damit vorläufig offen.

Zur getrennten Vertrauensfrage, ob es im Tool-Ergebnis bleibt oder auf Trainingswissen ausweicht, ist das Signal besser. Beim Test EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das ist ein gutes Mindestsignal für Compliance-nahe Recherchen. Es ist aber kein Vollbeweis, weil auch hier keine inhaltliche Verifikation dokumentiert ist.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der transparentes Verhalten bei einem scheiternden Tool-Aufruf misst, hat das Modell keinen Ersatzinhalt halluziniert. Das ist für Produktion wesentlich. Wenn ein Tool fehlschlägt, ist saubere Fehlerkommunikation akzeptabel. Genau dieses Mindestverhalten scheint hier vorhanden zu sein. Für robuste Pipelines ist das ein klar positives Signal.

**Betriebsprofil**

Latenz: n/a  
Kosten pro Run: local  
Preisniveau laut Modelltarif: $1.5/1M Input, $9.0/1M Output  
Leistungsbild: ökonomisch attraktiv auf dem Papier, operativ mangels Laufzeitdaten nicht belastbar einordenbar

**Fazit & Empfehlung**

Geeignet für assistive, überwachte MCP-Pipelines mit starkem Orchestrator, klaren Tool-Gates und nachgelagerter Validierung. Nicht geeignet als autonomer Tool-Operator, solange valide Tool-Calls im eigenen Stack nicht nachgewiesen sind. Der produktive Reiz liegt im langen Kontext, multimodalen Input und der agentischen Ausrichtung. Die Freigabe sollte aber an einen internen Tool-Contract-Test gebunden werden: korrekte Tool-Wahl, URL-Präzision, strukturierte Outputs und Fehlerpfade unter Last.