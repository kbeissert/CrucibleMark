**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:15:27


Bedingt deployen, weil die Tool-Ausführung stark und protokollsauber ist, die Synthesetreue aber zu oft vom belegbaren Tool-Inhalt wegdriftet und damit das Vertrauen in nachgelagerte Entscheidungen begrenzt.

**Tool-Execution-Profil**

Mistral Medium 3.5 verhält sich auf der MCP-Seite produktionsreif. Die Tool-Calls sind valide, Retry war nicht erforderlich, und das Modell zeigt kein reines Schema-Folgen. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis statt fetch ein Such-Tool gewählt werden muss, trifft es die richtige Werkzeugwahl sicher. Das spricht für echte Werkzeugintelligenz in offenen Pipelines.

Schwächer ist die Präzision beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableiten und dann fetch ausführen kann. Hier reicht die Ausführung für brauchbare Ergebnisse, aber nicht für deterministische Flows mit harten Erwartungen an exakte Endpunkte. Das Muster ist klar: Wenn die Umgebung das richtige Tool bereitstellt und die Zielermittlung offen ist, agiert das Modell stark. Wenn es selbst eine konkrete URL herleiten muss, sinkt die Verlässlichkeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Der P2-Wert von 59.17 passt zum Asset-Bild: perfekte Verdichtung bei HTTP Fetch & Extract, aber deutliche Schwächen bei EU License Research, URL Construction & Fetch und Multilingual Search & Synthesis. Das Modell kann Fakten aus vorliegendem Content sauber extrahieren. Es ist aber weniger zuverlässig darin, mehrere Tool-Ergebnisse eng am Belegstand zusammenzuführen und Unsicherheit sauber zu markieren.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau dieses Verhalten prüft, halluziniert es zwar nicht und der Verifikationsstatus ist stark. Trotzdem ist der niedrige P2-Wert ein Warnsignal: Das Modell bleibt formal im sicheren Bereich, verdichtet die recherchierten Lizenzinformationen aber nicht präzise genug für Compliance-nahe Nutzung. Da global Halluzination erkannt wurde, ist das ein Sicherheitsrisiko, nicht nur ein Qualitätsmangel. In einer Tool-Pipeline untergräbt erfundener oder überdehnter Output die Beweiskette der gesamten Infrastruktur.

**Fehlerresilienz**

Im 404-Test reagiert das Modell akzeptabel. Es kommuniziert den Tool-Fehler transparent und erfindet keinen Seiteninhalt. Der P2-Wert von 60 zeigt, dass die Fehlermeldung nicht immer ideal verdichtet ist, aber das Verhalten bleibt produktionsfähig. Für Betrieb zählt hier vor allem, dass bei fehlgeschlagenem Abruf keine Ersatzfakten konstruiert werden.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Gleichzeitig liegt das Modell nur 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist für ein open-weights, lokal einsetzbares Server-Modell ein starkes Betriebsargument.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Pipelines, in denen Tool-Wahl, Abruf und strukturierte Extraktion wichtiger sind als hochpräzise Schlussverdichtung: Rechercheassistenz, technische Informationsbeschaffung, Vorverarbeitung für menschliche Freigabe. Nicht die erste Wahl für Compliance, Policy-Auslegung, mehrsprachige Evidenzsynthese oder andere Flows, in denen jedes Ergebnis eng am Tool-Beleg bleiben muss. Deploy nur mit Response-Grounding, Quellenanzeige und einem Validator auf der letzten Synthesestufe.