**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:11:28


Bedingt deploy, weil die Tool-Ausführung stark und protokolltreu ist, die Synthesetreue aber mit Halluzinationsbefund nicht stabil genug für hochkritische Faktenpipelines wirkt.

**Tool-Execution-Profil**

Kimi K2.5 arbeitet im MCP-Kontext handlungsfähig. Die Tool-Calls sind valide, Retry war nicht nötig, und der P1-Wert von 90 zeigt, dass das Modell die Infrastruktur praktisch bedienen kann. Besonders stark ist Web Search & Tool Selection: In dem Test, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählt es das passende Werkzeug sicher. Das spricht für echte Werkzeugwahl statt starrem Muster.

Weniger sauber ist URL Construction & Fetch. In dem Test, der die Ziel-URL aus Vorwissen ableiten und dann korrekt abrufen lässt, erreicht es nur 80. Das ist brauchbar, aber nicht deterministisch genug für Pipelines, in denen URL-Bildung ohne Vorvalidierung zuverlässig sitzen muss. Das Profil ist damit klar: gute Orchestrierung, solide Protokolldisziplin, aber keine Präzision, auf die man bei abgeleiteten Endpunkten blind vertrauen sollte.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. P2 liegt bei 65.83. Das reicht für operative Zusammenfassungen, aber nicht für belastbare Extraktion. Der schwächste Befund kommt aus HTTP Fetch & Extract: In dem Test, der präzise Fakten wie Namen, Jahreszahlen und Versionen aus echtem Seiteninhalt zieht, fällt die Verdichtung deutlich ab. Kimi K2.5 kann also Ergebnisse beschaffen, verliert aber bei der inhaltlichen Verdichtung Genauigkeit.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research bleibt es innerhalb des abgerufenen Materials. Der Test prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden. Mit Content-Verification-State A und ohne Halluzination ist das ein gutes Vertrauenssignal. Gleichzeitig bleibt der globale Halluzinationsbefund ein Sicherheitsrisiko: Sobald ein Modell in einer Tool-Pipeline erfundene Fakten als Tool-Ergebnis ausgibt, wird die Verlässlichkeit der gesamten Infrastruktur fraglich.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparentes Verhalten bei fehlschlagendem Tool-Aufruf prüft, kommuniziert Kimi K2.5 den Fehler sauber und erfindet keinen Ersatzinhalt. Das ist der Mindeststandard für robuste Agentenpfade, und den erfüllt es.

**Betriebsprofil**

Langsam: 7.29s erster Call, 32.03s zweiter Call, 242.04s total.  
MCP-Latenz 1.02s. Der Hauptanteil liegt beim Modell, nicht beim Tooling.  
Günstig: 0.006807 USD pro Run. Preislich attraktiv, zeitlich teuer.

**Fazit & Empfehlung**

Geeignet für agentische Recherche- und Orchestrierungs-Pipelines mit Human-in-the-Loop, Tool-First-Architekturen und sauberer Nachvalidierung der extrahierten Fakten. Nicht geeignet für Compliance-, Vertrags-, Regulatorik- oder andere High-Trust-Pipelines, in denen die textuelle Verdichtung selbst als verlässlicher Endpunkt gelten muss. Wenn Sie Kimi K2.5 einsetzen, dann als Tool-Koordinator mit nachgelagerter Verifikation, nicht als letzte Instanz für faktenkritische Synthese.