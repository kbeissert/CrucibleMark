**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:13:28


Nicht deploy für produktive MCP-Pipelines, weil das Modell zwar valide Tool-Calls erzeugt, aber bei Combined 64.88 mit erkannter Halluzination das zentrale Vertrauenskriterium verletzt.

**Tool-Execution-Profil**

Qwen 3 32B kann Werkzeuge grundsätzlich bedienen. Die Tool-Calls waren valide, MCP-protokollkonform und ohne Retry ausführbar. Das spricht für eine stabile formale Integration in eine Tool-Infrastruktur. Auch bei der Werkzeugwahl zeigt das Modell echte situative Steuerung statt bloßem Schema-F: Beim Test Web Search & Tool Selection, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählte es das passende Werkzeug durchgängig korrekt. Beim Test URL Construction & Fetch, der die eigenständige Ableitung einer Ziel-URL und den anschließenden Abruf misst, bleibt es brauchbar, aber nicht präzise genug für strikt deterministische Pipelines. P1 86.67 ist damit als solides Ausführungssignal zu lesen, nicht als Freigabe für autonome Tool-Ketten.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt belastbar. P2 43.33 zeigt, dass das Modell gefundene Inhalte oft nicht sauber in präzise, quellennahe Aussagen überführt. Besonders schwach fällt das bei EU License Research und Multilingual Search & Synthesis aus. Dort bricht die Verdichtungsqualität genau in den Fällen ein, in denen aktuelle, mehrdeutige oder sprachübergreifende Informationen eng am Tool-Output gehalten werden müssten.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Nein. Beim Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, halluziniert das Modell trotz Content-Verification-State A. Das ist kein gewöhnlicher Qualitätsfehler, sondern ein Sicherheitsrisiko. Wenn ein Modell erfundene oder vorab gelernte Fakten als Ergebnis einer Tool-Recherche ausgibt, unterläuft es die Kontrolllogik der gesamten Pipeline.

**Fehlerresilienz**

Nicht produktionsreif. Beim 404-Test, der transparentes Verhalten nach einem fehlgeschlagenen Tool-Call erzwingt, kommuniziert Qwen 3 32B den Fehler nicht verlässlich, sondern halluziniert Seiteninhalt weiter. P2 35 ist hier zweitrangig. Entscheidend ist der Befund selbst: halluzinierter Ersatzinhalt trotz Tool-Fehler ist produktionskritisch ohne Ausnahme.

**Souveränitätsprofil**

Lokal betreibbar und für souveräne Setups grundsätzlich attraktiv, auch wegen Open Weights und niedriger Run-Kosten von 0.002685. Leistunglich bleibt es aber 1.37 Punkte unter dem Fleet-Ø von 67.84. Der Souveränitätsvorteil kompensiert den Vertrauensverlust in der Synthese nicht.

**Fazit & Empfehlung**

Geeignet allenfalls für assistive, menschenüberwachte Recherche- oder Vorstrukturierungs-Pipelines, in denen Tool-Ergebnisse anschließend extern validiert werden. Nicht geeignet für Compliance, Lizenzprüfung, Incident-Analysen, autonome Web-Recherche oder jede Kette, in der Tool-Output als belastbare Faktengrundlage weiterverarbeitet wird. Wer lokale Souveränität sucht, kann es als günstigen Tool-Caller prüfen. Als vertrauenswürdige Tool-Syntheseinstanz sollte es nicht eingesetzt werden.