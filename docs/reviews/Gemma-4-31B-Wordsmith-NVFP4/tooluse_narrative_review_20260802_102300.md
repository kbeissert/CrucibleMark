**Deployment-Urteil**

> **Erstellt am:** 02.08.2026, 10:23:00


Bedingt deploy, weil die Tool-Ausführung meist stark ist, aber ein invalider Tool-Call und ein gesetztes Halluzinationssignal das Vertrauen für unüberwachte Produktionspipelines begrenzen.

**Tool-Execution-Profil**

Das Modell zeigt echte Werkzeugwahl statt bloßem Musterfolgen. Beim Test Web Search & Tool Selection, der prüft, ob ohne expliziten Hinweis erst gesucht statt direkt gefetcht werden muss, erkennt es den richtigen Zugriffspfad zuverlässig. Das ist ein starkes Signal für MCP-taugliche Orchestrierung. Beim URL-Construction-Test, der die korrekte Ableitung einer Ziel-URL aus Eigenwissen misst, arbeitet es brauchbar, aber nicht deterministisch genug für enge Automationspfade. Der Abfall von perfekter Tool-Wahl zu nur solider URL-Präzision zeigt: Es versteht, welches Tool gebraucht wird, schwächelt aber bei der exakten Parametrisierung. Dass der Tool-Call insgesamt als nicht valide markiert wurde, ist deshalb operativ wichtiger als der hohe P1-Wert. Retry war nicht erforderlich, also liegt das Problem eher in der Ausführung eines Schritts als in systematischem Protokollmissverständnis.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur mittel. P2 von 60 passt zum Muster der Einzeltests: Solide Extraktion bei HTTP Fetch & Extract, aber deutlicher Qualitätsverlust bei Multilingual Search & Synthesis, wo die deutschsprachige Verdichtung über Sprachgrenzen hinweg erkennbar unsauber wird. Für Pipelines, die aus Tool-Rohdaten belastbare Kurzbefunde erzeugen sollen, ist das zu knapp.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der genau diesen Rückfall auf Trainingswissen statt aktuelle Web-Quellen prüft, bleibt es ausreichend diszipliniert und halluziniert nicht. Das ist der wichtigste Vertrauensanker dieses Reviews. Gleichzeitig bleibt das globale Halluzinationssignal ein Sicherheitsrisiko: Sobald ein Modell erfundene Fakten als Tool-Ergebnis rahmt, wird die gesamte Tool-Infrastruktur fragwürdig.

**Fehlerresilienz**

Beim Test Tool Failure Handling (404), der transparentes Verhalten bei einem fehlschlagenden Tool-Call misst, erfindet das Modell keinen Seiteninhalt. Das ist akzeptabel für Produktion. Die P2-Qualität von 60 zeigt aber, dass die Fehlerkommunikation nicht besonders präzise oder führend ist. Es fällt also eher auf die sichere als auf die hilfreiche Seite.

**Souveränitätsprofil**

Lokal betreibbar und damit souverän einsetzbar. Zugleich ist das Modell fleet-kompetitiv genug, liegt aber 1.22 Punkte unter dem Fleet-Ø von 66.87. Für lokale Open-Weight-Infrastruktur ist das ein tragfähiger Wert, kein Ausreißer nach oben.

**Fazit & Empfehlung**

Geeignet für lokale MCP-Pipelines mit menschlicher Nachkontrolle, vor allem für Recherche, Suchschritt-Auswahl und allgemeine Tool-Orchestrierung. Nicht geeignet für Compliance-nahe, vollautomatische oder mehrsprachige Synthese-Pipelines, in denen jeder Tool-Call formal gültig und jede Verdichtung belastbar sein muss. Wer dieses Modell einsetzt, sollte strikte Tool-Call-Validierung, Output-Schema-Prüfung und eine nachgelagerte Verifikationsstufe verpflichtend vorsehen.