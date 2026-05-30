**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:49:11


Bedingt deploy, weil die Tool-Ausführung verlässlich ist und keine Halluzination erkannt wurde, die Synthesetreue nach Tool-Nutzung aber zu uneinheitlich für unüberwachte Produktionspfade bleibt.

**Tool-Execution-Profil**

Grok 4 Reasoning zeigt ein belastbares Tool-Profil. Die Calls waren valide, das MCP-Protokoll wurde eingehalten, und der P1-Wert von 89.17 bestätigt, dass das Modell Werkzeuge operativ beherrscht. Besonders stark ist die Werkzeugwahl: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Fetch unterscheiden lässt, wählte es das richtige Tool fehlerfrei. Das spricht gegen starres Musterfolgen und für echte Situationsbewertung.

Weniger stark ist die Präzision beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und danach sauber fetcht. P1 80 ist brauchbar, aber nicht präzise genug für deterministische Pipelines mit harten URL-Annahmen. Retry erforderlich wirkt hier eher wie ein Format- oder Ablaufproblem als wie ein Verständnisfehler. Das Modell weiß grundsätzlich, welches Werkzeug es braucht, braucht aber Guardrails bei der letzten Ausführungsschärfe.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt gut. P2 56.67 ist der zentrale Schwachpunkt dieses Laufs. Das Modell findet Informationen, verdichtet sie aber nicht durchgehend präzise genug für Architekturen, in denen die Antwort selbst weiterverarbeitet oder direkt an Nutzer ausgeliefert wird. Die Einzelergebnisse bestätigen das: EU License Research und Tool Failure Handling (404) liegen beide bei P2 40, also dort, wo operative Zurückhaltung wichtiger wäre als reasoning-lastige Ausschmückung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Test EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb es trotz schwacher Verdichtung im verifizierten Inhaltsraum. Content-Verification-State A und keine erkannte Halluzination sind ein klares Vertrauenssignal. Das Modell erfindet hier nichts, es fasst nur nicht streng genug zusammen.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt misst, blieb Grok 4 Reasoning auf der sicheren Seite. Es halluzinierte keinen Seiteninhalt trotz Fehler. P2 40 zeigt, dass die Fehlerdarstellung nicht besonders knapp oder entscheidungsreif war. Für Produktion ist das trotzdem akzeptabel, weil das Sicherheitskriterium erfüllt ist: Fehlschlag wird als Fehlschlag behandelt.

**Betriebsprofil**

Total 90.93s. Einzelaufrufe 7.15s und 7.11s. MCP-Latenz 0.89s. Langsam für interaktive Pfade, vertretbar für hochwertige Hintergrundläufe. Kosten pro Run 0.014590. Preislich moderat, gemessen an der Leistung eher akzeptabel als attraktiv.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit menschlicher Prüfung, für Recherche-Orchestrierung und für Tool-first Agents, bei denen Tool-Auswahl und Fehlersicherheit wichtiger sind als perfekte Endverdichtung. Nicht die richtige Wahl für vollautomatische Compliance-, Policy- oder Executive-Summary-Pfade, in denen die Antwort selbst ohne Nachkontrolle entscheidungsreif sein muss. Wenn Sie es einsetzen, dann mit strikter Antwortvalidierung, knappen Ausgabeformaten und Retry-Handling auf der Orchestrierungsseite.