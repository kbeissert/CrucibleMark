**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:40:39


Bedingt deploy, weil Gemma 4 E4B valide Tool-Calls erzeugt, nicht halluziniert und mit 74.67 insgesamt produktionsnah wirkt, die Synthesequalität aber sichtbar hinter der Tool-Ausführung zurückbleibt.

**Tool-Execution-Profil**

Das Modell ist bei Tool-Nutzung klar stärker als bei der anschließenden Verdichtung. P1 von 90 zeigt sich in der Praxis: Tool-Call war valide, ein Retry war nicht nötig, und das Modell bleibt MCP-konform. Besonders wichtig ist die Werkzeugwahl: Im Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheidet, wählt es das richtige Werkzeug sicher. Das spricht gegen starres Musterfolgen und für brauchbare Tool-Intelligenz in dynamischen Pipelines.

Weniger sauber ist die Ausführung beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen herleiten und dann abrufen kann. Mit P1 80 ist das brauchbar, aber nicht deterministisch genug für Workflows, in denen URL-Bildung geschäftskritisch ist. Für Such-, Lookup- und Retrieval-first-Pipelines ist das unkritisch. Für direkt konstruierte Fetch-Pfade sollte man Guardrails oder Vorvalidierung einziehen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 von 60 insgesamt bedeutet: Die Kernaussagen bleiben meist erhalten, aber die Verdichtung ist nicht präzise genug für extraktionsnahe Aufgaben. Das sieht man auch bei HTTP Fetch & Extract und URL Construction & Fetch, wo die Tool-Ausführung tragfähig ist, die Antwort aber nicht zuverlässig auf dem Niveau einer strikten Faktenkonsolidierung landet. Besonders schwach ist Multilingual Search & Synthesis mit P2 40. Für sprachübergreifende Recherche mit deutscher Endausgabe braucht dieses Modell enge Ausgabeformate.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Vertrauenssignal gut. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, halluziniert es nicht. Content-Verification-State A und kein Halluzinationsbefund sind für Compliance-nahe Tool-Pipelines deutlich wichtiger als ein nur mittleres P2.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf misst, bleibt das Modell sauber. Es erfindet keinen Seiteninhalt und kommuniziert den Fehlschlag nachvollziehbar. Das ist für Produktion akzeptabel. Ein Modell, das an dieser Stelle Ersatzinhalt produziert, wäre nicht einsetzbar. Gemma 4 E4B besteht diese Hürde.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Deployments attraktiv. Leistung liegt 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist ein tragbarer Abstand, wenn lokale Ausführung, Datenhoheit und kontrollierte Infrastruktur wichtiger sind als maximale Antwortqualität.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines mit klarer Tool-First-Architektur: Suche, Abruf, einfache Recherche, robuste Fehlerbehandlung und kontrollierte lokale Deployments. Nicht die richtige Wahl für Pipelines, in denen die Modellantwort selbst das Endprodukt ist, etwa präzise mehrsprachige Synthese, extraktionsnahe Berichte oder verdichtete Compliance-Outputs ohne nachgelagerte Validierung. Empfehlung: einsetzen als lokales Retrieval- und Tool-Orchestrierungsmodell, nicht als letzte Instanz für hochpräzise Ergebnisverdichtung.