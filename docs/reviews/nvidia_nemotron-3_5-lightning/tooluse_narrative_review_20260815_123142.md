**Deployment-Urteil**

> **Erstellt am:** 15.08.2026, 12:31:42


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue mit P2 50.00 und nicht validem Tool-Call zu wenig Sicherheitsreserve für autonome End-to-End-Pipelines bietet.

**Tool-Execution-Profil**

NVIDIA Nemotron 3.5 Lightning zeigt klare operative Stärke bei der Werkzeugwahl. Beim Test Web Search & Tool Selection, der ohne Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählt es das richtige Werkzeug zuverlässig. Das spricht gegen starres Musterfolgen und für brauchbare Tool-Intelligenz in offenen Retrieval-Schritten. Beim URL-Construction-Test konstruiert es die Ziel-URL brauchbar und führt Fetch meist korrekt aus, aber nicht mit der Präzision, die man für deterministische Pipelines ohne Guardrails erwartet.

Der Gesamtwert in P1 ist hoch, doch der Befund „Tool-Call valide: false“ ist für MCP-Betrieb relevant. Das Modell plant und startet Werkzeuge gut, produziert aber nicht durchgehend protokollsaubere Aufrufe. Da kein Retry erforderlich war, liegt das Problem eher in der finalen Call-Form oder Parametrisierung als im grundsätzlichen Aufgabenverständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ausreichend. Die P2-Leistung bleibt sichtbar hinter der Ausführungsschicht zurück. In EU License Research, Tool Failure Handling (404) und Web Search & Tool Selection fällt die Verdichtung auf P2 40 zurück. Das bedeutet: Es findet den Stoff, komprimiert ihn aber nicht zuverlässig in belastbare, entscheidungsreife Antworten. Für Workflows mit menschlicher Nachsicht ist das tragbar. Für automatische Weiterverarbeitung ist es zu instabil.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Das Vertrauenssignal ist besser als die Verdichtungsqualität. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, wurde keine Halluzination erkannt. Das Modell erfindet hier also keine Compliance-Fakten aus dem Vorwissen. Dieses Verhalten hält die Pipeline vertrauensfähig, auch wenn die Antwortausbeute knapp oder unvollständig bleibt.

**Fehlerresilienz**

Beim 404-Test, der transparentes Scheitern gegen erfundenen Ersatzinhalt prüft, bleibt das Modell auf der sicheren Seite. Es halluziniert keinen Seiteninhalt trotz fehlgeschlagenem Tool-Aufruf. Die P2 40 zeigt aber, dass die Fehlerkommunikation eher knapp als operativ hilfreich ist. Für Produktion ist das akzeptabel: Ein sauber gemeldeter Fehler ist reparierbar, erfundener Inhalt nicht.

**Souveränitätsprofil**

Lokal betreibbar, open weights und damit ohne Cloud-Zwang in souveränen Umgebungen einsetzbar. Mit 70.50 Combined liegt es 3.19 Punkte über dem Fleet-Ø von 67.31. Für ein lokal lauffähiges Agentenmodell ist das konkurrenzfähig.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit Retrieval, Suchsteuerung, mehrsprachiger Recherche und menschlichem Review vor der finalen Übergabe. Nicht geeignet als unbeaufsichtigter Synthese-Endpunkt für Compliance, Policy oder andere textkritische Entscheidungen, bei denen die Antwort selbst belastbar sein muss. Empfohlen als lokaler Orchestrator mit strikten Schema-Checks, Call-Validation und nachgelagerter Verifikation der Zusammenfassung.