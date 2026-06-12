**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:23:08


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber die Tool-Calls nicht durchgängig valide waren und die Synthesequalität für verlässliche Endausgaben nur auf mittlerem Produktionsniveau liegt.

**Tool-Execution-Profil**

Das Modell zeigt operative Tool-Kompetenz. Der P1-Wert von 88.33 spricht dafür, dass es Werkzeugnutzung grundsätzlich versteht und Aufgaben in einer MCP-Pipeline aktiv in Richtung Ausführung bringt. Kritisch ist der Gegenbefund, dass der Tool-Call nicht valide war. Das ist kein kosmetischer Fehler, sondern ein Integrationsrisiko: Ein Modell kann die richtige Absicht haben und trotzdem am Protokoll oder am Call-Schema scheitern.

Zu den Tests für Web Search & Tool Selection sowie URL Construction & Fetch liegen keine Einzelergebnisse vor. Deshalb lässt sich nicht sauber trennen, ob die Stärke aus echter Werkzeugwahl stammt oder aus einem robusten Standardmuster bei naheliegenden Aufrufen. Für Architekten ist genau das die offene Flanke. Ohne diese Sicht bleibt unklar, ob das Modell in dynamischen Pipelines selbstständig zwischen Suche und direktem Fetch unterscheiden kann. Positiv ist immerhin, dass kein Retry erforderlich war. Das spricht eher gegen ein persistentes Formatproblem und eher für einen einzelnen Validitätsmangel im Ablauf.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Der P2-Wert von 63.33 reicht für knappe, brauchbare Zusammenfassungen, aber nicht für Pipelines, in denen feine Unterschiede, Randbedingungen oder Compliance-Details in der Endantwort präzise erhalten bleiben müssen. Das Modell kann Ergebnisse zusammenziehen, aber nicht mit der Konstanz, die man für hochwertige Entscheidungsunterstützung erwartet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Der Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Modellgedächtnis kommen, zeigt keinen Halluzinationsbefund. Das ist das wichtigere Vertrauenssignal. Es gibt hier keinen Hinweis, dass das Modell erfundene oder vortrainierte Fakten als Tool-Ergebnis ausgibt.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Aufruf misst, halluzinierte das Modell keinen Seiteninhalt. Das ist für Produktion akzeptabel. Wenn ein Fetch scheitert, ist kontrolliertes Eingeständnis des Fehlers der richtige Modus. Dieses Modell hält diese Linie.

**Souveränitätsprofil**

Lokal betreibbar und fleet-kompetitiv. Der Combined-Score liegt 1.37 Punkte unter dem Fleet-Ø von 67.62. Damit liefert es im sovereign Setup keine bloße Ausweichlösung, sondern eine real nutzbare lokale Option.

**Fazit & Empfehlung**

Geeignet für lokale Recherche-, Retrieval- und Assistenzpipelines, in denen Tool-Nutzung wichtiger ist als perfekte Endverdichtung und in denen ein nachgelagerter Validator Tool-Calls prüft. Nicht die erste Wahl für Compliance-, Legal- oder Executive-Summary-Strecken, in denen die Antwort selbst ohne menschliche Kontrolle belastbar sein muss. Wer lokal deployen will und MCP orchestrationseitig absichert, kann es produktiv einsetzen. Ohne Call-Validierungsschicht sollte es nicht direkt an kritische Tools gelassen werden.