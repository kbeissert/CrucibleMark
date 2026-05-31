**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:51:34


Bedingt deploy, weil Gemma 3 4B valide Tool-Calls erzeugt und im Tool-Handling stark ist, aber mit erkannter Halluzination bei nur moderater Gesamtleistung kein verlässlicher Synthese-Endpunkt für kritische Pipelines ist.

**Tool-Execution-Profil**

Die Tool-Ausführung ist der klare Produktionsvorteil dieses Modells. Es hält das MCP-Protokoll sauber ein, produziert valide Calls und brauchte keinen Retry. Beim Web-Search-&-Tool-Selection-Test, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, agiert es mit voller Treffsicherheit. Das spricht gegen reines Musterfolgen und für brauchbare Werkzeugwahl im Kontext. Beim URL-Construction-Test, der die Herleitung einer Ziel-URL aus Eigenwissen und anschließendes Fetch misst, bleibt es etwas unpräziser. P1 von 80 zeigt: Es kann die Strecke gehen, aber nicht deterministisch genug für fragile Pipelines, in denen die URL-Konstruktion selbst kritisch ist.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Werte sind der schwache Teil des Profils. Besonders EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis fallen mit jeweils 15 deutlich ab. Das Modell kann also Tools ausführen, verliert aber danach Faktenpräzision, Priorisierung und Verdichtung. Für produktive Pipelines heißt das: Die Retrieval-Schicht funktioniert besser als die Antwortschicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen bezogen werden, wurde eine Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell in einer Tool-Pipeline erfundene oder aus Vorwissen rekonstruierte Aussagen als Tool-Ergebnis ausgibt, unterläuft es die Vertrauenskette der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, halluziniert Gemma 3 4B keinen Ersatzinhalt. Das ist produktionsrelevant positiv. Die Fehlerkommunikation bleibt zwar nur mittelpräzise, aber sie bleibt auf der sicheren Seite: kein erfundener Seiteninhalt trotz fehlgeschlagenem Abruf.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments praktisch attraktiv. Leistung bleibt aber knapp unter Fleet-Niveau: -4.01 Punkte unter dem Fleet-Ø von 66.21. Für ein Nano-Modell ist das wettbewerbsfähig genug, aber kein Argument, Qualitätskontrollen abzubauen.

**Fazit & Empfehlung**

Geeignet für lokale, kostenkritische MCP-Pipelines, in denen das Modell primär Tools auswählt, Requests formuliert und Ergebnisse an eine nachgelagerte Prüfschicht übergibt. Nicht geeignet als letzter Antwortgenerator in Compliance-, Policy-, Research- oder mehrsprachigen Synthese-Pipelines. Wenn Sie es einsetzen, dann als Tool-Router oder Vorverarbeiter mit harter Output-Validierung, nicht als vertrauenswürdige Instanz für die inhaltliche Endfassung.