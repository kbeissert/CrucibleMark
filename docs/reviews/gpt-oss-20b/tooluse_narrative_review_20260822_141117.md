**Deployment-Urteil**

> **Erstellt am:** 22.08.2026, 14:11:17


Nicht deploy für autonome MCP-Pipelines, weil die Tool-Calls nicht valide sind und der kombinierte Befund mit 27.75 klar unter Produktionsniveau liegt. Positiv ist nur, dass keine Halluzination erkannt wurde.

**Tool-Execution-Profil**

Das Kernproblem liegt nicht in der Wissensdisziplin, sondern in der Ausführung. P1 liegt durchgehend bei 35, also auf einem Niveau, das weder sichere Tool-Wahl noch protokollfeste Ausführung trägt. Beim Test Web Search & Tool Selection, der prüft, ob das Modell ohne Hinweis erkennt, dass eine Suche statt eines direkten Fetch nötig ist, zeigt es keine belastbare Werkzeugintelligenz. Beim Test URL Construction & Fetch, der die korrekte Ziel-URL aus eigenem Wissen ableiten und dann sauber abrufen soll, bleibt es auf demselben schwachen Niveau. Das spricht eher für ein starres oder unsicheres Tool-Muster als für kontextabhängige Auswahl. Entscheidend für den Betrieb: Der Tool-Call war nicht valide. Damit ist die MCP-Integration praktisch blockiert, selbst wenn die verbale Antwort noch brauchbar wirkt. Retry war nicht erforderlich, also ist das kein einmaliger Format-Ausreißer, sondern ein grundlegendes Zuverlässigkeitsdefizit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 liegt konstant bei 20 über alle Assets, also auch bei HTTP Fetch & Extract und Multilingual Search & Synthesis, wo präzise Verdichtung von abgerufenen Inhalten, Eigennamen und Jahreszahlen zählen würde. Das Modell scheint Inhalte nicht robust in knappe, belastbare Arbeitsantworten zu überführen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen kommen, wurde keine Halluzination erkannt. Das ist ein Vertrauenssignal. Es zeigt Zurückhaltung, kompensiert aber die schwache Synthese nicht.

**Fehlerresilienz**

Beim 404-Test, der misst, ob das Modell nach einem fehlgeschlagenen Tool-Aufruf transparent bleibt oder Seiteninhalt erfindet, halluziniert es nicht. Das ist für Produktion wichtig. Ein Modell darf an einem Tool scheitern, wenn es den Fehler klar meldet. Genau diese Mindestdisziplin ist hier vorhanden. Sie hebt das Modell aber nur auf „nicht gefährlich“, nicht auf „einsatzbereit“.

**Betriebsprofil**

Total 61.43s pro Run. Einzelaufrufe 5.71s und 4.53s. Lokal betrieben, also infrastrukturell günstig. Für diese Leistungsstufe ist die Gesamtlatenz zu hoch.

**Fazit & Empfehlung**

Geeignet höchstens für überwachte lokale Setups, in denen ein externer Orchestrator die Tool-Wahl erzwingt, Calls validiert und Antworten nachprüft. Nicht geeignet für agentische Rechercheströme, Compliance-Pipelines oder allgemein für MCP-Workflows, in denen das Modell selbstständig Tools auswählen und korrekt aufrufen muss. Wer lokale Souveränität mit echter Tool-Zuverlässigkeit braucht, sollte dieses Modell nur als sprachliches Nachbearbeitungsmodul einsetzen, nicht als Tool-Agent.