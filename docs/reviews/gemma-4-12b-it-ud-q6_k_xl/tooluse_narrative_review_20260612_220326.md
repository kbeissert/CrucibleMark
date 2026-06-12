**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:03:26


Bedingt deploy, weil das Modell valide Tool-Calls erzeugt und nicht halluziniert, aber die Synthesequalität mit Combined 63.21 und klaren Verdichtungsschwächen für verlässliche Endantworten nicht ausreicht.

**Tool-Execution-Profil**

Die operative Tool-Seite ist die stärkere Hälfte dieses Modells. Es arbeitet MCP-konform, der Tool-Call war valide, und es erkennt bei dynamischen Aufgaben meist das richtige Werkzeug. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch nötig ist, zeigt es mit P1 95 echte Werkzeugwahl statt sturem Schema. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließenden Fetch misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für empfindliche Pipelines mit harter URL-Präzision.

Das Profil spricht also für echte Tool-Intelligenz, nicht nur für Formatbefolgung. Der notwendige Retry wirkt dabei eher wie ein Robustheits- oder Formatproblem im Ablauf als wie ein grundlegendes Verständnisversagen. Kritisch ist weniger die Auswahl des Tools als die Stabilität bis zur fertigen, verwertbaren Antwort.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 46.67 ist der zentrale Schwachpunkt. Das Modell findet Informationen, komprimiert sie aber oft zu grob, lässt relevante Nuancen weg oder liefert nur teilweise belastbare Schlussfassungen. Das sieht man besonders bei EU License Research mit P2 20 und bei Web Search & Tool Selection mit P2 40. Besser wird es bei HTTP Fetch & Extract sowie URL Construction & Fetch mit P2 60, also dort, wo die Quelle enger geführt ist.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil besser. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das ist ein Vertrauenssignal. Dennoch bleibt die Antworttreue nicht hoch genug, weil es zwar nicht erfindet, aber die gefundenen Inhalte zu schwach absichert und verdichtet.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell akzeptabel. Im 404-Test, der transparente Fehlerkommunikation gegen erfundenen Ersatzinhalt misst, halluziniert es keinen Seiteninhalt. P2 40 zeigt keine saubere operative Fehlerbehandlung, aber immerhin eine wichtige Produktionseigenschaft: Es verdeckt den Fehler nicht mit plausibel klingendem Fülltext.

**Souveränitätsprofil**

Lokal gut betreibbar, aber nicht fleet-kompetitiv. Das Modell liegt 1.37 Punkte unter dem Fleet-Ø von 67.62. Für eine lokale, souveräne Tool-Pipeline ist das vertretbar, solange die Abschlussverdichtung außerhalb des Modells abgesichert wird.

**Fazit & Empfehlung**

Geeignet ist dieses Modell für lokale MCP-Pipelines, in denen Tool-Auswahl, Web-Recherche und mehrsprachige Informationsbeschaffung wichtiger sind als präzise Endverdichtung. Es passt als Recherche- und Orchestrierungsschicht mit nachgelagerter Validierung oder einem stärkeren Reviewer-Modell. Nicht geeignet ist es als alleinige Antwortinstanz für Compliance, Lizenzbewertung, Executive Summaries oder andere Pfade, in denen die Synthese selbst das Produkt ist.