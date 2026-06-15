**Deployment-Urteil**

> **Erstellt am:** 14.06.2026, 16:15:01


Bedingt deploy, weil die Tool-Ausführung stark wirkt, aber der invalide Tool-Call trotz ausbleibender Halluzination das Vertrauen in eine unbeaufsichtigte MCP-Pipeline begrenzt. Der Combined-Score von 77.50 ist produktionsfähig, aber nicht freihändig.

**Tool-Execution-Profil**

GPT-5.5 zeigt ein belastbares Tool-Use-Grundprofil. P1 von 90.00 spricht dafür, dass das Modell Werkzeuge grundsätzlich zielführend einsetzt und mehrstufige Abläufe versteht. Kritisch bleibt der Befund `tool_call_valid=false`: Das Problem liegt nicht im inhaltlichen Verständnis, sondern in der Protokolltreue des Aufrufs. Für MCP-Pipelines ist genau das relevant, weil ein semantisch richtiger Plan an einem formal falschen Call scheitern kann.

Zu Web Search & Tool Selection und URL Construction & Fetch fehlen asset-scharfe Einzelwerte. Deshalb lässt sich nicht sauber belegen, ob GPT-5.5 aktiv zwischen Such- und Abrufwerkzeugen differenziert oder nur ein starkes Standardmuster ausführt. Der Gesamtbefund spricht eher für vorhandene Werkzeugintelligenz als für starres Schema. Für deterministische Produktionspfade bleibt aber ein Adapter oder Validator vor dem Tool-Dispatch sinnvoll.

**Synthesetreue**

Wie gut verdichtet es Tool-Ergebnisse? Solide, aber nicht auf Frontier-Niveau, das man für hochverdichtete Analysten- oder Compliance-Ausgaben erwarten würde. P2 von 66.67 zeigt, dass GPT-5.5 Ergebnisse brauchbar zusammenführt, aber bei Präzision, Gewichtung oder knapper Faktensicherung nicht durchgehend scharf genug arbeitet.

Bleibt es im Tool-Ergebnis oder weicht es auf Training aus? Im Honeypot EU License Research, der prüft, ob aktuelle Lizenzrestriktionen aus Web-Quellen statt aus Trainingswissen beantwortet werden, blieb es vertrauenswürdig. `Halluzination erkannt: false` ist hier das entscheidende Signal. Das Modell erfindet in diesem kritischen Test keine Quelle und keine Aktualität.

**Fehlerresilienz**

Im 404-Test, der transparentes Verhalten bei einem fehlschlagenden Tool-Aufruf prüft, halluziniert GPT-5.5 keinen Ersatzinhalt. Das ist für Produktion akzeptabel. Ein Modell darf an einem fehlenden Dokument scheitern. Es darf nur nicht so tun, als hätte es eines gesehen. Diese Grenze hält GPT-5.5 ein.

**Betriebsprofil**

Call 1: 32.20s  
MCP-Latenz: 0.94s  
Call 2: 19.36s  
Total: 314.99s  

Langsam.  
Preis: $5.0/1M Input, $30.0/1M Output.  
Teuer bis sehr teuer für ein Modell, das zusätzliche Guardrails für Tool-Validierung braucht.

**Fazit & Empfehlung**

Geeignet für hochwertige, überwachte Tool-Pipelines mit komplexer Planung, langem Kontext und klarer Fehlerbehandlung. Nicht die erste Wahl für streng deterministische MCP-Orchestrierung, bei der jeder Tool-Call ohne Nachbearbeitung formal sitzen muss. Deployen, wenn Sie Call-Validation, Schema-Repair und Output-Checks bereits in der Infrastruktur haben. Nicht deployen als unbeaufsichtigten Kern für Compliance-nahe oder transaktionskritische Tool-Ketten.