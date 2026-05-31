**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:52:00


Bedingt deploybar, weil Gemma 4 2B valide Tool-Calls erzeugt und im Toolzugriff verlässlich wirkt, aber die Synthesequalität mit Combined 67.75 und erkannter Halluzination nicht stabil genug für faktenkritische Endausgaben ist.

**Tool-Execution-Profil**

Die operative Seite ist die klare Stärke dieses Modells. Tool-Calls sind valide, MCP-konform und ohne Retry gelaufen. Das spricht gegen ein Protokoll- oder Formatproblem und für belastbare Grundintegration in eine Tool-Pipeline. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Fetch unterscheiden lässt, wählt das Modell das richtige Werkzeug sicher. Das zeigt echte Werkzeugwahl statt bloßem Schema-Folgen. Schwächer ist es beim URL-Construction-Test, der die Ziel-URL aus Weltwissen ableiten und dann korrekt abrufen lässt. Dort reicht die Präzision für brauchbare Ausführung, aber nicht für deterministische Pipelines mit harten URL-Annahmen. Das Muster ist klar: Wenn das Tool die Unsicherheit absorbiert, arbeitet das Modell sauber. Wenn es vor dem Tool noch exakte Konstruktion leisten muss, fällt die Zuverlässigkeit.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt. Die P2-Leistung ist der eigentliche Engpass. In EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis ruft das Modell die richtigen Quellen ab, komprimiert sie aber zu flach oder verliert wichtige Details. Für produktive Systeme heißt das: Die Retrieval-Schicht kann stimmen, die Antwortschicht bleibt anfällig für Auslassungen und unpräzise Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Vertrauensbruch prüft, bleibt es im Ergebnisraum und halluziniert nicht. Das ist ein starkes Signal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko. Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnisse ausgeben kann, beschädigt es das Vertrauen in die gesamte Infrastruktur, auch wenn der konkrete Honeypot bestanden wurde.

**Fehlerresilienz**

Beim 404-Test, der transparentes Scheitern gegen erfundenen Ersatzinhalt misst, reagiert Gemma 4 2B akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler und bleibt damit grundsätzlich produktionsfähig für robuste Orchestrierung. Die Fehlerkommunikation ist nicht vorbildlich präzise, aber sie bleibt auf der sicheren Seite: lieber begrenzte Aussage als erfundene Kompensation.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Umgebungen praktisch attraktiv. Der Sovereignty Gap liegt bei -4.01 Punkten unter dem Fleet-Ø von 66.21. Damit ist das Modell im lokalen Betrieb konkurrenzfähig genug, wenn Kontrolle, Kostenhoheit und einfache Edge-Bereitstellung wichtiger sind als hohe Antworttreue.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen das Modell primär Tools auswählt, Aufrufe ausführt und Rohresultate weiterreicht oder von nachgelagerter Logik prüfen lässt. Geeignet auch für interne Recherche-Workflows mit Human-in-the-Loop. Nicht geeignet für Compliance, regulatorische Ausgaben, kundensichtbare Faktensynthesen oder jede Pipeline, in der die Modellantwort selbst als vertrauenswürdige Endverdichtung dienen soll. Hier braucht es ein stärkeres Modell oder eine harte Verifikationsschicht nach der Synthese.