**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:32


Bedingt deploy, weil Kimi K2.5 valide Tool-Calls ohne Halluzinationsbefund liefert, aber die Synthesequalität mit 60.00 für anspruchsvolle Entscheidungs-Pipelines zu inkonsistent bleibt.

**Tool-Execution-Profil**

Das stärkste Signal ist die Ausführungsebene. Mit P1 86.67 produziert das Modell verwertbare Tool-Aufrufe und bleibt MCP-konform. Der Tool-Call war valide, ein Retry war nicht nötig. Das spricht gegen ein Formatproblem und für tatsächliches Protokollverständnis. Für eine agentische Orchestrator-Rolle ist das die zentrale Eintrittskarte.

Bei der Werkzeugwahl lässt sich nur begrenzt fein urteilen, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelscores vorliegen. Aus dem Gesamtsignal folgt aber: Das Modell scheitert nicht an der operativen Übergabe an die Tool-Schicht. Es wirkt daher eher wie ein Modell mit echter Tool-Intelligenz als wie eines, das starr immer denselben Aufrufpfad nutzt. Für deterministische Pipelines bleibt trotzdem ein Vorbehalt, solange die Trennschärfe zwischen Suchbedarf und direktem Fetch nicht asset-spezifisch belegt ist.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 60.00 ist für Produktionssynthese kein Ausfall, aber auch kein starkes Vertrauenssignal. Man kann erwarten, dass Ergebnisse brauchbar zusammengeführt werden. Man sollte nicht erwarten, dass feine Fakten, Randbedingungen oder implizite Unterschiede immer sauber priorisiert werden. Für einfache Zusammenfassungen reicht das. Für Compliance, Policy, Vendor Assessment oder andere textkritische Aufgaben ist das zu knapp.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research wurde keine Halluzination erkannt. Das ist der wichtigere Befund als der fehlende P2-Wert. Das Modell beantwortet die aktuelle Lizenzfrage also nicht erkennbar aus altem Weltwissen, sondern hält die Bindung an externe Quellen ein. Für tool-gestützte Recherchepipelines ist das ein belastbares Vertrauenssignal.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen fehlgeschlagenen Tool-Call statt erfundenem Seiteninhalt prüft, halluzinierte Kimi K2.5 keinen Ersatzinhalt. Das ist produktionsfähig. Ein Modell muss bei Fehlern nicht elegant sein, aber es muss ehrlich sein. Diese Bedingung erfüllt es.

**Betriebsprofil**

Call 1: 6.49s. MCP-Latenz: 1.42s. Call 2: 34.44s. Total: 254.10s.  
Langsam.  
Kosten pro Run: 0.005853. Günstig.  
Im Verhältnis zur Leistung ist das Kostenprofil gut, das Latenzprofil jedoch klar der begrenzende Faktor.

**Fazit & Empfehlung**

Geeignet für agentische MCP-Pipelines, in denen Tool-Ausführung, Fehlertransparenz und niedrige Stückkosten wichtiger sind als erstklassige Verdichtung. Gut passend für Recherche-Orchestrierung, Vorstrukturierung und mehrstufige Tool-Ketten mit menschlicher Endkontrolle. Nicht die richtige Wahl für textkritische Endantworten, Compliance-Ausgaben ohne Review oder latenzsensitive Nutzerpfade. Als Tool-Operator brauchbar. Als autonomer Syntheseentscheider nur mit engen Guardrails.