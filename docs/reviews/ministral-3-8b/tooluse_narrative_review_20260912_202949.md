**Deployment-Urteil**

> **Erstellt am:** 12.09.2026, 20:29:49


Nicht deploy für produktive MCP-Pipelines, weil das Modell trotz brauchbarer Tool-Ausführung erfundene Inhalte als Tool-Ergebnis ausgibt und dabei keine valide Ende-zu-Ende-Vertrauensgrenze hält.

**Tool-Execution-Profil**

Ministral 3 8B zeigt auf der Ausführungsseite echte Brauchbarkeit. P1 89.17 ist für ein Edge-Modell stark, und die Einzelergebnisse zeigen, dass es Werkzeuge nicht nur mechanisch aufruft. Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Abruf prüft, wählt es das richtige Werkzeug sicher. Das spricht für situative Werkzeugwahl statt starrem Fetch-Muster. Beim URL-Construction-Test, der die Ableitung einer Ziel-URL aus Vorwissen und den anschließenden Abruf misst, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für Pfade, in denen URL-Präzision kritisch ist.

Der Haken liegt im Protokoll. Tool-Call valide: false bedeutet, dass die Pipeline trotz guter Werkzeugintention nicht auf durchgehend saubere MCP-Konformität zählen kann. Retry war nicht nötig, daher wirkt das weniger wie ein reines Formatproblem und mehr wie ein Zuverlässigkeitsbruch im Ausführungsabschluss.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 29.17 zeigt, dass das Modell gefundene Inhalte nur unzuverlässig in belastbare Antworten überführt. Das sieht man quer über die Aufgaben: EU License Research, HTTP Fetch & Extract und Multilingual Search & Synthesis enden jeweils bei P2 15. Nur beim URL-Construction-Test erreicht es mit P2 80 eine saubere Verdichtung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell. Das ist kein bloßer Qualitätsmangel, sondern ein Sicherheitsrisiko. Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als recherchierte Ergebnisse präsentiert, verliert die gesamte Infrastruktur ihre Vertrauensbasis.

**Fehlerresilienz**

Im 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt prüft, reagiert das Modell nicht produktionsreif. P2 35 wäre für sich schon schwach. Entscheidend ist der Befund Halluzination trotz 404-Fehler: True. Ein Modell, das nach einem gescheiterten Tool-Aufruf Seiteninhalt erfindet, ist für produktive Pipelines untragbar. Hier gibt es keine milde Interpretation.

**Souveränitätsprofil**

Lokal betreibbar, Apache-2.0-lizenziert und damit souverän einsetzbar. Mit 59.58 Combined liegt es 8.17 Punkte unter dem Fleet-Ø von 67.75. Das ist für lokale Bereitstellung respektabel, aber nicht stark genug, um die Vertrauensdefizite zu kompensieren.

**Fazit & Empfehlung**

Geeignet ist das Modell für lokale Assistenzsysteme mit niedriger Fallhöhe, etwa Tool-routing, Vorstrukturierung oder interne Entwürfe unter menschlicher Kontrolle. Nicht geeignet ist es für Compliance-, Recherche-, Incident-, Support- oder Dokumentationspipelines, in denen Tool-Fehler sauber offengelegt und Ergebnisse strikt aus den abgerufenen Quellen gebildet werden müssen. Wenn Sie einem Modell eigenständig eine Tool-Infrastruktur übergeben wollen, ist dieses Modell in der vorliegenden Form keine sichere Wahl.