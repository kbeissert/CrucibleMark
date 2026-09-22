**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:16:49


Bedingt deploy, weil die Tool-Nutzung stark ist, aber ein invalider Tool-Call und erkannte Halluzination das Vertrauen für unbeaufsichtigte MCP-Pipelines begrenzen. Der Gesamteindruck ist gut, aber nicht robust genug für Hochvertrauensstrecken.

**Tool-Execution-Profil**

Qwen 3.8 27B zeigt echte Werkzeugintelligenz statt bloßem Musterfolgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählt es das passende Tool zuverlässig. Das spricht für brauchbare Planungslogik in dynamischen Pipelines. Beim URL-Construction-Test, der die Ziel-URL aus Eigenwissen ableiten und anschließend korrekt abrufen lässt, ist es dagegen weniger präzise. Das Ergebnis ist brauchbar, aber nicht deterministisch genug für Systeme, die aus Modelltext direkt Requests generieren.

Der P1-Wert von 90 zeigt insgesamt starke Ausführung. Kritisch bleibt jedoch, dass der Tool-Call im Lauf als nicht valide markiert wurde. Das ist kein Retry-Thema, also kein bloßes Formatproblem mit anschließend sauberer Korrektur, sondern ein Zuverlässigkeitssignal: Das Modell kann gute Tool-Entscheidungen treffen, produziert aber nicht durchgehend MCP-saubere Aufrufe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. Der P2-Wert von 59.17 passt zum Profil: solide bei klaren Fehlerfällen und strukturierter Suche, aber schwächer bei präziser Extraktion und Verdichtung aus Fetch-Inhalten. Besonders HTTP Fetch & Extract, also die saubere Übernahme konkreter Fakten aus abgerufenen Seiten, fällt mit P2 35 deutlich ab. Für Produktionspipelines heißt das: Ergebnisse müssen nach dem Tool-Aufruf oft noch gegengeprüft oder nachnormalisiert werden.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt es auf der sicheren Seite. Keine Halluzination wurde erkannt. Gleichzeitig ist global Halluzination erkannt: true gesetzt. Das ist als Sicherheitsrisiko zu werten, nicht als bloßer Qualitätsmangel. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird die gesamte Tool-Infrastruktur angreifbar.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei fehlschlagendem Abruf prüft, reagiert das Modell produktionsgerecht. Es kommuniziert den Fehler offen und erfindet keinen Seiteninhalt. Das ist ein starkes Signal. Solches Verhalten ist für operative Pipelines akzeptabel, weil Fehler sichtbar bleiben und Downstream-Systeme sauber eskalieren können.

**Betriebsprofil**

Call 1: 5.95s. MCP-Latenz: 1.45s. Call 2: 41.48s. Total: 293.29s.  
Lokal: keine API-Kosten.  
Geschwindigkeit: langsam bis sehr langsam im Gesamtlauf, gemessen an der nur guten Gesamtleistung.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Recherche- und Orchestrationspipelines mit menschlicher Kontrolle, besonders wenn Tool-Wahl wichtiger ist als perfekte Verdichtung. Auch für 404-robuste Agentenpfade brauchbar. Nicht geeignet für Compliance-, Fakten- oder Extraktionsstrecken, in denen Tool-Ergebnisse unverändert weiterverarbeitet werden. Wer Qwen 3.8 27B einsetzt, sollte strikte Output-Validierung, Schema-Prüfung und eine zweite Verifikationsstufe hinter jeden Tool-Schritt setzen.