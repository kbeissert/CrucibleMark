**Deployment-Urteil**

> **Erstellt am:** 23.09.2026, 00:17:30


Bedingt deploy. Das Modell ist für Tool-Ausführung stark und halluziniert in diesem Lauf nicht, aber der ungültige Tool-Call bei insgesamt nur guter Gesamtausbeute macht es für produktive MCP-Pipelines nur mit Guardrails vertretbar.

**Tool-Execution-Profil**

Qwen3.8-2.4T-A95B zeigt echte Werkzeugintelligenz statt bloßem Schema-Folgen. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Direktabruf prüft, erkennt es sauber, dass erst web_search und nicht fetch nötig ist. Das ist ein gutes Signal für offene, dynamische Agentenpfade. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen plus anschließenden Abruf verlangt, ist es brauchbar, aber nicht deterministisch genug. Hier liegt der Unterschied: Die strategische Tool-Wahl ist stark, die operative Präzision im konkreten Call schwankt. Da der Tool-Call insgesamt nicht valide war und kein Retry nötig wurde, spricht das eher für ein Ausführungs- oder Formatrandproblem als für ein grundsätzliches Missverständnis der Aufgabe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. Die P2-Leistung von 66,67 passt zu den Einzelbildern: HTTP Fetch & Extract ist sehr sauber, Multilingual Search & Synthesis fällt deutlich ab. Das Modell kann gefundene Informationen strukturieren, verliert aber bei mehrsprachiger oder compliance-naher Verdichtung an Präzision. Für Architekturen, in denen die Tool-Schicht nur Rohmaterial liefert und das Modell den finalen Bericht baut, ist das ein limitierender Faktor.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt es grundsätzlich im sicheren Bereich. Kein Halluzinationsbefund ist hier das wichtigere Signal als die nur mittlere P2-Ausbeute. Das Vertrauen in die Tool-Kette bleibt also erhalten, auch wenn die Verdichtung nicht durchgehend belastbar ist.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Test Tool Failure Handling (404), der auf Transparenz bei fehlschlagenden Tool-Calls zielt, kommuniziert das Modell den Fehler, statt Seiteninhalt zu erfinden. Genau das braucht eine robuste Pipeline. Der Befund ist nicht exzellent, aber sicher.

**Betriebsprofil**

Call 1: 4,59s. MCP-Latenz: 1,55s. Call 2: 25,20s. Total: 188,06s. Langsam für den erzielten Qualitätsstand. Kosten/Run: local. Preisprofil des Modells: $2,0/1M Input, $6,0/1M Output. Für Frontier-Niveau nicht teuer, aber die Laufzeit ist klar der operative Engpass.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines, in denen Tool-Auswahl, lange Kontexte und vorsichtiger Umgang mit Fehlern wichtiger sind als perfekte Endverdichtung. Nicht die erste Wahl für Compliance-Reports, mehrsprachige Synthese oder strikt deterministische MCP-Strecken, in denen jeder Tool-Call formal sitzen muss. Deploy nur mit Call-Validation, Output-Schema-Checks und einer nachgelagerten Verifikationsschicht für die finale Zusammenfassung.