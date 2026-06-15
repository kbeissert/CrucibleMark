**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:19:27


Bedingt deploy, weil die Tool-Ausführung verlässlich ist, aber die Synthesetreue für produktionsnahe Wissens- und Compliance-Pipelines zu schwankend bleibt. Der kombinierte Score von 74 bestätigt Nutzbarkeit, nicht blindes Vertrauen.

**Tool-Execution-Profil**

Gemini 2.5 Pro verhält sich als Tool-Operator stark. P1 liegt bei 90, der Tool-Call war valide und ein Retry war nicht nötig. Das spricht für saubere MCP-konforme Aufrufe und geringe Integrationsreibung.

Bei **Web Search & Tool Selection**, also der Frage, ob ohne expliziten Hinweis eher Suche als direkter Fetch nötig ist, erkennt das Modell den richtigen Werkzeugtyp sicher und erreicht P1 100. Das wirkt nicht wie starres Schema-Fahren, sondern wie echte Situationswahl. Beim **URL-Construction-Test**, der prüft, ob das Modell die Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetcht, bleibt es mit P1 80 brauchbar, aber nicht deterministisch genug für fragile Endpunkte. Für orchestrierte Pipelines mit Suchschritt vor Abruf ist das Profil klar stärker als für direkte URL-Konstruktion aus implizitem Wissen.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur ordentlich. P2 liegt insgesamt bei 60. In **HTTP Fetch & Extract** und **Multilingual Search & Synthesis**, also bei strukturierter Extraktion und sprachübergreifender Verdichtung, arbeitet das Modell solide. Der Ausreißer ist **EU License Research** mit P2 20. Das ist kein Tool-Use-Problem, sondern ein Verdichtungsproblem unter Aktualitätsdruck: Es ruft Quellen ab, verdichtet sie aber nicht belastbar genug für sensible Sachverhalte.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der genau das prüft, wurde keine Halluzination erkannt und der Content-Verification-State steht auf A. Das Vertrauenssignal ist deshalb gemischt, aber wichtig: Das Modell erfindet nichts, doch es transformiert abgerufene Evidenz nicht immer in eine präzise, entscheidungstaugliche Antwort.

**Fehlerresilienz**

Im **Tool Failure Handling (404)**, also beim Test auf transparenten Umgang mit fehlgeschlagenem Abruf, reagiert Gemini 2.5 Pro produktionsgerecht. P2 80 bei ausbleibender Halluzination zeigt, dass es Fehler offen kommuniziert statt Seiteninhalt zu erfinden. Das ist für Tool-Pipelines akzeptabel und operativ wichtiger als stilistische Antwortqualität.

**Betriebsprofil**

Total 123.44s pro Run. Einzelaufrufe 8.11s und 11.54s, MCP-Latenz 0.93s. Langsam für interaktive Workflows. Kosten 0.023781 pro Run. Für Frontier-Leistung nicht teuer, aber angesichts der nur mittleren Synthesetreue kein Effizienzvorteil.

**Fazit & Empfehlung**

Geeignet für MCP-gestützte Recherche-, Routing- und Orchestrierungs-Pipelines, in denen das Modell primär Tools auswählt, Aufrufe formuliert und Ergebnisse vorsortiert. Nicht die erste Wahl für Compliance, Policy, Lizenz- oder andere Entscheidungen, bei denen die letzte Verdichtungsstufe exakt und quellentreu sein muss. Deployen, wenn ein nachgelagerter Verifikations- oder Review-Schritt die finale Antwort absichert.