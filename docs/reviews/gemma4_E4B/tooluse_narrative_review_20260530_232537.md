**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:25:37


Bedingt deploy, weil Gemma 4 E4B zuverlässig valide Tool-Calls erzeugt und keine Halluzination im Lauf gezeigt hat, die Synthesetreue nach dem Tool-Einsatz aber nur auf mittlerem Produktionsniveau liegt.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsseite klar belastbar. Tool-Calls waren valide, MCP-konform und ohne Retry ausführbar. Das ist für eine Tool-Pipeline die erste Hürde, und hier besteht kein akuter Integrationswiderstand. Besonders stark ist es beim Web Search & Tool Selection-Test, der prüft, ob ohne expliziten Hinweis web_search statt fetch nötig ist. Dort zeigt es echte Werkzeugwahl mit P1 100, nicht nur starres Musterverhalten. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Eigenwissen ableitet und dann fetch ausführt, fällt es auf P1 80 zurück. Das spricht dafür, dass es Tools richtig klassifiziert, aber bei deterministischer Vorarbeit vor dem Call nicht immer präzise genug bleibt. Für dynamische Recherche-Pipelines ist das akzeptabel. Für URL-sensitive Flows mit wenig Fehlertoleranz braucht es Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht stark genug für anspruchsvolle Entscheidungs- oder Compliance-Ausgaben. P2 60 im Gesamtbild heißt: brauchbare Zusammenfassung, jedoch begrenzte Präzision bei Verdichtung, Priorisierung und multilingualer Zusammenführung. Das sieht man besonders im Multilingual Search & Synthesis-Test, der sprachübergreifende Recherche auf Deutsch zusammenführt und nur P2 40 erreicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gut. Im EU License Research-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb das Modell im Tool-Pfad. Content-Verification-State A, keine Halluzination erkannt. Das ist der wichtigere Befund als die nur mittlere Verdichtungsqualität.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell produktionsgerecht. Im 404-Test, der zwischen transparenter Fehlerkommunikation und erfundenem Seiteninhalt unterscheidet, halluziniert es nicht und bleibt mit P2 80 klar auf der sicheren Seite. Das ist akzeptabel für Produktion, weil ein gescheiterter Abruf als Fehler sichtbar bleibt und nicht als falscher Inhalt in die Pipeline einsickert.

**Souveränitätsprofil**

Lokal betreibbar und insgesamt konkurrenzfähig, aber nicht fleet-führend. Der Sovereignty Gap liegt bei -5.32 Punkten unter dem Fleet-Ø von 66.76. Für local_sovereign ist das ein brauchbares Ergebnis, wenn Datenhaltung und Kontrollierbarkeit wichtiger sind als maximale Antwortqualität.

**Fazit & Empfehlung**

Geeignet für lokale Recherche-, Routing- und Tool-Orchestrierungs-Pipelines, in denen korrekte Tool-Nutzung und saubere Fehleroffenlegung wichtiger sind als hochwertige Endverdichtung. Nicht die erste Wahl für Pipelines, die aus Tool-Ergebnissen belastbare, dichte Entscheidungstexte oder mehrsprachige Synthesen erzeugen müssen. Deployen, wenn die finale Antwort durch Schema-Checks, Post-Processing oder einen stärkeren Reviewer abgesichert wird.