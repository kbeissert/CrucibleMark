**Deployment-Urteil**

> **Erstellt am:** 22.06.2026, 21:36:37


Nicht deploy für MCP-gestützte Tool-Pipelines, weil bei Combined 0.00 weder valide Tool-Calls noch verwertbare Ausführungsdaten vorliegen. Die Abwesenheit von Halluzination ist hier kein Entlastungssignal, sondern nur ein Nicht-Befund.

**Tool-Execution-Profil**

Für die eigentliche Tool-Nutzung gibt es keine belastbare Produktionsfreigabe. Tool-Call valide steht auf False, zugleich fehlen für alle sechs Aufgaben P1-Werte. Damit ist nicht nachweisbar, dass das Modell MCP-konform das richtige Tool wählt, Parameter sauber setzt und den Aufruf formal korrekt abschließt.

Besonders kritisch ist die Lücke bei Web Search & Tool Selection, also dem Test, ob das Modell ohne Hinweis erkennt, dass erst gesucht und nicht direkt gefetcht werden muss. Ebenso fehlt ein verwertbarer Befund beim URL-Construction-Test, der prüft, ob das Modell eine Ziel-URL aus eigenem Wissen korrekt ableitet und dann fetch präzise ausführt. Ohne diese beiden Signale lässt sich keine Werkzeugintelligenz erkennen. In der Praxis muss man daher von einem unbestätigten, potenziell fragilen Tool-Verhalten ausgehen, nicht von agentischer Reife. Retry war nicht erforderlich, aber das hilft nicht weiter. Das Problem ist nicht Formatkosmetik, sondern fehlende Evidenz für funktionierende Ausführung.

**Synthesetreue**

Zur P2-Verdichtungsqualität liegt kein verwertbarer Nachweis vor. Damit ist offen, wie gut das Modell Tool-Ergebnisse verdichtet, widerspruchsfrei zusammenführt und von Nebensignalen trennt. Für produktive Pipelines ist das ein Kernrisiko, weil gute Reasoning-Fähigkeit ohne belastbare Ergebnisbindung nicht genügt.

Das Vertrauensurteil aus EU License Research fällt vorsichtig neutral aus. Der Honeypot prüft, ob das Modell aktuelle Lizenzrestriktionen aus Web-Quellen holt statt aus dem Training zu antworten. Halluzination erkannt steht auf False, aber Content-Verification-State und P2 sind n/a. Das heißt: kein negativer Befund, aber auch kein Beweis, dass das Modell im Tool-Ergebnis bleibt.

**Fehlerresilienz**

Beim 404-Test, der transparente Fehlerkommunikation gegen halluzinierten Ersatzinhalt prüft, wurde keine Halluzination erkannt. Das ist das einzig klar brauchbare Produktionssignal in diesem Datensatz. Ein Modell, das bei Tool-Fehlern nicht einfach Seiteninhalt erfindet, verhält sich im Störfall zumindest sicherheitsverträglich. Mehr lässt sich daraus nicht ableiten.

**Betriebsprofil**

Latenz: n/a.  
Kosten pro Run: local.  
Leistungsbezug: nicht bewertbar, da keine belastbaren Ausführungsdaten vorliegen.

**Fazit & Empfehlung**

Command A Reasoning ist in diesem Benchmark nicht als verlässliches Tool-Modell nachgewiesen. Für reine Denkarbeit ohne externe Werkzeuge mag es separat prüfenswert sein. Für produktive MCP-Pipelines mit Web-Recherche, Fetch, URL-Konstruktion und nachgelagerter Verdichtung empfehle ich es nicht. Vor einer Freigabe braucht es einen vollständigen Re-Run mit validierten Tool-Calls, messbarer Tool-Selektion und überprüfbarer Synthese aus echten Tool-Ergebnissen.