**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:00:15


Bedingt deploy, weil die Tool-Nutzung oft funktioniert, aber die Protokolltreue der Calls nicht sauber genug ist und die Synthese aus Tool-Ergebnissen für produktive Entscheidungswege zu unzuverlässig bleibt.  

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugintelligenz, nicht nur starres Musterverhalten. Beim Web-Search-and-Tool-Selection-Test erkennt es ohne expliziten Hinweis korrekt, dass zuerst Suche statt direktem Fetch nötig ist. Das ist ein starkes Signal für dynamische MCP-Pipelines. Auch beim URL-Construction-and-Fetch-Test leitet es Zielpfade meist brauchbar ab, aber nicht präzise genug für deterministische Abläufe. Der Unterschied zwischen perfekter Tool-Auswahl und nur ordentlicher URL-Konstruktion zeigt: Die Planungsentscheidung sitzt besser als die operative Ausführung.

Kritisch bleibt die formale Seite. Tool-Call valide ist false, obwohl kein Retry nötig war. Das spricht weniger für Verständnisprobleme als für unzuverlässige Protokoll- oder Argumenttreue im ersten Versuch. In einer MCP-Kette ist genau das teuer, weil Orchestratoren dann mit Guardrails oder Post-Validation nacharbeiten müssen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung zeigt, dass das Modell gefundene Inhalte oft nur grob zusammenzieht, statt sie präzise zu verdichten. Das sieht man besonders bei EU License Research und Multilingual Search and Synthesis, wo die Recherche gelingt, die nachgelagerte Verdichtung aber zu flach bleibt. Für menschenlesbare Notizen reicht das. Für Compliance-, Policy- oder Architekturentscheidungen reicht es nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauensurteil besser als die Verdichtungsqualität. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen kommen, wurde keine Halluzination erkannt. Das Modell wirkt also nicht erfinderisch, sondern eher unscharf. Für Produktion ist das der bessere Fehler.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei Tool-Fehlern prüft, halluziniert das Modell keinen Ersatzinhalt. Das ist der entscheidende Punkt. Die Qualität der Fehlerkommunikation ist dennoch nur begrenzt gut, weil die Antwort nicht sauber genug in einen klaren Fehlerpfad übersetzt wird. Produktionskritisch wäre erfundener Seiteninhalt. Das passiert hier nicht.

**Souveränitätsprofil**

Lokal betreibbar, kommerziell nutzbar und ohne externen Datentransfer einsetzbar. Mit 65.50 Combined liegt es 0.75 Punkte unter dem Fleet-Ø von 66.55. Das ist nah genug am Flottenschnitt, um als souveräne Option relevant zu bleiben. Die Modifikationskette der Gewichte senkt aber die Nachvollziehbarkeit.

**Fazit & Empfehlung**

Geeignet für lokale Recherche- und Assistenzpipelines, in denen ein Orchestrator Tool-Calls validiert, Fehlerfälle abfängt und ein Mensch die Endverdichtung prüft. Nicht geeignet für MCP-Strecken, die aus Tool-Ergebnissen direkt belastbare Aussagen für Compliance, Lizenzbewertung oder andere hochpräzise Entscheidungslogik ableiten. Wenn Sie ein lokales Modell mit brauchbarer Tool-Intelligenz suchen, ist es ein Kandidat. Wenn Sie einer unbeaufsichtigten Tool-Infrastruktur die Endantwort anvertrauen wollen, ist es noch nicht stabil genug.