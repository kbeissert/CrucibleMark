**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:23:59


Bedingt deploy, weil die Werkzeugsteuerung stark ist, aber ein ungültiger Tool-Call und erkannte Halluzination das Vertrauen in unbeaufsichtigte MCP-Pipelines begrenzen. Der Combined-Score von 71.67 zeigt brauchbare Produktionsreife, aber keine Freigabe für High-Trust-Automation.

**Tool-Execution-Profil**

GPT-OSS 120B zeigt echte Werkzeugintelligenz statt stumpfer Routinen. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis search statt fetch gewählt wird, traf es die richtige Wahl sicher. Das ist ein gutes Signal für dynamische Tool-Pipelines. Beim URL-Construction-Test konstruiert es die Ziel-URL meist brauchbar und führt den Fetch anschließend aus, aber nicht präzise genug für deterministische Abläufe. Das erklärt den P1-Abfall auf 80 in diesem Asset.

Die Gesamtbewertung für Tool Execution ist mit 90 stark. Trotzdem bleibt der Befund „Tool-Call valide: false“ kritisch. Das heißt operativ: Die Planungsseite ist belastbar, die Protokolltreue nicht durchgehend. Für MCP ist genau diese letzte Meile entscheidend. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein persistentes Formatversagen und eher für einen einzelnen Ausführungsfehler.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung von 55 zeigt, dass das Modell gefundene Inhalte oft nicht sauber in belastbare Endantworten überführt. Besonders deutlich ist das bei HTTP Fetch & Extract und Multilingual Search & Synthesis, also genau dort, wo exakte Übernahme von Fakten, Namen und Versionen zählt. Für Recherche mit menschlicher Nachkontrolle ist das tragbar. Für automatische Downstream-Entscheidungen ist es zu unsauber.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt das Modell ausreichend auf Quellenkurs und halluziniert nicht. Das ist das wichtigere Vertrauenssignal. Gleichzeitig ist der globale Halluzinationsbefund ein Sicherheitsrisiko, nicht nur ein Qualitätsmangel. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird die gesamte Tool-Infrastruktur als Wahrheitsanker beschädigt.

**Fehlerresilienz**

Im 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call prüft, verhält sich das Modell produktionsgerecht. Es kommuniziert den Fehler sauber und erfindet keinen Seiteninhalt. Das ist für den Betrieb entscheidend. Ein Tool kann ausfallen. Das Modell darf dann nur Unsicherheit melden, nicht Lücken füllen.

**Betriebsprofil**

Call 1: 15.45s. MCP-Latenz: 1.26s. Call 2: 31.76s. Total: 290.85s. Langsam für die gezeigte Synthesequalität. Kosten/Run: local. Günstig im Geldfluss, teuer in Laufzeit.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Research- und Retrieval-Pipelines, in denen das Modell Tools selbst auswählen soll und ein Operator die Endantwort prüft. Nicht geeignet für Compliance-, Extraktions- oder mehrsprachige Synthese-Pipelines, in denen die Tool-Antwort ohne menschliche Kontrolle weiterverarbeitet wird. Wenn Sie es einsetzen, dann mit strikter Antwortvalidierung, Schema-Prüfung für Tool-Calls und einem Guardrail, das finale Aussagen an die tatsächlichen Tool-Rückgaben bindet.