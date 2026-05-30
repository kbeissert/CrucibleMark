**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:24:56


Bedingt deploybar, aber nicht direkt in eine MCP-gestützte Tool-Pipeline, weil die Tool-Calls nicht valide im MCP-Format ankommen und der Gesamteindruck mit 47.71 klar unter Produktionsniveau bleibt.

**Tool-Execution-Profil**

Der Kernbefund liegt nicht bei Halluzination, sondern bei Protokolltreue. Mistral Small 4 beherrscht Tool-Nutzung grundsätzlich, erzeugt in diesem Setup aber das Mistral-eigene Tool-Call-Format statt MCP-kompatiblem JSON. Für eine produktive MCP-Infrastruktur ist das ein harter Integrationsfehler, weil der Orchestrator Calls nicht deterministisch parsen kann. Dass `retry_required=true` gesetzt ist, spricht daher eher für ein Formatproblem als für fehlendes Aufgabenverständnis.

Bei der Werkzeugwahl selbst lässt sich nur begrenzt Positives ableiten, weil mehrere Assets durch Parse-Fehler unbrauchbar werden. Gerade beim Test Web Search & Tool Selection, der prüft, ob das Modell ohne Hinweis zwischen Suche und direktem Fetch unterscheiden kann, fehlt damit ein belastbarer Nachweis echter Tool-Intelligenz. Auch beim URL-Construction-Test, der die eigenständige Ableitung einer Ziel-URL und anschließenden Fetch misst, gibt es keinen verwertbaren Beleg für präzise, MCP-taugliche Ausführung. Für Architekten heißt das: Das Modell wirkt nicht blind schemafixiert, aber es ist in der vorliegenden Form kein verlässlicher MCP-Akteur.

**Synthesetreue**

Wie gut verdichtet es? Schwach. Der P2-Wert von 36.67 zeigt, dass aus Tool-Ergebnissen keine konsistent starke, belastbare Verdichtung entsteht. Für Pipelines, in denen nachgelagerte Systeme auf knappe, exakte Extraktion angewiesen sind, ist das zu wenig.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist der Befund besser. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, wurde keine Halluzination erkannt. Das ist ein Vertrauenssignal. Es beweist aber nur Zurückhaltung, nicht Präzision.

**Fehlerresilienz**

Akzeptabel. Im Test Tool Failure Handling (404), der transparentes Verhalten bei fehlschlagendem Abruf prüft, hat das Modell keinen Seiteninhalt erfunden. Das ist produktionsrelevant, weil ein 404 sauber als Fehler behandelt wurde statt als Anlass für improvisierte Antwortinhalte. Damit bricht es Vertrauen nicht aktiv, auch wenn es die Pipeline operativ nicht sauber bedienen kann.

**Souveränitätsprofil**

Lokal betreibbar, open weights und damit souveränitätsstark im Deployment. Leistungsseitig bleibt es aber 5.32 Punkte unter dem Fleet-Ø von 66.76. Das ist nur dann attraktiv, wenn lokale Kontrolle, Lizenzfreiheit und niedrige Kosten höher gewichtet werden als sofortige MCP-Kompatibilität.

**Fazit & Empfehlung**

Geeignet ist Mistral Small 4 für lokale, souveräne Assistenten mit Adapter-Schicht, die das proprietäre Tool-Call-Format in MCP übersetzt und Ergebnisse eng validiert. Nicht geeignet ist es als direktes Drop-in-Modell für produktive MCP-Orchestrierung, Compliance-nahe Recherche oder präzise Extraktionspipelines. Wer dieses Modell einsetzen will, sollte es als günstigen lokalen Reasoning- und Antwortkern behandeln, nicht als verlässlichen MCP-nativen Tool-Operator.