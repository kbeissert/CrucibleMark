**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:25:25


Bedingt deploy, weil Gemma 3 4B valide Tool-Calls erzeugt und in der Ausführung stark ist, aber mit erkannter Halluzination im Gesamtsystem kein vertrauenswürdiger Synthese-Endpunkt bleibt. Der Combined-Score von 65.17 ist dafür zweitrangig. Ausschlaggebend ist die Sicherheitsfrage.

**Tool-Execution-Profil**

Die Tool-Seite ist der klare Pluspunkt. Mit P1 90 zeigt das Modell, dass es MCP-konform arbeitet, valide Calls produziert und kein Retry braucht. Das spricht nicht für bloßes Format-Glück, sondern für stabile Protokolldisziplin.

Bei Web Search & Tool Selection, also dem Test ob ohne Hinweis web_search statt fetch gewählt wird, erreicht es 100. Das ist ein gutes Signal für echte Werkzeugwahl statt starrem Musterabruf. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus internem Wissen und den anschließenden Fetch prüft, fällt es auf P1 80. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, in denen die URL-Bildung selbst kritisch ist. Das Profil ist daher klar: gute Auswahl des Werkzeugtyps, nur mäßige Präzision bei selbst konstruierten Zieladressen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 40.83 zeigt, dass Gemma 3 4B gefundene Inhalte nicht zuverlässig in belastbare, knappe Ergebnisantworten überführt. Das sieht man auch in HTTP Fetch & Extract und Multilingual Search & Synthesis mit jeweils nur 15 Punkten in der Verdichtung. Das Modell kommt also an Daten heran, verliert aber beim Zusammenführen, Gewichten und Absichern.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen gezogen werden, liegt P2 bei 15 und Halluzination wurde erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Fakten als Ergebnis einer Tool-Recherche ausgibt, untergräbt es die Verlässlichkeit der gesamten Tool-Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der den Umgang mit einem fehlschlagenden Tool-Aufruf misst, bleibt das Modell immerhin transparent. Es halluziniert keinen Seiteninhalt trotz Fehler. P2 40 ist nicht stark, aber das entscheidende Produktionssignal ist positiv: Es erfindet bei Tool-Fehlern keinen Ersatzinhalt. Das ist akzeptabel und deutlich wichtiger als sprachliche Eleganz.

**Souveränitätsprofil**

Lokal betreibbar, niedrige Einstiegshürde, für souveräne Deployments praktisch. Gleichzeitig liegt das Modell mit einem Sovereignty Gap von -5.32 Punkten unter dem Fleet-Ø von 66.76. Es ist also lokal verfügbar, aber nicht fleet-kompetitiv genug, um ohne Guardrails als allgemeiner Tool-Synthesizer zu überzeugen.

**Fazit & Empfehlung**

Geeignet für lokale, kostenarme Pipelines, in denen das Modell primär Tool-Aufrufe ausführt, Suchwerkzeuge auswählt oder Rohresultate an ein zweites Prüfsystem weiterreicht. Nicht geeignet als letzter Antwortgenerator in Compliance-, Research- oder mehrsprachigen Retrieval-Pipelines, wenn die Ausgabe direkt als belastbares Tool-Ergebnis verstanden wird. Wenn Sie es einsetzen, dann als günstigen Tool-Operator mit nachgelagerter Verifikation durch ein stärkeres Modell oder durch regelbasierte Validierung.