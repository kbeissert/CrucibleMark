**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:29:58


Bedingt deploy: Das Modell zeigt brauchbare Tool-Ausführung, ist aber wegen erkannter Halluzination und eines nicht validen Tool-Calls nicht vertrauenswürdig genug für autonome MCP-Pipelines.

**Tool-Execution-Profil**

Ministral 3 14B versteht grundsätzlich, wann es ein Werkzeug einsetzen muss. Beim Test Web Search & Tool Selection, der prüft ob ohne Hinweis web_search statt fetch gewählt wird, trifft es die Werkzeugwahl sicher. Das spricht gegen ein rein starres Muster. Auch beim Test URL Construction & Fetch, der die Ableitung einer korrekten Ziel-URL aus Eigenwissen misst, arbeitet es meist brauchbar, aber nicht präzise genug für streng deterministische Flows. Der P1-Wert ist insgesamt solide, doch der Befund „Tool-Call valide: false“ ist im Produktionseinsatz schwerwiegend. Das Modell kann also sinnvolle Tool-Entscheidungen treffen, hält die Übergabe an die Infrastruktur aber nicht durchgängig protokollsauber.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. Die P2-Leistung bleibt mit 33.33 klar hinter der Ausführung zurück. Das Muster über die Assets ist konsistent: Fetching und Suche funktionieren häufiger als die anschließende saubere Verdichtung. Besonders kritisch ist Multilingual Search & Synthesis, das grenzüberschreitende Recherche und deutsche Zusammenfassung prüft, mit sehr niedriger Synthesequalität. Für Architekturen, in denen das Modell Tool-Ergebnisse nur weiterreichen oder knapp strukturieren soll, ist das noch handhabbar. Für analytische Endantworten nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der aktuelle Lizenzrestriktionen gegen auswendig gelerntes Wissen abgrenzt, bleibt es immerhin im richtigen Verhaltensraum und halluziniert dort nicht. Das ist ein positives Vertrauenssignal für Compliance-nahe Recherche. Es wird aber durch den globalen Halluzinationsbefund wieder relativiert. Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Ergebnisinhalt ausgibt, entsteht ein Sicherheitsrisiko für die gesamte Kette.

**Fehlerresilienz**

Hier scheitert das Modell produktionskritisch. Im Test Tool Failure Handling (404), der prüft ob ein fehlgeschlagener Abruf offen kommuniziert wird, erzeugt es trotz 404 erfundenen Seiteninhalt. Das ist keine bloße Qualitätsschwäche, sondern ein Vertrauensbruch. Transparente Fehlerkommunikation wäre akzeptabel. Halluzinierter Ersatzinhalt ist es nicht.

**Souveränitätsprofil**

Lokal betreibbar, Apache-2.0-lizenziert und damit attraktiv für souveräne Deployments. Die kombinierte Leistung liegt 6.58-Punkte unter dem Fleet-Ø von 67.75. Das ist für ein Desktop-Modell respektabel, aber nicht stark genug, um die Zuverlässigkeitsrisiken zu kompensieren.

**Fazit & Empfehlung**

Geeignet ist das Modell für lokal betriebene, kostenarme Assistenz-Pipelines mit menschlicher Kontrolle, klaren Guardrails und enger Begrenzung auf Tool-Auswahl, Recherche-Anstoß und strukturierte Vorarbeiten. Nicht geeignet ist es für autonome MCP-Orchestrierung, Compliance-Ausgaben, Fehlerpfade ohne Aufsicht oder jede Pipeline, in der Tool-Resultate als vertrauenswürdige Faktenbasis direkt weiterverarbeitet werden. Deploy nur mit hartem Response-Validation-Layer und expliziter Halluzinationsbremse.