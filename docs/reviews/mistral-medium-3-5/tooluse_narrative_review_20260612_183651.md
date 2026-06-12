**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:36:51


Bedingt deploy, weil die Tool-Ausführung stark und protokollsauber ist, die Synthesetreue mit Combined 74.25 aber nicht stabil genug für ungeprüfte High-Trust-Pipelines bleibt. Tool-Calls waren valide, ein Retry war nicht nötig, trotzdem wurde im Lauf eine Halluzination erkannt. Das ist im Produktionseinsatz ein Sicherheitsbefund.

**Tool-Execution-Profil**

Mistral Medium 3.5 verhält sich auf der MCP-Ebene belastbar. P1 mit 90 zeigt, dass das Modell Tools nicht nur aufruft, sondern in der Regel korrekt auswählt und formal gültig benutzt. Besonders relevant ist der Kontrast zwischen Web Search & Tool Selection und URL Construction & Fetch: Beim Test, ob ohne Hinweis erkannt wird, dass erst gesucht statt direkt gefetcht werden muss, liefert es P1 100. Das spricht für echte Werkzeugwahl statt starrem Abrufmuster. Beim Test, ob es eine Ziel-URL aus Eigenwissen präzise konstruieren und dann fetchen kann, fällt es auf P1 80 zurück. Die Schwäche liegt also nicht in der Tool-Intelligenz, sondern in der letzten Meile der Adresspräzision. Für dynamische Pipelines ist das akzeptabel. Für deterministische Fetch-Flows mit fragilen Endpunkten ist es ein Risiko.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Uneinheitlich. HTTP Fetch & Extract mit P2 100 ist stark und zeigt saubere Extraktion aus konkretem Content. Dem stehen schwache Verdichtungen in EU License Research und Multilingual Search & Synthesis mit jeweils P2 40 sowie URL Construction & Fetch mit P2 35 gegenüber. Das Modell kann also Ergebnisse korrekt holen, verdichtet sie aber nicht durchgehend präzise genug für belastbare Entscheidungsoutputs.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, blieb es formal im Werkzeugpfad: Content-Verification-State A, keine Halluzination erkannt. Das ist positiv. Gleichzeitig steht der globale Halluzinationsbefund im Run im Raum. Damit ist das Risiko nicht hypothetisch. Wenn ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es das Vertrauen in die gesamte Tool-Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit fehlschlagenden Tool-Calls prüft, halluziniert Mistral Medium 3.5 keinen Seiteninhalt. P2 60 ist kein Qualitätsbeweis, aber ein brauchbares Produktionssignal: Es kommuniziert Fehler eher offen, statt Ersatzinhalt zu erfinden. Das ist akzeptabel und deutlich wichtiger als sprachliche Glätte.

**Souveränitätsprofil**

Lokal betreibbar, open weights und damit für souveräne Deployments attraktiv. Leistungsseitig liegt es 1.37 Punkte unter dem Fleet-Ø von 67.62 und ist damit praktisch fleet-kompetitiv, ohne Souveränität gegen deutlichen Qualitätsverlust zu tauschen.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Recherche, Tool-Orchestrierung, Websuche und strukturierter Extraktion, besonders wenn ein nachgelagerter Verifier oder schema-strikter Postprocessor die Antwort absichert. Nicht die erste Wahl für Compliance-, Policy- oder mehrsprachige Synthese-Strecken, in denen die verbale Verdichtung selbst als Endprodukt gilt. Wer ihm Infrastruktur übergibt, kann sich auf die Werkzeugseite eher verlassen als auf die letzte inhaltliche Zusammenfassung.