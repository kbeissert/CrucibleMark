**Deployment-Urteil**

> **Erstellt am:** 12.06.2026, 18:24:06


Bedingt deploy, weil das Modell Tool-Aufrufe zuverlässig und protokollkonform ausführt, die inhaltliche Verdichtung der Tool-Ergebnisse aber nur begrenzt belastbar ist. Combined 76.33 ist für produktive Tool-Pipelines tragfähig, solange die letzte fachliche Ausformulierung nicht unkontrolliert ans Modell delegiert wird.

**Tool-Execution-Profil**

Das stärkste Signal ist die Ausführungsebene. Das Modell produziert valide Tool-Calls, brauchte keinen Retry und zeigte keine MCP-Formatprobleme. Im Test Web Search & Tool Selection, der prüft ob ohne Hinweis search statt fetch gewählt wird, erkennt es den richtigen Werkzeugtyp sicher. Das spricht gegen bloßes Musterfolgen und für echte Werkzeugwahl im Kontext.

Weniger sauber ist die Präzision im Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL misst. Dort reicht es für brauchbare, aber nicht vollständig deterministische Ausführung. Für Pipelines mit bekannter URL-Struktur ist das akzeptabel. Für Systeme, in denen falsche Endpunkte teuer oder sicherheitsrelevant sind, sollte die URL-Bildung extern vorgegeben werden.

**Synthesetreue**

Wie gut verdichtet es? Nur ordentlich. P2 von 63.33 zeigt ein Modell, das gefundene Inhalte meist korrekt zusammenzieht, aber nicht konsistent präzise genug für hochwertige Endantworten arbeitet. Das sieht man besonders bei EU License Research, wo die Rechercheausführung stark ist, die Verdichtung der Ergebnisse aber deutlich abfällt, sowie bei Multilingual Search & Synthesis, wo die deutschsprachige Zusammenfassung hinter der Suchleistung zurückbleibt.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt das Modell im sicheren Bereich. Der Content-Verification-State ist A, Halluzination wurde nicht erkannt. Das ist das zentrale Vertrauenssignal: schwache Verdichtung ja, erfundene Tool-Ergebnisse nein.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Test Tool Failure Handling (404), der transparente Reaktion auf einen fehlschlagenden Abruf misst, hat das Modell keinen Ersatzinhalt halluziniert. P2 60 zeigt, dass die Kommunikation des Fehlers nicht besonders stark formuliert ist, aber sie bleibt ehrlich. Für MCP-Pipelines ist das wesentlich wichtiger als sprachliche Eleganz.

**Souveränitätsprofil**

Lokal betreibbar und fleet-kompetent genug für souveräne Deployments. Der Sovereignty Gap liegt bei -1.37 Punkten unter dem Fleet-Ø von 67.62. Damit bleibt es nahe am Flottenschnitt, ohne Cloud-Abhängigkeit. Das ist ein brauchbares Verhältnis aus Kontrolle und Leistung.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen verlässliche Tool-Nutzung, Suchentscheidung und saubere Fehlerbehandlung wichtiger sind als hochwertige Endsynthese. Gut passend für Recherche-Orchestrierung, Compliance-Vorstufen, Retrieval mit menschlicher Nachprüfung und Systeme mit starkem Downstream-Validator. Nicht die richtige Wahl für vollautonome Antwortgeneratoren, bei denen das Modell Tool-Ergebnisse präzise, knapp und ohne Nacharbeit in entscheidungsfähige Texte überführen muss.