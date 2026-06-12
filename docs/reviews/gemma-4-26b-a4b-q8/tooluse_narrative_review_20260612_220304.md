**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:03:04


Bedingt deploy, weil es Tools zuverlässig und protokollkonform benutzt, aber die Verdichtung der Tool-Ergebnisse für produktive Entscheidungsstrecken zu ungenau bleibt. Der kombinierte Eindruck ist gut, das eigentliche Vertrauenssignal liegt hier klar stärker in P1 als in P2.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsebene belastbar. Die Tool-Calls waren valide, ein Retry war nicht nötig, und es zeigt kein MCP-Formatproblem. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis erkannt wird, dass web_search statt fetch gebraucht wird, arbeitet es mit voller Treffsicherheit. Das spricht für echte Werkzeugwahl statt starrem Abrufmuster.

Weniger stark ist es beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Fetch misst. Dort bleibt die Ausführung brauchbar, aber nicht deterministisch genug für Pipelines, die aus Modellwissen präzise URLs erwarten. Das Bild ist daher klar: gute Tool-Intelligenz bei der Wahl des richtigen Wegs, geringere Präzision bei selbst konstruierten Zugriffspfaden.

**Synthesetreue**

Wie gut verdichtet es? Nur mittel. Die Synthesis Quality von 56.67 zeigt sich auch im Asset-Breakdown: EU License Research und Multilingual Search & Synthesis landen jeweils nur bei P2=40, HTTP Fetch & Extract und URL Construction & Fetch bei P2=60. Das Modell holt die Daten, komprimiert sie aber nicht verlässlich in eine saubere, entscheidungsfeste Antwort. Für menschenbegleitete Workflows ist das akzeptabel. Für automatisierte Downstream-Nutzung ist es zu lose.

Bleibt es im Tool-Ergebnis? Ja, und das ist der wichtigere Befund. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Content-Verification-State A ist hier ein echtes Vertrauenssignal: Das Modell weicht nicht sichtbar auf vortrainiertes Wissen aus, auch wenn die abschließende Verdichtung schwach bleibt.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlgeschlagenem Tool-Call gegen erfundenen Ersatzinhalt prüft, halluziniert das Modell keinen Seiteninhalt. P2=60 zeigt, dass die Fehlerkommunikation nicht besonders präzise ist, aber sie bleibt ehrlich. Das ist die Mindestanforderung für Tool-Pipelines, und diese erfüllt das Modell.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Infrastrukturen attraktiv. Mit einem Sovereignty Gap von -1.37 Punkten unter dem Fleet-Ø von 67.62 bleibt es praktisch fleet-kompetitiv. Das ist für ein lokal laufendes, restriktiv lizenziertes Workstation-Modell ein solides Betriebsprofil.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Such- und Abrufpipelines, in denen Tool-Auswahl, gültige Calls und transparente Fehlerbehandlung wichtiger sind als perfekte Endverdichtung. Nicht die erste Wahl für Compliance-Zusammenfassungen, mehrsprachige Ergebnis-Synthese oder andere Ketten, in denen die Modellantwort selbst als belastbare Endausgabe weiterverwendet wird. Als lokaler Tool-Operator mit menschlicher Aufsicht ist es brauchbar. Als autonomer Synthese-Knoten eher nicht.