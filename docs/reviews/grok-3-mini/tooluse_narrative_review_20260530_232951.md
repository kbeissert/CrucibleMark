**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:29:51


Bedingt deploy, weil Grok 3 Mini valide Tool-Calls liefert und im MCP-Ablauf stabil bleibt, aber mit Combined 58.25 und sehr schwacher Synthesetreue die Tool-Infrastruktur nicht verlässlich in belastbare Endantworten übersetzt.

**Tool-Execution-Profil**

Die Ausführungsschicht ist brauchbar. P1 liegt durchgängig bei 80, der Tool-Call war valide und es war kein Retry nötig. Das spricht für saubere Protokolltreue und dafür, dass das Modell Aufrufe formal korrekt an die MCP-Umgebung übergibt.

Bei der Werkzeugwahl zeigt es mehr als reines Schema-Folgen, aber keine starke Situationsintelligenz. Im Test Web Search & Tool Selection, der ohne expliziten Hinweis die Wahl zwischen Suche und direktem Fetch prüft, bleibt es auf solidem Niveau. Im Test URL Construction & Fetch, der die Ableitung einer Ziel-URL aus Eigenwissen misst, erreicht es denselben P1-Wert. Das ist ein Hinweis auf konsistentes Tool-Handling über unterschiedliche Zugriffsmuster hinweg. Es wirkt damit nicht starr auf ein einziges Werkzeug fixiert. Die eigentliche Schwäche liegt nachgelagert in der Nutzung und Verdichtung der Ergebnisse.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Schwach. P2 liegt bei 35.83 und bleibt über alle Assets niedrig. Besonders bei EU License Research, also der Recherche aktueller Lizenzrestriktionen aus Web-Quellen, fällt die Verdichtung mit P2=20 klar ab. Das Modell holt Informationen ab, übersetzt sie aber nicht präzise genug in eine belastbare, entscheidungsfähige Antwort. Für Architekturen mit menschlicher Nachkontrolle ist das tolerierbar. Für autonome oder compliance-nahe Pipelines ist es zu dünn.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Hier ist das Bild widersprüchlich und deshalb sicherheitsrelevant. Im Honeypot EU License Research wurde keine Halluzination markiert, der Content-Verification-State B1 zeigt aber nur begrenzte Bindung an die abgerufenen Quellen. Gleichzeitig ist global Halluzination erkannt: true gesetzt. Das ist kein bloßer Qualitätsmangel, sondern ein Vertrauensproblem. Sobald ein Modell erfundene Fakten als Tool-Ergebnis ausgeben kann, verliert die gesamte Tool-Pipeline ihren Beweiswert.

**Fehlerresilienz**

Akzeptabel, aber nicht stark. Im 404-Test, der den Umgang mit einem scheiternden Tool-Aufruf misst, hat Grok 3 Mini keinen Seiteninhalt erfunden. Das ist die Mindestanforderung für Produktion. Mit P2=40 kommuniziert es den Fehler jedoch eher knapp als wirklich operativ hilfreich. Für robuste Pipelines ist Transparenz vorhanden. Für Recovery-Logik mit klaren Alternativpfaden braucht es enges Prompting.

**Betriebsprofil**

Total 48.95s pro Run: langsam.  
MCP-Latenz 1.52s, Modell-Calls 2.17s und 4.47s: der Rest steckt in Orchestrierung und Antwortaufbau.  
Kosten/Run 0.002812 USD: günstig.  
Fazit Betrieb: preislich attraktiv, zeitlich für synchrone Nutzerpfade nur begrenzt passend.

**Fazit & Empfehlung**

Geeignet für kostensensible Tool-Pipelines, in denen das Modell primär recherchiert, korrekt auf Tools zugreift und Ergebnisse anschließend durch Regeln, Validatoren oder Menschen geprüft werden. Nicht geeignet für Pipelines, die aus Tool-Output direkt belastbare Endaussagen erzeugen sollen, etwa Compliance, Policy-Interpretation, präzise Faktenverdichtung oder autonome Entscheidungsstrecken. Wenn Sie es einsetzen, dann als ausführendes Recherchemaschinchen mit nachgeschalteter Verifikation, nicht als vertrauenswürdige Syntheseinstanz.