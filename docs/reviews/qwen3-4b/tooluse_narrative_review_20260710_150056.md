**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:00:56


Bedingt deploy, weil Qwen 3 4B valide Tool-Calls produziert und im Gesamtbild brauchbare Tool-Ausführung zeigt, aber die Synthesequalität mit Halluzinationsbefund für produktive Entscheidungs- oder Compliance-Pipelines nicht stabil genug ist.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsseite klar stärker als auf der Antwortseite. Die Tool-Calls waren valide, MCP-protokollkonform und ohne Retry ausführbar. Das spricht gegen ein Formatproblem und für ein grundsätzlich sauberes Schnittstellenverhalten.

Bei Web Search & Tool Selection, also dem Test, ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erkennt Qwen 3 4B den richtigen Werkzeugtyp sicher. Das ist ein gutes Signal für dynamische Pipelines. Beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL selbst ableiten und dann per fetch abrufen kann, ist es brauchbar, aber nicht deterministisch genug. Es zeigt also echte Werkzeugwahl statt sturem Musterabruf, verliert aber Präzision, sobald es die Zieladresse selbst konstruieren muss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt verlässlich. Die P2-Leistung ist der klare Engpass: bei HTTP Fetch & Extract fällt die Extraktionspräzision deutlich ab, und bei Multilingual Search & Synthesis bricht die Verdichtung praktisch weg. Für Pipelines, in denen aus Tool-Output belastbare Kurzantworten, strukturierte Begründungen oder saubere Faktenzusammenfassungen entstehen müssen, ist das zu schwach.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen geholt werden, bleibt das Modell im Test sauber am Tool-Ergebnis. Das ist das wichtige Vertrauenssignal. Gleichzeitig ist der globale Halluzinationsbefund ein Sicherheitsrisiko: Wenn ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnisse ausgibt, untergräbt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Call prüft, reagiert Qwen 3 4B produktionsgerecht. Es kommuniziert den Fehler, statt Seiteninhalt zu erfinden. Genau dieses Verhalten ist für Betriebspipelines akzeptabel, weil der Orchestrator damit sauber weiterentscheiden kann.

**Souveränitätsprofil**

Lokal betreibbar, Apache-2.0-lizenziert und damit für souveräne Deployments operativ attraktiv. Leistungsseitig liegt es nur 0.75 Punkte unter dem Fleet-Ø von 66.55. Für ein Nano-Modell ist das ein gutes Verhältnis aus Kontrolle, Ressourcenbedarf und brauchbarer Tool-Kompetenz.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines, in denen das Modell primär Tools auswählt, Aufrufe sauber ausführt und Fehler transparent meldet. Nicht geeignet als letzte Instanz für faktenkritische Synthese, mehrsprachige Rechercheverdichtung oder Compliance-nahe Ausgaben ohne nachgelagerte Verifikation. Empfehlung: als leichter Tool-Operator oder Vorstufe in Edge- und Sovereignty-Setups einsetzen, aber die finale Antwortschicht einem stärkeren Modell oder einem strikten Validator überlassen.