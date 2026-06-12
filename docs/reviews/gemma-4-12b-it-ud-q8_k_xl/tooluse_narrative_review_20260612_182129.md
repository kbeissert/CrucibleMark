**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:21:29


Bedingt deploy, weil das Modell valide Tool-Calls erzeugt und keine Halluzination im Lauf erkannt wurde, aber die Synthesetreue mit einem Combined-Score von 62.33 nur für kontrollierte Tool-Pipelines reicht.

**Tool-Execution-Profil**

Bei der Tool-Ausführung arbeitet das Modell grundsätzlich verlässlich. Tool-Call valide: true und kein Retry-Bedarf sprechen für saubere MCP-Konformität. Die eigentliche Stärke liegt in der Werkzeugwahl: Beim Web-Search-&-Tool-Selection-Test, der prüft, ob ohne Hinweis search statt fetch erkannt wird, erreicht es volle Ausführungssicherheit. Das wirkt nicht wie starres Musterfolgen, sondern wie brauchbare Situationsdiagnose. Auch beim Multilingual Search & Synthesis und bei EU License Research greift es die Web-Strecke korrekt auf.

Schwächer ist die Präzision im nachgelagerten Zugriff. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL misst, ist die Leistung brauchbar, aber nicht deterministisch genug für fragile Fetch-Ketten. Das Muster ist klar: Es weiß meist, welches Tool gebraucht wird, aber nicht immer exakt, wie der Zugriffspfad konstruiert werden muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. P2 43.33 ist der kritische Wert dieses Laufs. Das Modell kann Ergebnisse zusammenziehen, aber es verliert dabei Präzision, Priorisierung und Belegnähe. Das sieht man über mehrere Assets hinweg: EU License Research, Web Search & Tool Selection, URL Construction & Fetch und Multilingual Search & Synthesis bleiben alle bei P2 40. Für Produktionspipelines heißt das: Die Beschaffung stimmt häufiger als die Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb das Modell im verifizierten Inhaltsraum. Content-Verification-State A bei gleichzeitig keiner erkannten Halluzination ist ein echtes Vertrauenssignal.

**Fehlerresilienz**

Beim 404-Test, der transparentes Scheitern gegen erfundenen Ersatzinhalt prüft, halluziniert das Modell keinen Seiteninhalt. Das ist für Produktion der zentrale Punkt. Die Antwortqualität bleibt mit P2 40 nur mäßig, aber das Verhalten ist sicherer als der Score vermuten lässt: Es scheitert sichtbar, nicht verdeckt.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistung liegt  -1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist nah genug am Flottenschnitt, um lokale Nutzung ohne harten Qualitätsabfall zu rechtfertigen.

**Fazit & Empfehlung**

Geeignet für lokale, MCP-gestützte Pipelines mit klaren Guardrails, vor allem dort, wo Tool-Auswahl wichtiger ist als hochwertige Endverdichtung: Recherche-Routing, Voraggregation, mehrsprachige Beschaffung, kontrollierte Fetch-Workflows. Nicht die erste Wahl für Compliance-Reports, entscheidungsreife Zusammenfassungen oder Workflows, in denen die Modellantwort direkt an Fachnutzer geht. Wer es einsetzt, sollte die Tool-Phase nutzen und die finale Synthese durch ein stärkeres Redaktionsmodell oder harte Post-Checks absichern.