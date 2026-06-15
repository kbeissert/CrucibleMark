**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:07:44


Bedingt deploy, weil es valide Tool-Calls erzeugt und im Tool-Pfad meist kompetent arbeitet, aber mit Halluzination im Honeypot und nur moderater Gesamttreue kein verlässliches Vertrauensniveau für kritische MCP-Pipelines erreicht.

**Tool-Execution-Profil**

Die operative Stärke liegt klar in der Tool-Ausführung. P1 81.67 zeigt, dass das Modell MCP-konforme Aufrufe meist korrekt bildet. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis das richtige Recherchewerkzeug gewählt wird, erkennt es den Bedarf für web_search sehr sicher. Das spricht gegen reines Call-Schema-Abspulen und für echte Werkzeugwahl. Beim Test URL Construction & Fetch, der die eigenständige Herleitung der Ziel-URL und den anschließenden Abruf misst, bleibt es brauchbar, aber weniger präzise. Die Auswahlintelligenz ist also stärker als die deterministische Ausführung im letzten Schritt.

Retry war erforderlich. Das wirkt hier eher wie ein Robustheitsproblem in der Interaktion als ein grundsätzliches Verständnisdefizit. Da die Tool-Calls am Ende valide waren, ist das kein Protokollbruch, aber ein Warnsignal für Pipelines mit engem Timeout- oder Ein-Schuss-Budget.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 40.83 ist der eigentliche Bremsklotz dieses Modells. Es kann Inhalte aus Fetch und Search zwar einsammeln, verdichtet sie aber oft nicht belastbar genug für Produktionsantworten. Das Muster ist deutlich: HTTP Fetch & Extract funktioniert sauber, aber bei EU License Research und Multilingual Search & Synthesis bricht die Verdichtungsqualität stark ein. Für reine Extraktion ist das akzeptabel. Für entscheidungsreife Zusammenfassungen nicht.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein, nicht zuverlässig. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, fiel es mit P2 15 und erkannter Halluzination durch. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vortrainierte Fakten als Ergebnis einer Tool-Recherche ausgibt, untergräbt es die Vertrauenskette der gesamten Infrastruktur.

**Fehlerresilienz**

Beim 404-Test, der transparentes Verhalten bei Tool-Fehlern prüft, bleibt das Modell auf der akzeptablen Seite. Es hat keinen Seiteninhalt erfunden und den Fehlschlag im Kern korrekt behandelt. P2 60 ist nicht elegant, aber produktionsfähig. Transparente Fehlerkommunikation ist vorhanden.

**Souveränitätsprofil**

Lokal betreibbar und damit souverän einsetzbar. Leistungsseitig liegt es jedoch 1.37 Punkte unter dem Fleet-Ø von 67.84. Das ist nah genug für lokale Deployments mit Compliance- oder Datenhaltungsdruck, aber kein Beleg für überlegene lokale Wirtschaftlichkeit bei diesem Risikoprofil.

**Fazit & Empfehlung**

Geeignet für lokale, souveräne Tool-Pipelines mit menschlicher Kontrolle, wenn der Schwerpunkt auf Tool-Selektion, Abruf und Vorstrukturierung liegt. Nicht geeignet für Compliance, Policy, Lizenz- oder andere High-Trust-Pipelines, in denen die Antwort nach Tool-Nutzung als verifizierte Synthese gelten muss. Wer dieses Modell einsetzt, sollte die Ausgabe strikt auf Tool-Zitate, Feldextraktion oder nachgelagerte Validierung begrenzen.