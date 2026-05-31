**Deployment-Urteil**

> **Erstellt am:** 31.05.2026, 08:52:25


Bedingt deploy, weil die Tool-Aufrufe valide sind und die Tool-Ausführung stark wirkt, das Modell aber mit erkannter Halluzination in der Synthese das Vertrauensmodell einer Tool-Pipeline verletzt.

**Tool-Execution-Profil**

Ministral 3B versteht Tool-Nutzung grundsätzlich. P1 mit 89.17 zeigt, dass es MCP-konforme Aufrufe erzeugt und die Infrastruktur technisch bedienen kann. Beim Test Web Search & Tool Selection, der prüft ob das Modell ohne Hinweis zwischen Suche und direktem Fetch unterscheidet, wählt es das richtige Werkzeug zuverlässig. Das spricht gegen reines Musterausführen und für brauchbare Werkzeugwahl im Prompt-Kontext. Beim URL-Construction-Test, der aus Eigenwissen eine Ziel-URL ableiten und dann korrekt fetchen lässt, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Pipelines mit strikt erwarteten Endpunkten.

Dass ein Retry erforderlich war, wirkt hier eher wie ein Ausführungs- oder Formatproblem als ein grundlegendes Verständnisproblem. Die validen Calls und die hohen P1-Werte sprechen nicht für Planungsversagen, sondern für Instabilität in der ersten Antwortform.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 mit 40.00 ist der klare Engpass. Das Modell kann Informationen holen, verdichtet sie aber oft nicht belastbar weiter. Das sieht man besonders bei EU License Research, Web Search & Tool Selection und Multilingual Search & Synthesis mit jeweils nur P2 15. Für produktive Pipelines heißt das: Die Retrieval-Schicht funktioniert eher als die Berichts- oder Entscheidungs-Schicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht verlässlich. Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell trotz Content-Verification-State A. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Aussagen als Ergebnis eines Tool-Laufs ausgibt, verliert die gesamte Pipeline ihre Nachvollziehbarkeit.

**Fehlerresilienz**

Hier ist das Modell akzeptabel. Im 404-Test, der transparenten Umgang mit gescheiterten Tool-Calls gegen halluzinierten Ersatzinhalt misst, kommuniziert es den Fehler offen und erfindet keinen Seiteninhalt. P2 80 in diesem Asset ist für Produktion relevant, weil Fehlersichtbarkeit wichtiger ist als glatte Sprache.

**Souveränitätsprofil**

Lokal betreibbar und damit operativ attraktiv für souveräne Setups. Die Leistung liegt jedoch 4.01 Punkte unter dem Fleet-Ø von 66.21. Das ist wettbewerbsfähig für Edge-Hardware, aber nicht stark genug, um die Vertrauenslücke in der Synthese zu kompensieren.

**Fazit & Empfehlung**

Geeignet für lokal betriebene Retrieval- und Routing-Pipelines, in denen ein nachgelagerter Validator, Schema-Checker oder ein stärkeres Modell die Endsynthese übernimmt. Nicht geeignet für Compliance-, Research- oder Entscheidungs-Pipelines, in denen die Antwort selbst als verlässliche Auswertung von Tool-Ergebnissen gelten muss. Wer nur ein kompaktes Modell für Tool-Ausführung sucht, kann es einsetzen. Wer dem Modell die letzte inhaltliche Autorität geben will, sollte es nicht freigeben.