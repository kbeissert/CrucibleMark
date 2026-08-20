**Deployment-Urteil**

> **Erstellt am:** 19.08.2026, 23:18:50


Bedingt deployen, weil die Tool-Ausführung brauchbar ist, aber die MCP-Aufrufe nicht durchgehend valide sind und die Synthesetreue für produktive Wissens- und Compliance-Pipelines zu schwach bleibt.

**Tool-Execution-Profil**

Qwen 3.6 35B-A3B zeigt kein verlässlich agentisches Werkzeugverhalten. Es kann Tools ausführen, wenn der Pfad schon klar ist, aber es wählt sie nicht konsistent richtig. Das sieht man direkt an der Differenz zwischen **Web Search & Tool Selection**, das ohne expliziten Hinweis die Wahl zwischen Suche und Fetch prüfen soll, mit P1 35, und **URL Construction & Fetch**, das die Ableitung einer Ziel-URL und den anschließenden Abruf misst, mit P1 80. Das Modell folgt also eher einem bekannten Abrufmuster, statt situativ zu erkennen, welches Werkzeug die Aufgabe verlangt.

Positiv ist, dass **HTTP Fetch & Extract** mit P1 80 auf solide mechanische Ausführung hindeutet. Negativ ist der globale Befund **Tool-Call valide: false**. Für eine MCP-Pipeline heißt das: Die Absicht zur Tool-Nutzung ist vorhanden, aber das Protokollverhalten ist nicht robust genug für unbeaufsichtigte Orchestrierung.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur eingeschränkt. Die P2-Leistung von 45.83 ist der eigentliche Engpass. Bei **HTTP Fetch & Extract**, das präzise Fakten aus echtem Seiteninhalt verlangt, bleibt es mit P2 60 noch brauchbar. Bei **Multilingual Search & Synthesis**, also sprachübergreifender Recherche mit deutscher Zusammenfassung, ebenfalls P2 60. Für belastbare Verdichtung in produktiven Entscheidungs- oder Dokumentationspfaden reicht das nicht. **EU License Research** fällt mit Combined 26 klar ab.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot **EU License Research**, der genau dies prüft, wurde keine Halluzination erkannt. Das ist wichtig. Das Modell erfindet hier keine externen Fakten. Gleichzeitig ist P2 20 ein Warnsignal: Es bleibt zwar formal innerhalb des sicheren Rahmens, verdichtet die gewonnenen Informationen aber nur schwach. Vertrauen in die Faktentreue ist damit höher als Vertrauen in die Nutzbarkeit der Antwort.

**Fehlerresilienz**

Beim **Tool Failure Handling (404)**, das auf transparente Reaktion bei fehlgeschlagenem Abruf prüft, halluziniert das Modell keinen Ersatzinhalt. Das ist produktionsrelevant positiv. P2 60 zeigt, dass es Fehlerzustände akzeptabel kommuniziert, auch wenn die Reaktion nicht besonders klar oder handlungsleitend ausfällt. Für Betriebspipelines ist das akzeptabel, solange ein übergeordnetes System Retry- oder Fallback-Logik übernimmt.

**Betriebsprofil**

Total 58.11s pro Run: langsam.  
Call 1 1.17s, MCP-Latenz 1.33s, Call 2 7.19s: Frontload schnell, Gesamtablauf zäh.  
Kosten/Run: local. Günstig im Betrieb, aber die Laufzeit steht nicht im Verhältnis zur nur moderaten Gesamtleistung.

**Fazit & Empfehlung**

Geeignet für lokale, souveränitätsnahe Pipelines mit menschlicher Sichtkontrolle, besonders wenn Fetch-lastige Aufgaben und einfache URL-basierte Abrufe dominieren. Nicht geeignet für autonome MCP-Orchestrierung, Compliance-Workflows, dynamische Rechercheketten oder jede Pipeline, in der die korrekte Tool-Wahl und saubere Verdichtung ohne Nachprüfung sitzen müssen. Wenn Sie es einsetzen, dann als kostengünstigen lokalen Worker unter strikter Tool-Validierung und mit nachgelagerter Qualitätskontrolle.