**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:02:58


Bedingt deploy, weil die Tool-Ausführung stark ist, aber die Synthesetreue zu oft auf bloß ausreichendem statt belastbarem Produktionsniveau bleibt. Das Kernproblem ist nicht Halluzination, sondern dass valide Tool-Nutzung nicht durchgehend in präzise, quellentreue Verdichtung übersetzt wird.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, erkennt es korrekt, dass erst web_search nötig ist. Das spricht gegen ein starres Fetch-first-Muster. Auch bei Multilingual Search & Synthesis und EU License Research ruft es die nötigen Quellen zuverlässig ab.

Schwächer ist die Präzision im letzten Schritt. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Vorwissen ableiten und dann fetch ausführen lässt, bleibt die Ausführung brauchbar, aber nicht deterministisch genug für fragile Pipelines. Dazu passt das globale Signal: hohe Tool-Execution, aber tool_call_valid=false. Das Modell versteht also die Orchestrierung, produziert jedoch nicht in jedem Fall formal saubere oder vollständig protokollkonforme Calls. Retry war nicht nötig. Das ist eher ein Robustheits- als ein Verständnissproblem.

**Synthesetreue**

Wie gut verdichtet es? Nur mäßig belastbar. Die Verdichtung von Tool-Ergebnissen wirkt uneinheitlich: HTTP Fetch & Extract und URL Construction & Fetch sind sauber, aber EU License Research und Web Search & Tool Selection fallen bei der Zusammenführung deutlich ab. Für produktive MCP-Pipelines ist genau das kritisch, weil der Mehrwert nicht der Tool-Call selbst ist, sondern die korrekte Reduktion auf entscheidbare Fakten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Modell auf der sicheren Seite. P2=40 ist schwach, aber halluziniert nicht. Das ist ein wichtiges Vertrauenssignal: Es erfindet keine Compliance-Fakten, auch wenn es sie nicht gut genug verdichtet.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Scheitern statt erfundenem Seiteninhalt verlangt, kommuniziert das Modell den Fehlschlag ohne Halluzination. P2=60 zeigt, dass die Fehlerkommunikation noch knapper und operativer werden sollte, aber das Sicherheitsverhalten ist intakt.

**Betriebsprofil**

Call 1: 4.71s. MCP-Latenz: 1.29s. Call 2: 20.87s. Total: 161.26s.  
Lokal betrieben, daher direkte Run-Kosten vernachlässigbar.  
Für die gezeigte Leistung insgesamt langsam.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Retrieval-Pipelines, in denen Tool-Auswahl, Web-Zugriff und transparente Fehlerbehandlung wichtiger sind als perfekte Executive Summaries. Nicht geeignet für Compliance-, Policy- oder Decision-Support-Strecken, in denen die Antwort selbst revisionsfest sein muss. Wer dieses Modell einsetzt, sollte die Tool-Schicht nutzen, aber die finale Verdichtung durch ein strengeres Prüf- oder Postprocessing-Modul absichern.