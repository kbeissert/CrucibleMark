**Deployment-Urteil**

> **Erstellt am:** 30.05.2026, 23:38:32


Bedingt deploy, weil die Tool-Ausführung tragfähig ist, aber die Synthesetreue mit Combined 67.92 und aktiv erkannter Halluzination nicht stabil genug für vertrauenskritische Pipelines ist.

**Tool-Execution-Profil**

DeepSeek V4 Flash arbeitet auf der Ausführungsseite belastbar. P1 von 86.67, valide Tool-Calls und kein erforderlicher Retry sprechen dafür, dass das Modell MCP-konform formuliert und die Infrastruktur nicht durch Formatfehler belastet. Das ist für produktive Tool-Pipelines der erste harte Gatekeeper, und diesen besteht es.

Bei der Werkzeugwahl bleibt das Bild unvollständig, weil für Web Search & Tool Selection sowie URL Construction & Fetch keine Einzelscores vorliegen. Deshalb lässt sich nicht sauber belegen, ob das Modell situativ zwischen web_search und fetch unterscheidet oder nur einem festen Muster folgt. Aus den vorliegenden Daten lässt sich nur ableiten: Wenn es ein Tool aufruft, tut es das formal korrekt. Ob es das richtige Tool unter unklarer Aufgabenlage konsistent auswählt, ist mit diesen Ergebnissen noch nicht abgesichert.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Nur begrenzt belastbar. P2 von 51.67 ist der eigentliche Warnwert dieses Runs. Das Modell kommt also eher bis zur Datenbeschaffung als bis zur verlässlichen Verdichtung. Für Architekturen, in denen das Modell Tool-Antworten in knappe Entscheidungsgrundlagen, Compliance-Hinweise oder extrahierte Fakten übersetzen soll, ist das zu wenig Reserve.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus dem Training beantwortet werden, wurde keine Halluzination erkannt. Das ist positiv. Gleichzeitig bleibt der globale Halluzinationsflag ein Sicherheitsrisiko. In einer MCP-Pipeline ist erfundener Inhalt nicht einfach eine Qualitätsfrage. Er unterläuft die Beweisführung der gesamten Tool-Kette.

**Fehlerresilienz**

Im Test Tool Failure Handling (404), der transparenten Umgang mit einem fehlgeschlagenen Tool-Call prüft, hat das Modell keinen Ersatzinhalt halluziniert. Das ist produktionsfähig. Wenn ein Fetch scheitert, erfindet es hier keine Seite, sondern bleibt im Fehlerraum. Genau dieses Verhalten braucht man für robuste Orchestrierung.

**Betriebsprofil**

Call 1: 3.24s. MCP-Latenz: 1.37s. Call 2: 10.21s. Total: 88.90s.  
Direkte Aussage: Tool-Interaktion einzeln noch akzeptabel, Gesamtrun langsam.  
Kosten/Run: 0.000933 USD. Direkte Aussage: sehr günstig im Verhältnis zur gebotenen Tool-Ausführung, aber die lange End-to-End-Laufzeit relativiert den Preisvorteil.

**Fazit & Empfehlung**

Geeignet für kostensensitive Pipelines, in denen das Modell primär Tools korrekt anstößt, Fehler transparent meldet und ein nachgelagerter Validator die inhaltliche Verdichtung absichert. Nicht geeignet für autonome Research-, Compliance- oder Entscheidungs-Pipelines, in denen die Modellzusammenfassung selbst als verlässlicher Endzustand gilt. Wer DeepSeek V4 Flash einsetzt, sollte es als ausführenden Knoten mit strikter Verifikation behandeln, nicht als vertrauenswürdigen Synthese-Layer.