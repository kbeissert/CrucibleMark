**Deployment-Urteil**

> **Erstellt am:** 10.07.2026, 15:01:06


Bedingt deploy, weil Qwen 3 14B valide Tool-Calls produziert und die Tool-Ebene zuverlässig bedient, aber die Synthesequalität mit Combined 65.67 nur moderat ist und eine Halluzination im Gesamtlauf das Vertrauen in unbeaufsichtigte Antwortausgabe begrenzt.

**Tool-Execution-Profil**

Auf der Ausführungsebene ist das Modell belastbar. Tool-Call valide: true und Retry erforderlich: false sprechen für saubere MCP-konforme Übergaben ohne Formatdrift. Das ist für produktive Tool-Pipelines der wichtigste erste Filter.

Bei der Werkzeugwahl zeigt es echte Situationsanpassung statt bloßem Schema-Fetch. Im Test Web Search & Tool Selection, der prüft ob ohne expliziten Hinweis web_search statt fetch gewählt wird, erreicht es P1 100. Das spricht für brauchbare Tool-Intelligenz in offenen Recherchepfaden. Beim URL-Construction-Test, der die korrekte Ziel-URL aus Modellwissen ableiten und anschließend fetch ausführen lässt, liegt es bei P1 80. Es kann also bekannte Pfade oft brauchbar konstruieren, aber nicht präzise genug für vollständig deterministische Pipelines ohne Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 41.67 ist der klare Schwachpunkt dieses Laufs. Besonders HTTP Fetch & Extract, also die strukturierte Extraktion aus realem Seiteninhalt, fällt mit P2 15 deutlich ab. Auch Multilingual Search & Synthesis bleibt mit P2 35 unter dem, was man für belastbare Downstream-Nutzung braucht. Das Modell holt Informationen, aber es komprimiert und priorisiert sie nicht stabil genug.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, bleibt es im zulässigen Korridor: Content-Verification-State A, Halluzination erkannt: False. Das ist ein gutes Vertrauenssignal für Compliance-nahe Recherche. Gleichzeitig gilt der globale Halluzinationsbefund als Sicherheitsrisiko: Wenn ein Modell irgendwo in der Pipeline erfundene Fakten als Tool-Ergebnis ausgibt, beschädigt es die Verlässlichkeit der gesamten Infrastruktur.

**Fehlerresilienz**

Akzeptabel für Produktion. Im Test Tool Failure Handling (404), der transparenten Umgang mit fehlgeschlagenem Abruf statt erfundenem Ersatzinhalt misst, liegt Qwen 3 14B bei P2 60 und halluziniert trotz 404 keinen Seiteninhalt. Es kommuniziert Fehler also grundsätzlich offen genug, um in orchestrierten Abläufen nicht sofort toxisch zu werden.

**Souveränitätsprofil**

Lokal betreibbar, kommerziell sauber lizenzierbar und damit für souveräne Deployments attraktiv. Gleichzeitig liegt es mit einem Sovereignty Gap von -0.75 Punkten unter dem Fleet-Ø von 66.55 praktisch auf Flottenniveau. Für ein lokales 14B-Dense-Modell ist das ein belastbares Betriebsprofil.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen Tool-Aufruf, Rechercheanstoß und Fehleroffenlegung wichtiger sind als hochwertige Verdichtung im letzten Antwortschritt. Gut passend für interne Recherche, Vorstufen von Agenten und überwachte Retrieval-Workflows. Nicht die richtige Wahl für Compliance-Ausgaben, Executive Summaries oder Extraktionspipelines, in denen die formulierte Endantwort ohne menschliche Prüfung direkt weiterverwendet wird. Setzen Sie es mit Antwortvalidierung, Schema-Prüfung und enger Output-Kontrolle ein.