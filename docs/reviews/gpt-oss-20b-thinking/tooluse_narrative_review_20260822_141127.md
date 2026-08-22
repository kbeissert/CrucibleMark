**Deployment-Urteil**

> **Erstellt am:** 22.08.2026, 14:11:27


Nicht deploy für produktive MCP-Pipelines, weil der Tool-Call nicht valide war und der kombinierte Befund mit 26.08 klar unter der Einsatzschwelle liegt. Dass keine Halluzination erkannt wurde, verhindert nur den schlimmsten Ausfallmodus.

**Tool-Execution-Profil**

Das Kernproblem liegt nicht in der Absicht zur Tool-Nutzung, sondern in der Ausführung. P1 liegt durchgängig bei 35, was auf ein systematisches Muster hindeutet: Das Modell erkennt den Tool-Kontext, produziert aber keine verlässlich gültigen Aufrufe. Für Produktion ist das zu wenig, weil MCP-Konformität binär wirkt. Ein fast richtiger Call ist operativ ein Fehlcall.

Die Tool-Selection-Daten zeigen auch keine belastbare Werkzeugintelligenz. Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis zwischen Suche und Direktabruf unterscheiden soll, bleibt es auf demselben Niveau wie beim URL-Construction-and-Fetch-Test, der präzise URL-Ableitung verlangt. Das spricht eher für ein starres Ausführungsverhalten als für saubere Situationsanpassung. Retry war nicht erforderlich. Das wirkt daher nicht wie ein behebbarer Format-Ausreißer, sondern wie ein Grundproblem in der Tool-Ausführung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 von 16.67 ist der eigentliche Produktivitätsbruch. Besonders im HTTP-Fetch-and-Extract-Test, der präzise Extraktion von Jahreszahlen, Eigennamen und Versionen aus echtem Fetch-Content misst, fällt die Verdichtung auf null. Das ist für jede Pipeline kritisch, die aus Tool-Output belastbare Felder oder Entscheidungsgrundlagen erzeugen soll.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil deutlich besser. Im EU-License-Research-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus dem Modellgedächtnis kommen, wurde keine Halluzination erkannt. Das schafft ein Mindestmaß an Vertrauen: Es erfindet nicht einfach aktuelle Compliance-Inhalte. Es kann sie nur nicht gut genug verarbeiten.

**Fehlerresilienz**

Akzeptabel. Im Tool-Failure-Handling-404-Test, der transparentes Verhalten bei fehlschlagendem Abruf prüft, halluziniert das Modell keinen Seiteninhalt. Es ersetzt Fehler also nicht durch erfundene Fakten. Das ist produktionsrelevant positiv, weil eine Pipeline mit klaren Fehlern weiter abgesichert werden kann.

**Betriebsprofil**

Total 62.71s pro Run. Einzelaufrufe 5.85s und 4.61s. Lokal betrieben, daher direkte Modellkosten praktisch niedrig. Im Verhältnis zur Leistung ist das langsam.

**Fazit & Empfehlung**

Geeignet höchstens für lokale, kostenkritische Assistenzpfade mit Human-in-the-Loop, in denen Tool-Fehler abgefangen und Ergebnisse manuell geprüft werden. Nicht geeignet für autonome MCP-Orchestrierung, Compliance-Recherche, strukturierte Extraktion oder jede Pipeline, die gültige Tool-Calls und präzise Verdichtung voraussetzt. Der Ausfallmodus ist nicht gefährlich halluzinativ, aber operativ unzuverlässig.