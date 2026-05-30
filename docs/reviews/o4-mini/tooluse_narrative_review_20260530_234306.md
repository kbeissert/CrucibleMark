**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:43:06


Bedingt deploy, weil o4-mini valide Tool-Calls erzeugt und MCP-konform arbeitet, aber bei moderatem Gesamtergebnis von 62.54 einmal nachweislich Tool-Ergebnisse durch halluzinierte Inhalte ersetzt und damit das Vertrauensmodell der Pipeline verletzt.

**Tool-Execution-Profil**

Die Tool-Ausführung ist stärker als die Endantwort. Mit P1 85 zeigt das Modell, dass es Werkzeuge grundsätzlich korrekt ansteuert. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, erkennt es den richtigen Zugriffspfad sehr sicher. Das spricht gegen reines Musterfolgen und für echte Werkzeugwahl. Beim Test URL Construction & Fetch, der die korrekte Zieladresse aus Modellwissen ableiten soll, bleibt es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Die Calls selbst sind valide, also kein Protokollproblem im MCP-Sinne. Dass ein Retry nötig war, wirkt hier eher wie ein Ausführungs- oder Formatproblem unter Mehrschrittlast, nicht wie ein grundlegendes Missverständnis der Tool-Semantik.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher schwach. Mit P2 40.83 verliert o4-mini in der letzten Meile: Es ruft Informationen ab, fasst sie aber oft nicht präzise genug zusammen. Besonders sichtbar wird das bei EU License Research und Multilingual Search & Synthesis, wo die Verdichtung unzuverlässig und zu grob ausfällt. Für Pipelines, in denen die Antwort selbst ein prüfbares Arbeitsprodukt ist, ist das der eigentliche Engpass.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüfen soll, ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen stammen, liegt P2 bei 15 und es wurde Halluzination erkannt. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Fakten als Tool-Ergebnis ausgibt, unterläuft es die Kontrollkette der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparente Reaktion auf einen fehlschlagenden Tool-Call misst, bleibt o4-mini auf akzeptablem Produktionsniveau. Es halluziniert keinen Seiteninhalt trotz Fehler und kommuniziert den Ausfall grundsätzlich offen. P2 60 ist dafür ausreichend. Das Modell ist also bei sichtbaren Tool-Fehlern vorsichtig genug. Das reduziert Betriebsrisiko deutlich.

**Betriebsprofil**

Total 73.58s pro Run: langsam.  
Einzelaufrufe 4.42s und 6.85s, MCP-Latenz 1.00s: Tool-Schicht unauffällig, Gesamtdauer hoch.  
$0.047125 pro Run: günstig bis moderat.  
Im Verhältnis zur Leistung ist das Preisprofil tragbar, das Zeitprofil nicht für latenzkritische Strecken.

**Fazit & Empfehlung**

Geeignet für interne Research- und Orchestrationspipelines, in denen Tools zuverlässig gewählt werden müssen und eine nachgelagerte Validierung die Antwort prüft. Nicht geeignet für Compliance-, Lizenz-, Policy- oder andere High-Trust-Pipelines, in denen die textuelle Synthese selbst als belastbares Ergebnis gilt. Wer o4-mini einsetzt, sollte Antworten strikt gegen Tool-Outputs verifizieren und Halluzinationswächter vor den letzten Ausgabe-Schritt setzen.