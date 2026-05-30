**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:43:47


Bedingt deploy, weil GLM-5 valide Tool-Calls ohne Halluzinationsbefund erzeugt, aber die Synthesequalität mit 66.67 für toolgestützte Produktionspipelines zu ungleichmäßig bleibt.

**Tool-Execution-Profil**

Im Kern ist das Modell tool-sicher. P1 liegt bei 90, die Tool-Calls waren valide und ein Retry war nicht nötig. Das spricht für saubere MCP-Konformität im Aufrufverhalten. Besonders stark ist Web Search & Tool Selection: Im Test, der ohne expliziten Hinweis zwischen Suche und direktem Abruf unterscheiden lässt, wählt GLM-5 das richtige Werkzeug zuverlässig. Das ist ein Signal für echte Werkzeugwahl statt bloßem Schema-F.

Schwächer ist URL Construction & Fetch. Im Test, der die Ziel-URL aus internem Wissen ableiten und dann korrekt abrufen lässt, arbeitet es brauchbar, aber nicht deterministisch genug für fragile Pipelines. Es erkennt also gut, wann gesucht werden muss, ist aber weniger präzise, wenn es eine URL selbst konstruieren soll. Für dynamische Recherchepfade ist das gut. Für starre Fetch-Ketten mit hoher Adresspräzision braucht es Guardrails.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich, nicht verlässlich gut. HTTP Fetch & Extract und Tool Failure Handling (404) liegen jeweils bei 80, ebenso Multilingual Search & Synthesis in der Gesamtschau. Aber EU License Research fällt bei der Verdichtung deutlich ab. Das Muster ist klar: GLM-5 kann gefundene Inhalte zusammenziehen, verliert aber bei sensiblen, regelbasierten Themen an Präzision und Priorisierung.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Vorwissen kommen, gab es keinen Halluzinationsbefund. Das ist das wichtigere Vertrauenssignal. P2=40 zeigt keine starke Verdichtung, aber Content-Verification-State A und hallucination=false bedeuten: Es bleibt grundsätzlich im abgerufenen Material und erfindet keine Compliance-Fakten.

**Fehlerresilienz**

Akzeptabel für Produktion. Im 404-Test, der transparenten Umgang mit fehlgeschlagenem Abruf statt erfundenem Ersatzinhalt misst, kommuniziert GLM-5 den Fehler sauber. Es halluziniert keinen Seiteninhalt trotz Tool-Fehler. Genau dieses Verhalten erhält Vertrauen in die Tool-Infrastruktur aufrecht.

**Betriebsprofil**

Total 242.58s. Einzelaufrufe 12.68s und 26.75s. MCP-Latenz 1.01s. Langsam für einen Generalist in dieser Leistungsklasse. Kosten pro Run 0.007638. Günstig im Verhältnis zur gebotenen Tool-Sicherheit, aber die Laufzeit limitiert interaktive oder hochparallele Nutzung.

**Fazit & Empfehlung**

Geeignet für MCP-Pipelines, in denen korrekte Tool-Nutzung, transparente Fehlerbehandlung und Web-Recherche wichtiger sind als erstklassige Verdichtung. Gut einsetzbar für Recherche-Orchestrierung, Voranalyse und agentische Routing-Schritte mit nachgelagerter Validierung. Nicht die erste Wahl für Compliance-nahe Synthese, entscheidungsreife Zusammenfassungen oder Pipelines, die aus Tool-Output direkt belastbare Endtexte erzeugen. Hier sollte ein stärkeres Verdichtungsmodell oder ein nachgeschalteter Verifier übernehmen.