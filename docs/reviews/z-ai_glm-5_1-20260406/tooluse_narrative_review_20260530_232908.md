**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:29:08


Bedingt deploybar, weil GLM 5.1 valide Tool-Calls produziert und im Toolzugriff stark ist, aber die Synthesequalität mit P2 59.17 zu oft hinter dem Produktionsmaßstab für vertrauenswürdige Tool-Pipelines zurückbleibt. Der gesetzte Halluzinationsbefund ist dabei als Sicherheitswarnsignal zu lesen, auch wenn die konkreten Tool-Use-Assets überwiegend sauber wirken.

**Tool-Execution-Profil**

Die Werkzeugausführung ist die klare Stärke dieses Modells. Mit P1 90 ruft es Tools zuverlässig und MCP-konform auf; der Tool-Call war valide und ein Retry war nicht nötig. Das spricht gegen ein Protokoll- oder Formatproblem.

Bei Web Search & Tool Selection, also dem Test ob ohne Hinweis search statt fetch gewählt wird, trifft GLM 5.1 die Werkzeugwahl sicher und erreicht P1 100. Das ist ein Signal für echte Tool-Intelligenz und nicht nur für starres Befolgen eines Schemas. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Eigenwissen prüft, fällt es mit P1 80 etwas ab. Es kann also recherchieren und passende Werkzeuge wählen, ist aber bei deterministischer URL-Bildung nicht präzise genug für fragile Fetch-Pipelines.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. Die P2-Leistung zeigt ein wiederkehrendes Muster: HTTP Fetch & Extract und Multilingual Search & Synthesis sind brauchbar, aber bei EU License Research und Web Search & Tool Selection bricht die Verdichtung deutlich ein. Das Modell findet Informationen, fasst sie aber nicht konstant präzise, priorisiert oder quellentreu genug zusammen.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, ist das Vertrauenssignal gemischt. Positiv ist: keine Halluzination erkannt, Content-Verification-State A. Negativ ist: P2 40. Das Modell bleibt also eher im abgerufenen Material, verarbeitet es aber nicht sauber genug. Da global ein Halluzinationsbefund vorliegt, bleibt ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgibt, wird die gesamte Tool-Infrastruktur angreifbar.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei scheiterndem Tool-Call misst, erreicht GLM 5.1 P2 80 und halluziniert keinen Seiteninhalt. Es kommuniziert Fehlschläge also grundsätzlich offen, statt Ersatzfakten zu erfinden. Genau dieses Verhalten ist in produktiven Pipelines erforderlich.

**Betriebsprofil**

Call 1: 9.61s. Call 2: 41.74s. MCP-Latenz: 0.77s. Total: 312.72s. Das ist langsam. Kosten pro Run: 0.014060. Das ist günstig bis moderat, aber die Laufzeit steht nicht im Verhältnis zur nur mittleren Syntheseleistung.

**Fazit & Empfehlung**

Geeignet für Pipelines, in denen Tool-Auswahl, Web-Recherche und robuste Fehlerbehandlung wichtiger sind als hochwertige Endverdichtung, etwa als Recherche- oder Retrieval-Schicht mit nachgelagerter Verifikation. Nicht geeignet als alleinige letzte Instanz für Compliance, Policy, Lizenz- oder andere entscheidungsnahe Ausgaben, bei denen die Antwort den Tool-Befund exakt und knapp repräsentieren muss. Wenn Sie GLM 5.1 einsetzen, dann mit enger Antwortvalidierung und idealerweise einem zweiten Modell oder Regelsystem für die finale Synthese.