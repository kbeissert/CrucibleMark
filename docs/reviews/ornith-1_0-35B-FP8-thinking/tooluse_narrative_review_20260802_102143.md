**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:21:43


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesequalität mit Combined 72 nur dann tragfähig ist, wenn nachgelagerte Validierung die Antwortschicht absichert. Halluzination wurde nicht erkannt, aber der Tool-Call war nicht durchgehend valide.

**Tool-Execution-Profil**

Ornith 1.0 35B zeigt echte Werkzeugintelligenz statt bloßer Schablonenbefolgung. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die richtige Entscheidung durchgehend. Das spricht für brauchbare Orchestrierung in offenen Pipelines. Beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst, bleibt es solide, aber nicht deterministisch genug für fragile Produktionspfade. Die Differenz zwischen perfekter Tool-Wahl und nur ordentlicher URL-Präzision ist wichtig: Das Modell erkennt meist, welches Werkzeug es braucht, produziert aber nicht immer den präzisesten Aufruf. Dass der Tool-Call insgesamt nicht als valide markiert wurde, ist für MCP-gestützte Systeme ein Warnsignal auf Protokoll- oder Argumentebene.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 von 60 zeigt, dass Ornith gefundene Informationen verwertbar zusammenführt, aber nicht mit der Präzision, die man für Compliance-, Policy- oder Entscheidungs-Workflows erwartet. Besonders im Test EU License Research, der aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training verlangt, bricht die Verdichtung deutlich ein.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauensurteil ist gemischt. Positiv ist, dass keine Halluzination erkannt wurde. Negativ ist das Honeypot-Ergebnis selbst: P2 20 bei EU License Research zeigt, dass das Modell aktuelle Recherche nicht zuverlässig in belastbare Antwortform übersetzt. Es erfindet nicht offen, aber es verankert sich auch nicht stabil genug im beschafften Material.

**Fehlerresilienz**

Bei Tool-Fehlern verhält sich das Modell produktionsgerecht. Im Test Tool Failure Handling (404), der transparente Kommunikation bei fehlgeschlagenem Abruf statt halluziniertem Ersatzinhalt misst, bleibt es sauber. P2 80 und keine Halluzination trotz 404 bedeuten: Fehler werden als Fehler behandelt. Das ist für robuste Agent-Pipelines wichtiger als elegante Formulierungen.

**Souveränitätsprofil**

Lokal betreibbar, kommerziell unkritisch und für souveräne Stacks attraktiv. Mit einem Sovereignty Gap von -1.22 Punkten unter dem Fleet-Ø von 66.87 bleibt es praktisch auf Fleet-Niveau. Für ein Open-Weight-Modell im lokalen Betrieb ist das ein starkes Einsatzsignal.

**Fazit & Empfehlung**

Geeignet für lokale Agent- und Recherchepipelines, in denen Tool-Auswahl, Suchverhalten und saubere Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung. Nicht die erste Wahl für Compliance-Ausgaben, Executive Summaries oder andere Pfade, in denen die Antwortschicht selbst belastbar sein muss. Empfehlung: als orchestrierendes Arbeitsmodell mit engem Schema, strikter Output-Validierung und optionalem zweitem Modell für Verifikation oder Final Synthesis einsetzen.