**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 22:02:53


Bedingt deploy, weil das Modell Tool-Aufrufe zuverlässig und MCP-konform ausführt, aber die Synthesequalität mit Combined 75.83 nur dann tragfähig ist, wenn nachgelagerte Validierung oder enge Ausgabeformate die Verdichtung absichern.

**Tool-Execution-Profil**

Auf der Tool-Ebene ist das Modell belastbar. Es produziert valide Calls, brauchte keinen Retry und zeigte keine Protokollabweichung. Das ist für eine MCP-gestützte Pipeline die Grundvoraussetzung, und die erfüllt es.

Bei Web Search & Tool Selection, also dem Test, ob ohne ausdrücklichen Hinweis web_search statt fetch gewählt wird, handelt es klar werkzeugintelligent und nicht nur schematisch. P1 100 ist hier das starke Signal: Es erkennt den Informationsbedarf und greift zum passenden Tool. Beim URL-Construction-Test, der prüft, ob es die Ziel-URL aus eigenem Wissen ableitet und dann korrekt fetch ausführt, fällt es auf P1 80 zurück. Das spricht nicht gegen die Tool-Fähigkeit, aber gegen deterministische Präzision bei impliziter URL-Bildung. Für starre Fetch-Pipelines sollte die URL-Erzeugung daher eher im System als im Modell liegen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich, nicht verlässlich gut. P2 63.33 ist der zentrale Vorbehalt. Besonders schwach ist die Verdichtung bei EU License Research und Multilingual Search & Synthesis mit jeweils P2 40. Das Modell beschafft die Information, komprimiert sie aber nicht immer präzise genug für Compliance-, Policy- oder Mehrquellen-Workflows. Für extraktive Zusammenfassungen mit klarer Struktur ist das handhabbar. Für offene Synthese mit feinen Einschränkungen ist es zu locker.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell innerhalb der Tool-Spur. Content-Verification-State A bei gleichzeitig keiner erkannten Halluzination ist ein gutes Vertrauenssignal. Der niedrige P2-Wert heißt hier nicht, dass es erfindet, sondern dass es die beschafften Fakten nicht scharf genug verdichtet.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei einem scheiternden Tool-Aufruf misst, reagiert das Modell produktionsfähig. Es kommuniziert den Fehler statt Seiteninhalt zu erfinden. P2 80 ohne Halluzination trotz 404 ist akzeptabel für reale Pipelines, in denen externe Quellen regelmäßig ausfallen.

**Souveränitätsprofil**

Lokal betreibbar und damit für souveräne Infrastrukturen attraktiv. Leistung liegt 1.37 Punkte unter dem Fleet-Ø von 67.62. Das ist nahe genug am Flottenschnitt, um den lokalen Betrieb nicht als Qualitätsopfer erscheinen zu lassen.

**Fazit & Empfehlung**

Geeignet für lokale Recherche-, Routing- und Tool-Orchestrierungspipelines, in denen das Modell primär Quellen findet, Tools korrekt ansteuert und Ergebnisse in feste Antwortschablonen überführt. Nicht die erste Wahl für Compliance-nahe Synthese, mehrsprachige Verdichtung oder Entscheidungen, bei denen feine semantische Unterschiede aus Tool-Output sauber herausgearbeitet werden müssen. Wenn Sie URL-Bildung, Output-Schema und gegebenenfalls eine zweite Validierungsstufe systemisch absichern, ist dieses Modell ein brauchbarer produktiver Tool-Operator.