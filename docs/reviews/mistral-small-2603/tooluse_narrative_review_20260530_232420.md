**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:20


Bedingt deploy: Das Modell halluziniert in diesem Lauf nicht, ist aber für MCP-gestützte Produktion ohne Adapter nicht direkt geeignet, weil die Tool-Calls nicht valide im erwarteten Protokollformat ankommen und der Gesamteindruck mit 47.71 klar schwach bleibt.

**Tool-Execution-Profil**

Das Kernproblem ist nicht fehlender Tool-Wille, sondern fehlende MCP-Protokolltreue. Mistral Small 4 produziert laut Modellkontext sein eigenes Tool-Call-Schema statt MCP-JSON. Das erklärt `tool_call_valid=false` und `retry_required=true`. Für den Produktionseinsatz ist das ein Formatproblem mit operativer Wirkung, nicht nur ein Schönheitsfehler: Der Orchestrator kann den Aufruf nicht sicher ausführen.

Bei der Werkzeugwahl lässt sich deshalb nur eingeschränkt Intelligenz nachweisen. Die Tests Web Search & Tool Selection, die prüfen, ob ohne Hinweis zwischen Suche und direktem Abruf unterschieden wird, und URL Construction & Fetch, die saubere URL-Ableitung plus Abruf messen, liefern hier keine verwertbaren Einzelwerte. Das Muster spricht eher dafür, dass das Modell Tool-Nutzung grundsätzlich versteht, aber an der Schnittstelle zur MCP-Infrastruktur scheitert. Für Architekten heißt das: Mit einem Prompt- oder Middleware-Adapter ist ein zweiter Versuch sinnvoll. Ohne Adapter bleibt die Pipeline fragil.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. Der P2-Wert von 36.67 zeigt, dass aus abgerufenen Informationen keine verlässlich präzise, belastbare Verdichtung entsteht. Für produktive Pipelines ist das relevant, weil die letzte Meile nicht der Abruf, sondern die saubere Zusammenführung der Resultate ist.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen kommen, wurde keine Halluzination erkannt. Das ist ein gutes Vertrauenssignal. Es ist aber kein Freibrief, weil der Test wegen der Tool-Formatprobleme kein vollständiges Verifikationsbild liefert.

**Fehlerresilienz**

Im 404-Test, der transparenten Umgang mit scheiternden Tool-Aufrufen prüft, hat das Modell keinen Seiteninhalt erfunden. Das ist für Produktion akzeptabel. Wenn ein Tool fehlschlägt, ist ehrliche Fehlerkommunikation deutlich wichtiger als aggressive Vervollständigung. Mistral Small 4 hält diese Grenze ein.

**Souveränitätsprofil**

Lokal betreibbar und lizenzseitig attraktiv. In der lokalen souveränen Flotte bleibt die Leistung aber begrenzt: -5.32 Punkte unter dem Fleet-Ø von 66.76. Das Modell erfüllt damit den Souveränitätsvorteil stärker als den Qualitätsanspruch.

**Fazit & Empfehlung**

Geeignet für souveräne, kostenarme Pipelines mit eigener Adapter-Schicht, in denen Tool-Aufrufe normiert und Antworten nachvalidiert werden. Nicht geeignet für MCP-native Deployments, in denen das Modell selbst korrekt formatierte Calls und belastbare Endverdichtung liefern muss. Wer lokale Kontrolle priorisiert und ein Gateway zwischen Modell und MCP setzt, kann es als günstigen Generalisten prüfen. Für Compliance-, Recherche- oder entscheidungsnahe Tool-Pipelines ohne solche Schutzschichten würde ich es nicht freigeben.