**Deployment-Urteil**

> **Erstellt am:** 06.09.2026, 18:11:25


Bedingt deploy, weil die Tool-Ausführung stark ist und keine Halluzination erkannt wurde, aber der nicht valide Tool-Call trotz hohem Gesamtscore das Vertrauen in eine strikt automatisierte MCP-Pipeline begrenzt.

**Tool-Execution-Profil**

Qwen 3.8 27B zeigt echte Werkzeugintelligenz statt bloßer Schablonenbefolgung. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, wählt es das richtige Tool sicher. Das spricht für brauchbare Planungslogik in offenen Retrieval-Schritten. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Modellwissen ableiten und dann per Fetch abrufen lässt, bleibt es dagegen nur solide. Das Muster ist klar: Wenn die Tool-Wahl das Hauptproblem ist, arbeitet das Modell stark. Wenn die Pipeline auf präzise URL-Konstruktion und vollständig valide Call-Parameter angewiesen ist, sinkt die Deterministik. Der Befund „Tool-Call valide: false“ ist deshalb produktionsrelevant. Nicht als Zeichen fehlenden Verständnisses, sondern als Hinweis auf formale Unsicherheit an der MCP-Schnittstelle.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt überzeugend. Die P2-Leistung von 59.17 zeigt, dass Qwen 3.8 27B brauchbare Ergebnisse zusammenzieht, aber nicht konstant präzise genug für Pipelines ist, in denen aus Tool-Output belastbare Kurzfassungen, Extrakte oder Entscheidungsvorlagen entstehen sollen. Stark ist es bei HTTP Fetch & Extract und bei Tool Failure Handling (404), schwächer bei mehrsprachiger Verdichtung und bei konsistenter Endredaktion.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus trainiertem Vorwissen beantwortet werden, bleibt das Modell auf der sicheren Seite. Keine Halluzination, P2 80. Das ist ein gutes Vertrauenssignal für Compliance-nahe Recherchestränge.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell produktionsgerecht. Im 404-Test, der transparentes Verhalten bei einem fehlschlagenden Abruf prüft, erfindet es keinen Seiteninhalt und kommuniziert den Ausfall sauber. Das ist entscheidend. Ein Modell darf scheitern, aber es darf den Fehler nicht mit erfundenen Fakten verdecken. Hier ist Qwen 3.8 27B verlässlich.

**Betriebsprofil**

Call 1: 5.55s. MCP-Latenz: 0.90s. Call 2: 43.90s. Total: 302.09s. Langsam. Kosten pro Run: local. Günstig im Betrieb, aber zeitlich teuer im Verhältnis zur nur mittleren Synthesequalität.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Agentenpipelines, in denen Tool-Wahl, Web-Suche und transparente Fehlerbehandlung wichtiger sind als perfekte Ergebnisverdichtung. Nicht die erste Wahl für vollautomatische MCP-Strecken mit harten Anforderungen an Call-Validität, strikte URL-Präzision und hochwertige Endsynthese ohne menschliche Kontrolle. Am besten als orchestrierendes Arbeitsmodell mit nachgelagerter Validierung oder Redaktionsstufe einsetzen.