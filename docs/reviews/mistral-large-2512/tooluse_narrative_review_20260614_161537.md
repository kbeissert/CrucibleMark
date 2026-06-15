**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:15:37


Bedingt deploy, weil Mistral 3 Large valide Tool-Calls erzeugt und im MCP-Ablauf sauber arbeitet, aber die Synthesetreue mit Combined 59.71 und Halluzinationsbefund für produktive Tool-Pipelines nicht verlässlich genug ist.

**Tool-Execution-Profil**

Das Modell ist auf der Ausführungsseite klar stärker als auf der Antwortseite. P1 90 zeigt, dass es Tools korrekt anspricht und keine Protokollprobleme erzeugt. Der Befund wirkt nicht wie starres Schema-Fahren. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und Fetch prüft, erkennt es den richtigen Werkzeugtyp sicher und erreicht P1 100. Das spricht für echte Werkzeugwahl unter Unsicherheit. Beim URL-Construction-Test, der korrekte Ziel-URL und anschließenden Fetch verlangt, fällt es auf P1 80 zurück. Es kann also operativ arbeiten, ist aber bei abgeleiteten URLs nicht präzise genug für deterministische Abläufe. Retry war nicht nötig. Das Problem liegt nicht im Format, sondern in der inhaltlichen Genauigkeit nach erfolgreichem Call.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nicht gut genug für belastbare Produktionsantworten. P2 30 ist der zentrale Bremspunkt dieses Modells. Besonders schwach sind EU License Research mit P2 20, URL Construction & Fetch mit P2 15 und Multilingual Search & Synthesis mit P2 15. Das Muster ist klar: Das Modell findet Informationen oft, komprimiert sie aber unzuverlässig, lässt Präzision liegen und verliert Faktenbindung in der Endantwort.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen wirklich aus Web-Quellen statt aus Trainingswissen stammen, bleibt das Modell formal im Tool-Pfad. Content-Verification-State A und keine Halluzination in diesem Test sind ein positives Vertrauenssignal. Trotzdem bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko. In einer MCP-Pipeline zählt nicht nur, ob ein Tool aufgerufen wurde, sondern ob die Antwort strikt auf dessen Ergebnis begrenzt bleibt. Diese Grenze hält Mistral 3 Large nicht konsistent.

**Fehlerresilienz**

Beim 404-Test, der transparenten Umgang mit einem fehlschlagenden Tool-Call prüft, reagiert das Modell akzeptabel. P2 60 ist nicht stark, aber es erfindet keinen Seiteninhalt. Genau das ist für Produktion entscheidend. Ein nicht auflösbarer Abruf wird kommuniziert statt kaschiert.

**Betriebsprofil**

Call 1: 21.01s. Call 2: 8.92s. MCP-Latenz: 0.95s. Total: 185.30s. Langsam. Kosten/Run: 0.007693. Günstig bis moderat. Für die gelieferte Synthesequalität ist das Latenz-Leistungs-Verhältnis schwach.

**Fazit & Empfehlung**

Geeignet für Pipelines, in denen das Modell primär Tool-Auswahl, Request-Aufbau und einfache Fehlerbehandlung übernimmt und ein nachgelagerter Verifier die Endantwort absichert. Nicht geeignet für Compliance-, Research- oder mehrsprachige Retrieval-Pipelines, in denen die natürliche Sprachsynthese selbst als vertrauenswürdiges Produkt ausgeliefert wird. Wenn Sie Mistral 3 Large einsetzen, dann als ausführenden Agenten mit harter Ergebnisvalidierung, nicht als letzte Instanz der faktengebundenen Ausgabe.