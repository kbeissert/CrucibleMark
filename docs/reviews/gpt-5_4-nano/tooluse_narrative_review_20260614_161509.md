**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:15:09


Bedingt deploy, weil die kombinierte Leistung nur moderat ausfällt und der Tool-Call im Lauf nicht valide war, auch wenn kein Halluzinationssignal erkannt wurde. Für produktive Tool-Pipelines ist das ein Integrationsrisiko, kein Ausschlussgrund.

**Tool-Execution-Profil**

Das Kernproblem liegt nicht in erfundenen Inhalten, sondern in der operativen Ausführung. P1 mit 67.50 zeigt brauchbare Grundfähigkeit bei Tool-Nutzung, aber kein belastbares Niveau für deterministische MCP-Pipelines. Der Befund `tool_call_valid=false` wiegt hier stärker als der reine Score, weil er auf Protokoll- oder Argumentfehler im tatsächlichen Aufruf hindeutet.

Zu den Auswahltests für Web Search & Tool Selection sowie URL Construction & Fetch liegen keine verwertbaren Einzeldaten vor. Deshalb lässt sich nicht sauber belegen, ob das Modell Werkzeuge situationsgerecht auswählt oder eher einem starren Muster folgt. Für Architekten ist genau diese Lücke relevant: Ohne klare Evidenz für zuverlässige Werkzeugwahl sollte GPT-5.4 Nano nicht als autonomer Tool-Router eingesetzt werden. Positiv ist, dass kein Retry erforderlich war. Das spricht eher gegen ein triviales Formatproblem und eher für begrenzte Ausführungspräzision im Erstversuch.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Eher nur ausreichend. P2 mit 46.67 ist der schwächste Teil des Profils und signalisiert, dass das Modell gefetchte oder recherchierte Ergebnisse nicht konsistent präzise zusammenzieht. Für einfache Extraktion oder knappe Statuszusammenfassungen kann das reichen. Für Compliance, Beschaffung oder technische Entscheidungsgrundlagen ist das zu dünn.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das ist das wichtigste Vertrauenssignal im gesamten Lauf. Es zeigt Vorsicht bei aktueller Wissensabhängigkeit, auch wenn die Verdichtungsqualität selbst nicht stark ist.

**Fehlerresilienz**

Im Test Tool Failure Handling (404), der die Reaktion auf einen scheiternden Tool-Call prüft, hat das Modell keinen Seiteninhalt erfunden. Das ist für Produktion akzeptabel. Ein Modell, das bei 404 transparent bleibt, beschädigt die Tool-Infrastruktur nicht zusätzlich, wenn ein Upstream-Fehler auftritt.

**Fazit & Empfehlung**

GPT-5.4 Nano passt in kostensensitive Pipelines mit engem Aufgabenschnitt: Klassifikation, einfache Extraktion, Vorfilterung, Routing unter Aufsicht und Sub-Agent-Hilfsfunktionen. Nicht geeignet ist es als eigenständig entscheidender Recherche- oder Synthese-Agent, sobald valide Tool-Calls und präzise Verdichtung geschäftskritisch sind. Wenn Sie es einsetzen, dann hinter Schema-Validierung, mit Tool-Call-Gates und einem stärkeren Modell für Endsynthese oder Freigabe.