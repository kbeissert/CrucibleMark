**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:20:27


Bedingt deploy, weil die Tool-Ausführung stark ist, aber Halluzination im Honeypot und ein nicht valider Tool-Call das Vertrauen für produktive MCP-Pipelines begrenzen. Der Combined-Score von 74 zeigt brauchbare Substanz, reicht aber nicht für unbewachte High-Trust-Workflows.

**Tool-Execution-Profil**

Xiaomi MiMo V2.5 Pro zeigt echte Werkzeugintelligenz. Beim Test Web Search & Tool Selection, der prüft, ob ohne Hinweis web_search statt fetch gewählt wird, erkennt es den richtigen Pfad sicher. Das spricht gegen starres Schema-Verhalten. Auch bei Multilingual Search & Synthesis und EU License Research ruft es die benötigten Werkzeuge konsequent auf.

Weniger sauber ist die Protokolltreue. Der globale Befund „Tool-Call valide: false“ ist für eine MCP-Integration relevant, weil schon kleine Format- oder Parameterfehler Orchestratoren hart scheitern lassen. Dass kein Retry erforderlich war, spricht eher gegen ein bloßes Flüchtigkeitsformat und eher für punktuelle Unschärfe in der Ausführung. Beim URL-Construction-Test, der korrekte URL-Ableitung und anschließendes Fetch misst, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Der P2-Wert von 44.17 ist der klare Schwachpunkt dieses Modells. Gute Einzelresultate bei HTTP Fetch & Extract sowie URL Construction & Fetch zeigen, dass es strukturierte Inhalte aus echten Tool-Antworten durchaus sauber zusammenziehen kann. Sobald die Aufgabe stärker nach Bewertung, Verdichtung oder mehrstufiger Zusammenführung verlangt, sinkt die Verlässlichkeit sichtbar.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht konsistent. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Trainingsstand beantwortet werden, fällt das Modell mit P2=15 und erkannter Halluzination klar durch. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Fakten als Ergebnis einer Live-Recherche ausgibt, beschädigt es die Beweiskette der gesamten Tool-Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call misst, reagiert das Modell akzeptabel. Es halluziniert keinen Seiteninhalt trotz Fehler. P2=60 ist nicht elegant, aber produktionstauglich, weil die Grundregel eingehalten wird: Fehler offenlegen statt Ersatzfakten erzeugen.

**Betriebsprofil**

Call 1: 7.01s. MCP-Latenz: 1.11s. Call 2: 23.68s. Total: 190.80s. Langsam für die gezeigte Synthesequalität. Kosten/Run: local. Preis laut Modell: $0.435 pro 1M Input-Tokens, $0.87 pro 1M Output-Tokens. Als Open-Weights-Modell wirtschaftlich vertretbar, aber die Laufzeit ist für interaktive Orchestrierung hoch.

**Fazit & Empfehlung**

Geeignet für überwachte Agenten-Pipelines, in denen Tool-Wahl, Web-Recherche und mehrsprachige Beschaffung wichtiger sind als belastbare Endverdichtung. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere Nachweispipelines, in denen das Modell strikt an Tool-Ergebnisse gebunden bleiben muss. Wenn Sie es einsetzen, dann mit hartem Output-Gating, Tool-Result-Quoting und nachgelagerter Verifikation vor jeder extern wirksamen Entscheidung.