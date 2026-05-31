**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:52:52


Bedingt deploy, weil das Modell Tools verlässlich und protokollkonform nutzt, aber die Verdichtung der Tool-Ergebnisse für produktive Wissenspipelines zu schwach bleibt. Der kombinierte Befund ist damit operativ brauchbar, aber nicht autonom vertrauenswürdig.

**Tool-Execution-Profil**

Die Tool-Ausführung ist die klare Stärke dieses Setups. Gemma 3 12B IT produziert valide Calls, brauchte keinen Retry und zeigt keine MCP-Formatprobleme. Das ist für eine lokale Tool-Pipeline ein belastbares Basissignal.

Bei **Web Search & Tool Selection**, also dem Test, ob ohne expliziten Hinweis zwischen Suche und direktem Fetch unterschieden wird, wählt das Modell das richtige Werkzeug sicher. Das spricht gegen bloßes Schema-Folgen und für brauchbare Werkzeugwahl in offenen Aufgaben. Beim **URL Construction & Fetch**, also der Ableitung einer korrekten Ziel-URL aus eigenem Wissen, ist es dagegen nur solide. Es kann die URL oft brauchbar konstruieren, aber nicht präzise genug für deterministische Flows mit geringer Fehlertoleranz. Das Muster ist klar: gute Tool-Intelligenz bei der Auswahl, etwas weniger Präzision bei der Vorbereitung des Calls.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt gut. Die P2-Leistung bleibt über fast alle Assets flach. Das Modell holt Informationen aus Tools, komprimiert sie dann aber zu grob, lässt Details liegen oder formuliert nicht eng genug an der Quelle. Für einfache Antwortobjekte reicht das. Für Compliance, Recherche-Memos oder extraktionsnahe Übergaben an Folgesysteme reicht es nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Urteil deutlich besser. Im **EU License Research**-Honeypot, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen stammen, bleibt das Modell auf dem Tool-Pfad. Keine erkannte Halluzination, Content-Verification-State A. Das schützt die Infrastrukturvertrauensbasis, auch wenn die Zusammenfassung selbst zu knapp bleibt.

**Fehlerresilienz**

Bei Tool-Fehlern reagiert das Modell akzeptabel für Produktion. Im **Tool Failure Handling (404)**-Test, der transparenten Umgang mit fehlgeschlagenen Abrufen gegen erfundenen Ersatzinhalt prüft, halluziniert es keinen Seiteninhalt. Die Antwort bleibt damit systemehrlich. Das ist wichtiger als Eleganz in der Formulierung.

**Souveränitätsprofil**

Lokal betreibbar und praktisch nutzbar. Der Combined-Score liegt 4.01 Punkte unter dem Fleet-Ø von 66.21. Damit ist das Modell im souveränen Betrieb konkurrenzfähig genug, wenn lokale Ausführung, kontrollierte Gewichte und geringe externe Abhängigkeit wichtiger sind als maximale Antwortgüte.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen das Modell Tools auslösen, Ergebnisse einholen und Fehler sauber offenlegen soll. Gut passend für interne Assistenten, Recherche-Vorstufen, Routing und kontrollierte Fetch-Workflows. Nicht die richtige Wahl für Pipelines, in denen die modellseitige Synthese bereits veröffentlichungsreif, compliance-tauglich oder extraktionsgenau sein muss. Dann braucht es ein stärkeres Modell für die letzte Verdichtungsstufe oder einen nachgelagerten Verifikationsschritt.