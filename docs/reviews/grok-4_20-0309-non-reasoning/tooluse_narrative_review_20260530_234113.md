**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:41:13


Bedingt deploy, weil die Tool-Calls überwiegend valide sind und die Ausführungsseite belastbar wirkt, das Modell aber mit erkannter Halluzination in einem Tool-gestützten Setting das Vertrauensmodell der Pipeline verletzt.

**Tool-Execution-Profil**

Grok 4 (Non-Reasoning) zeigt eine starke operative Tool-Nutzung. Mit P1 82.50 produziert es meist gültige Calls und bleibt MCP-seitig anschlussfähig. Besonders auffällig ist der Web-Search-and-Tool-Selection-Test, der prüft, ob ohne Hinweis statt fetch die Websuche gewählt werden muss: Hier handelt das Modell mit P1 95 klar situationsbezogen und nicht nur nach starrem Muster. Auch beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL mit anschließendem Fetch misst, arbeitet es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Pipelines mit harter URL-Präzision.

Dass ein Retry erforderlich war, spricht eher für Format- oder Ablaufinstabilität als für ein grundlegendes Verständnisproblem. Die hohe Validität der finalen Tool-Calls legt nahe, dass das Modell die Werkzeuglogik versteht, aber im ersten Durchlauf nicht immer sauber in das erwartete Protokoll oder Ausgabeformat einrastet.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 54.17 ist für ein Frontier-Generalistenmodell zu schwach, weil die Nachverarbeitung stark schwankt. Solide arbeitet es bei HTTP Fetch & Extract und bei URL Construction & Fetch mit jeweils P2 80 sowie bei Tool Failure Handling (404) mit P2 100. Kritisch brechen jedoch EU License Research mit P2 15, Web Search & Tool Selection mit P2 35 und Multilingual Search & Synthesis mit P2 15 ein. Das Muster ist klar: Es kann abrufen, aber nicht durchgehend verlässlich in belastbare, quellennahe Antworten überführen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Webquellen geholt werden, wurde eine Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell erfundene oder aus dem Training stammende Fakten als Ergebnis einer Tool-Recherche ausgibt, verliert die gesamte MCP-Infrastruktur ihre Auditierbarkeit.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell produktionsfähig. Im 404-Test, der transparente Fehlerkommunikation statt erfundenem Ersatzinhalt misst, erreichte es P2 100 und halluzinierte keinen Seiteninhalt. Das ist für den Betrieb entscheidend: Ein fehlgeschlagener Aufruf bleibt als Fehler sichtbar und wird nicht kaschiert.

**Betriebsprofil**

Call 1: 5.44s. MCP-Latenz: 1.18s. Call 2: 3.69s. Total: 61.88s.  
Kosten pro Run: 0.029169.  
Urteil: nicht schnell, preislich moderat, gemessen an der Syntheseleistung nur bedingt effizient.

**Fazit & Empfehlung**

Geeignet für überwachte Tool-Pipelines mit klaren Guardrails, Ergebnisvalidierung und nachgelagerter Prüfung auf Quellentreue. Gut einsetzbar für Retrieval, Fetch, Suchanstoß und transparentes Fehlerhandling. Nicht geeignet für Compliance-, Policy-, Lizenz- oder mehrsprachige Recherchepipelines, in denen die Antwort selbst als verifizierte Verdichtung gelten soll. Wenn Sie dieses Modell einsetzen, dann als ausführendes Werkzeugmodell mit strikter Verifikation, nicht als letzte vertrauenswürdige Syntheseschicht.