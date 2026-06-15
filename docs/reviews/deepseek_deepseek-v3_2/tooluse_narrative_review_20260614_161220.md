**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:12:20


Bedingt deploy, weil DeepSeek V3-2 Tool-Aufrufe zuverlässig und protokollkonform ausführt, aber die Verdichtung der Tool-Ergebnisse für produktive Entscheidungs- oder Compliance-Pipelines nicht konsistent präzise genug ist.

**Tool-Execution-Profil**

Das Ausführungsprofil ist stark. Der Tool-Call war valide, ein Retry war nicht nötig, und mit P1 90 zeigt das Modell, dass es MCP-gestützte Werkzeuge operativ beherrscht. Besonders wichtig ist die Werkzeugwahl: Beim Web-Search-and-Tool-Selection-Test, der ohne expliziten Hinweis zwischen Suche und direktem Fetch unterscheidet, wählte es das richtige Werkzeug sicher. Das spricht gegen starres Musterverhalten und für echte Situationsanpassung.

Etwas schwächer ist die Präzision beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und anschließend per Fetch abruft. Hier arbeitet es brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen exakte Endpunkte konstruieren lassen. Für discovery-lastige Flows ist das akzeptabel. Für fest verdrahtete Abrufketten sollte man URL-Bildung möglichst externalisieren.

**Synthesetreue**

Wie gut verdichtet es? Nur ordentlich. P2 60 ist der klare Begrenzungsfaktor dieses Modells. Es extrahiert und kombiniert Ergebnisse, aber die Zusammenfassung verliert zu oft Schärfe, besonders in Multilingual Search & Synthesis, wo die Recherche über Sprachgrenzen gelingt, die deutsche Verdichtung aber sichtbar abfällt. Für Operator-Support und Vorstrukturierung reicht das. Für belastbare Ergebnisnarrative eher nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal deutlich besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, blieb das Modell im verifizierten Inhaltsraum. Content-Verification-State A und keine erkannte Halluzination sind für produktive Tool-Pipelines ein starkes Signal.

**Fehlerresilienz**

Im 404-Test, der transparentes Scheitern von erfundenem Seiteninhalt trennt, reagierte DeepSeek V3-2 produktionsgerecht. Es halluzinierte keinen Ersatzinhalt und kommunizierte den Fehlschlag sauber. Das ist akzeptables Verhalten für reale Infrastrukturen, in denen einzelne Tools regelmäßig ausfallen.

**Betriebsprofil**

3.30s erster Call. 13.18s zweiter Call. 105.20s total. Günstig mit 0.001770 USD pro Run. Latenz insgesamt lang im Verhältnis zur nur soliden Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen zuverlässige Tool-Nutzung wichtiger ist als hochwertige Ergebnisverdichtung: Recherche-Orchestrierung, Vorabklärung, Link-Discovery, technische Assistenz und coder-nahe Workflows. Nicht die erste Wahl für Compliance-Berichte, Executive Summaries oder mehrsprachige Wissenssynthese mit hoher Formulierungspräzision. Wenn Sie DeepSeek V3-2 einsetzen, dann als Tool-Operator mit nachgelagerter strenger Validierung oder zweitem Synthese-Schritt.