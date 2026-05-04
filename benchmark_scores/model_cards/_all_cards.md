# Model Cards – Alle Modelle

### Dolphin Mistral NeMo
**Entwickler:** Cognitive Computations (Eric Hartford) · **Herkunft:** USA · **Fokus:** instruction-following

Dolphin Mistral NeMo ist ein von Cognitive Computations feinabgestimmtes Mistral-NeMo-Modell, das auf unzensierten, vielseitigen Instruktionsdaten trainiert wurde. Ziel ist ein hilfreicher Assistent ohne eingebaute Inhaltsbeschränkungen, der komplexe Anweisungen präzise befolgt und offen auf heikle Themen eingeht.

**Stärken:** Sehr gehorsames Instruktions-Following ohne eingebaute Inhaltssperren · Gute Allround-Sprachfähigkeiten dank Mistral-NeMo-Basis (12B Parameter, 128k Kontext) · Lokal betreibbar und vollständig open-weights, geeignet für datenschutzsensible Umgebungen
**Einschränkungen:** Fehlende Sicherheitsfilter können zur Generierung schädlicher oder problematischer Inhalte führen · Kein spezialisiertes Reasoning- oder Coding-Training; schwächer als dedizierte Modelle in diesen Bereichen

---

### Ministral 3B/14B Abliterated (Q8_0)
**Entwickler:** Mistral AI (Base) / Community Abliteration · **Herkunft:** France · **Fokus:** general

Mistral-basiertes Modell aus Frankreich, chirurgisch von Sicherheitsfiltern befreit (Abliteration). Stärken liegen in Instruction-Following, mehrsprachiger Verarbeitung und offener Inhaltsgenerierung ohne Verweigerungsverhalten. Entwickelt für Nutzer, die unzensierte Antworten ohne Guardrails benötigen.

**Stärken:** Kein Verweigerungsverhalten durch Abliteration – antwortet auf sensible Anfragen ohne Ausweichen · Kompaktes GGUF Q8_0-Format für effiziente lokale Ausführung mit hoher Quantisierungsqualität · Solide Mehrsprachigkeit und Instruction-Following auf Basis der Mistral-Architektur
**Einschränkungen:** Abliteration kann Modellkohärenz und Faktentreue in Randbereichen leicht verschlechtern · Keine eingebauten Sicherheitsfilter – ungeeignet für Produktionsumgebungen mit unbekannten Nutzern

---

### Hermes 4 14B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** instruction-following

Hermes 4 ist ein Instruction-Following-Modell von Nous Research (USA), feinabgestimmt auf einem kuratierten Datensatz für präzises Folgen von Anweisungen, Rollenspiel und agentenbasierte Aufgaben. Es kombiniert starke Gesprächsfähigkeit mit reduzierter Zensur durch gezieltes Fine-Tuning.

**Stärken:** Starkes Instruction-Following mit hoher Präzision bei komplexen Anweisungen · Für agentenbasierte und Tool-Use-Szenarien optimiert · Reduzierte Überrefusal durch gezieltes Uncensored-Fine-Tuning auf kuratierten Datensätzen
**Einschränkungen:** Als 14B-Modell bei sehr komplexen Mehrschritt-Reasoning-Aufgaben hinter größeren Modellen zurück · Q4_K_M-Quantisierung kann bei präzisen numerischen oder logischen Aufgaben zu leichten Qualitätseinbußen führen

---

### Claude Haiku 4.5
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** instruction-following

Claude Haiku 4.5 ist Anthropics schnellstes und kompaktestes Modell der Claude-4-Generation, entwickelt für latenzarme, kosteneffiziente Anwendungen. Es kombiniert starkes Instruction-Following mit verbesserter Reasoning-Fähigkeit und eignet sich besonders für Echtzeit-Interaktionen, Klassifikation und leichtgewichtige Agenten-Aufgaben.

**Stärken:** Sehr niedrige Latenz und hoher Durchsatz für Echtzeit-Anwendungen · Kosteneffizient bei hohem Anfragevolumen · Solides Instruction-Following und präzise Kurzantworten
**Einschränkungen:** Geringere Tiefe bei komplexen mehrstufigen Reasoning-Aufgaben im Vergleich zu Claude Sonnet oder Opus · Eingeschränkte Leistung bei sehr langen, kontextintensiven Dokumentenanalysen

---

### Claude Opus 4.5
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Opus 4.5 von Anthropic (USA) ist das leistungsstärkste Modell der Claude-4-Generation, trainiert auf komplexes Reasoning, nuanciertes Schreiben und agentic Tasks. Es wurde entwickelt, um anspruchsvolle Mehrschritt-Aufgaben, wissenschaftliche Analyse und autonome Agenten-Workflows zuverlässig zu bewältigen.

**Stärken:** Herausragende Leistung bei komplexen Reasoning- und Analyseaufgaben mit langen Kontexten · Optimiert für agentic Workflows und Multi-Step-Aufgaben mit hoher Zuverlässigkeit · Starke Fähigkeiten in nuanciertem, kohärentem Langform-Schreiben und Instruktionsbefolgung
**Einschränkungen:** Nur über Anthropic API verfügbar, kein lokaler Betrieb möglich · Höhere Latenz und Kosten im Vergleich zu kleineren Claude-Modellen, was Echtzeit-Anwendungen einschränken kann

---

### Claude Opus 4.6
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Opus 4.6 ist Anthropics leistungsstärkstes Modell der Opus-Linie, entwickelt für komplexe Reasoning-, Analyse- und Kreativaufgaben. Es zeichnet sich durch tiefes Kontextverständnis, nuancierte Instruktionsbefolgung und hohe Zuverlässigkeit bei anspruchsvollen Aufgaben aus.

**Stärken:** Herausragende Leistung bei komplexen Reasoning- und Analyseaufgaben · Sehr hohes Kontextverständnis und Fähigkeit zur Nuancierung in langen Gesprächen · Stark optimiert für agentenbasierte Workflows und mehrstufige Aufgabenplanung
**Einschränkungen:** Nur über Anthropics Cloud-API verfügbar, kein lokaler Betrieb möglich · Höhere Latenz und Kosten im Vergleich zu kleineren Claude-Modellen (z.B. Haiku, Sonnet)

---

### Claude Opus 4.7
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Opus 4.7 ist Anthropics leistungsstärkstes Modell der Claude-4-Generation, entwickelt in den USA mit Fokus auf komplexes Reasoning, nuanciertes Schreiben und agentic Tasks. Es kombiniert hohe Instruktionstreue mit starker Kontextverarbeitung und ist für anspruchsvolle Mehrschritt-Aufgaben ausgelegt.

**Stärken:** Sehr starkes Reasoning bei komplexen, mehrstufigen Aufgaben · Hohe Qualität bei langen, strukturierten Texten und nuanciertem Schreiben · Optimiert für agentic Workflows und Multi-Step-Orchestrierung
**Einschränkungen:** Nur über Anthropic API verfügbar, kein lokaler Betrieb möglich · Höhere Latenz und Kosten im Vergleich zu kleineren Claude-Modellen

---

### Claude Sonnet 4.5
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Sonnet 4.5 von Anthropic (USA) ist ein leistungsstarkes Allround-Modell der Claude-4-Generation, optimiert für komplexe Reasoning-Aufgaben, präzises Instruction-Following und agentenbasierte Workflows. Es kombiniert hohe Antwortqualität mit vertretbarer Latenz und richtet sich an anspruchsvolle Produktivanwendungen.

**Stärken:** Starkes Reasoning und mehrstufiges Problemlösen · Zuverlässiges Instruction-Following auch bei komplexen, langen Prompts · Gut geeignet für agentenbasierte und Tool-Use-Szenarien
**Einschränkungen:** Nur über Anthropic-API verfügbar, kein lokaler Betrieb möglich · Wissenstand begrenzt auf Trainingsdaten-Cutoff; aktuelle Ereignisse erfordern externe Tools

---

### Claude Sonnet 4.6
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Sonnet 4.6 von Anthropic (USA) ist ein leistungsstarkes Allround-Modell der Claude-4-Generation, optimiert für komplexe Reasoning-Aufgaben, präzises Instruction-Following und nuanciertes Schreiben. Es kombiniert hohe Antwortqualität mit vertretbarer Latenz und richtet sich an anspruchsvolle Produktiv-Anwendungen.

**Stärken:** Starkes analytisches Reasoning und strukturiertes Problemlösen · Präzises und nuanciertes Instruction-Following auch bei komplexen Vorgaben · Hohe Qualität bei langen, kohärenten Textgenerierungen und Zusammenfassungen
**Einschränkungen:** Ausschließlich über Anthropic-API verfügbar, kein lokaler Betrieb möglich · Kann bei sehr aktuellen Ereignissen nach dem Trainings-Cutoff keine verlässlichen Informationen liefern

---

### Codestral
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** coding

Codestral ist Mistral AIs spezialisiertes Code-Modell aus Frankreich, trainiert auf über 80 Programmiersprachen. Es glänzt bei Code-Vervollständigung, Debugging und Erklärungen. Entwickelt, um Entwickler mit schnellen, präzisen Code-Ausgaben zu unterstützen.

**Stärken:** Hervorragende Code-Vervollständigung und Fill-in-the-Middle (FIM) für viele Sprachen · Breite Sprachabdeckung mit über 80 Programmiersprachen inkl. Python, JS, Rust, Go · Schnelle Inferenz bei gleichzeitig hoher Code-Qualität dank optimierter Architektur
**Einschränkungen:** Nur über Mistral-API verfügbar, keine öffentlichen Gewichte für lokalen Betrieb · Schwächer bei komplexen Reasoning-Aufgaben außerhalb des Code-Kontexts

---

### DeepSeek R1 8B
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** reasoning

DeepSeek R1 8B ist ein chinesisches Open-Weights-Reasoning-Modell von DeepSeek. Es wurde entwickelt, um durch sichtbares Chain-of-Thought-Denken komplexe Schlussfolgerungen, Mathematik und Logikaufgaben zu lösen. Stärken liegen in strukturiertem Denken und STEM-Aufgaben bei kompakter Modellgröße.

**Stärken:** Sichtbares Chain-of-Thought-Reasoning mit <thinking>-Blöcken ermöglicht nachvollziehbare Lösungswege · Starke Leistung bei Mathematik, Logik und STEM-Aufgaben relativ zur Modellgröße · Lokal betreibbar auf Consumer-Hardware dank 8B-Parametergröße
**Einschränkungen:** Thinking-Prozess kann sehr ausführlich und langsam sein, was bei einfachen Aufgaben ineffizient ist · Zensur bei politisch sensiblen Themen mit China-Bezug (z.B. Tiananmen, Taiwan) ist im Modell verankert

---

### DeepSeek V3.1 671B
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** general

DeepSeek V3.1 ist ein chinesisches 671-Milliarden-Parameter-Modell mit Mixture-of-Experts-Architektur. Es wurde auf breiten multilingualen Daten trainiert und glänzt bei Reasoning, Coding und Instruktionsbefolgung. Ziel war ein leistungsstarkes Open-Weights-Modell auf Augenhöhe mit proprietären Frontier-Modellen.

**Stärken:** Sehr starke Leistung bei Coding- und Mathematik-Aufgaben · Effiziente MoE-Architektur mit hoher Kapazität bei vergleichsweise geringem Inferenz-Aufwand · Gute mehrsprachige Fähigkeiten, insbesondere Englisch und Chinesisch
**Einschränkungen:** Kann bei politisch sensiblen Themen mit Bezug zu China zensierte oder ausweichende Antworten liefern · Lokaler Betrieb der vollen 671B-Variante erfordert erhebliche Hardware-Ressourcen (mehrere High-End-GPUs)

---

### DeepSeek V3.2
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** general

DeepSeek V3.2 ist ein chinesisches Frontier-Modell von DeepSeek, trainiert auf breiten Wissens- und Reasoning-Aufgaben. Es zeichnet sich durch starke Coding-, Mathematik- und Sprachverständnisfähigkeiten aus und wurde entwickelt, um westliche Top-Modelle bei deutlich geringeren Trainingskosten zu erreichen.

**Stärken:** Starke Leistung bei Coding- und Mathematikaufgaben · Sehr gutes Preis-Leistungs-Verhältnis im Vergleich zu Konkurrenzmodellen · Breites Allgemeinwissen mit guter mehrsprachiger Kompetenz
**Einschränkungen:** Unterliegt chinesischer Zensur bei politisch sensiblen Themen (z.B. Tiananmen, Taiwan) · Als V3.2 möglicherweise noch nicht vollständig dokumentiert – Architekturdetails gegenüber V3 unklar

---

### Dolphin Mistral NeMo
**Entwickler:** Eric Hartford (Cognitive Computations) / Mistral AI · **Herkunft:** USA / France · **Fokus:** instruction-following

Dolphin Mistral NeMo ist ein uncensored Finetuning des Mistral-NeMo-12B-Basismodells durch Eric Hartford. Ziel war ein gehorsames, zensurfreies Assistenzmodell für Entwickler und Forscher. Stärken liegen in offener Instruktionsbefolgung, Rollenspiel und kreativen Aufgaben ohne inhaltliche Einschränkungen.

**Stärken:** Sehr hohe Instruktionstreue ohne eingebaute Inhaltsbeschränkungen · Gute Leistung bei kreativen und rollenspielbezogenen Aufgaben · Kompaktes 12B-Modell mit starker Allround-Performance, lokal effizient betreibbar
**Einschränkungen:** Fehlende Sicherheitsfilter können bei sensiblen Anwendungsfällen problematisch sein · Kann bei komplexen Mehrschritt-Reasoning-Aufgaben hinter größeren Modellen zurückbleiben

---

### Gemini 2.5 Flash
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemini 2.5 Flash ist Googles effizientes Multimodal-Modell der 2.5-Generation, entwickelt für schnelle, kosteneffektive Inferenz bei hoher Qualität. Stärken liegen in Reasoning, Code, langen Kontextfenstern (1M Token) und multimodaler Verarbeitung. Zielt auf skalierbare Produktionsanwendungen.

**Stärken:** Sehr großes Kontextfenster von bis zu 1 Million Token · Optionales Chain-of-Thought-Reasoning (Thinking-Modus) per API aktivierbar · Starke multimodale Fähigkeiten (Text, Bild, Audio, Video, Code)
**Einschränkungen:** Nur über Google-Cloud-API nutzbar, keine lokale Ausführung möglich · Wie alle Flash-Varianten qualitativ unterhalb des schwereren Gemini 2.5 Pro bei komplexen Reasoning-Aufgaben

---

### Gemini 2.5 Pro
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** reasoning

Gemini 2.5 Pro ist Googles leistungsstärkstes Reasoning-Modell (Stand 2025), entwickelt für komplexe Analyse-, Coding- und Mehrschritt-Aufgaben. Es unterstützt sehr lange Kontextfenster (bis 1 M Token), optionales Chain-of-Thought und erzielt Spitzenwerte in Mathematik- und Science-Benchmarks.

**Stärken:** Sehr starkes mathematisches und wissenschaftliches Reasoning mit optionalem Extended Thinking · Extrem großes Kontextfenster (bis zu 1 Million Token) für Dokumentenanalyse und lange Konversationen · Herausragende Coding-Fähigkeiten inkl. komplexer Multi-File-Projekte und Debugging
**Einschränkungen:** Ausschließlich über Google-Cloud-API verfügbar, keine lokale Ausführung möglich · Latenz im Thinking-Modus deutlich erhöht; bei einfachen Aufgaben oft überdimensioniert

---

### Gemini 3 Flash Preview
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemini 3 Flash Preview ist Googles schnelles Multimodal-Modell der dritten Generation, entwickelt für latenzarme, kosteneffiziente Anwendungen. Stärken liegen in schneller Verarbeitung langer Kontexte, multimodalen Eingaben und alltäglichen Reasoning-Aufgaben. Als Preview-Version ist die Leistung noch nicht final.

**Stärken:** Sehr niedrige Latenz bei hohem Durchsatz, geeignet für Echtzeit-Anwendungen · Starke multimodale Fähigkeiten (Text, Bild, Audio, Video) · Effiziente Verarbeitung sehr langer Kontextfenster
**Einschränkungen:** Preview-Status bedeutet Leistungsschwankungen und mögliche API-Instabilität · Schwächer als größere Gemini-Varianten bei komplexen mehrstufigen Reasoning-Aufgaben

---

### Gemma 3 12B
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 3 12B ist ein Open-Weights-Modell von Google DeepMind, trainiert auf multilingualen und multimodalen Daten. Es zielt auf effiziente lokale Nutzung bei starker Instruction-Following-Qualität. Stärken liegen in Textverstehen, Reasoning und Mehrsprachigkeit bei moderatem Ressourcenbedarf.

**Stärken:** Starkes Instruction-Following durch gezieltes Fine-Tuning (Gemma-IT-Variante) · Effizient lokal betreibbar – läuft auf Consumer-Hardware mit ausreichend VRAM · Solide Mehrsprachigkeit und gutes Textverstehen über diverse Domänen hinweg
**Einschränkungen:** Kontextfenster und Reasoning-Tiefe hinter größeren Frontier-Modellen (z.B. Gemini 1.5 Pro) zurück · Neigt bei komplexen mehrstufigen Aufgaben zu Vereinfachungen oder Auslassungen

---

### Gemma 3 4B
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 3 4B ist ein kompaktes Open-Weights-Modell von Google DeepMind, trainiert auf mehrsprachigen und multimodalen Daten. Es eignet sich für Instruction-Following, einfache Reasoning-Aufgaben und Textzusammenfassungen. Entwickelt als effizientes, lokal betreibbares Modell für Entwickler und Forscher mit begrenzten Ressourcen.

**Stärken:** Sehr geringer Ressourcenbedarf – läuft auf Consumer-Hardware und mobilen Geräten · Solides Instruction-Following für ein 4B-Modell · Mehrsprachige Fähigkeiten mit Unterstützung von über 35 Sprachen
**Einschränkungen:** Begrenzte Reasoning-Tiefe bei komplexen mehrstufigen Aufgaben im Vergleich zu größeren Modellen · Kontextfenster und Faktenwissen stoßen bei langen oder spezialisierten Anfragen schnell an Grenzen

---

### Gemma 4 26B
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 26B ist ein Open-Weights-Modell von Google DeepMind aus den USA. Es wurde als leistungsfähiges Allround-Modell für Instruction-Following, Reasoning und multilinguale Aufgaben entwickelt. Stärken liegen in effizienter lokaler Ausführung und solider Sprachverarbeitung bei moderatem Ressourcenbedarf.

**Stärken:** Effizient lokal betreibbar mit vergleichsweise geringem Hardwarebedarf für die Modellgröße · Solide Instruction-Following-Fähigkeiten durch gezieltes Fine-Tuning · Breite multilinguale Unterstützung und gute allgemeine Sprachverarbeitung
**Einschränkungen:** Schwächere Leistung bei komplexen mehrstufigen Reasoning-Aufgaben im Vergleich zu größeren Frontier-Modellen · Konservatives Sicherheitsfiltering kann bei legitimen Anfragen zu übermäßiger Ablehnung führen

---

### Gemma 4 2B
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 2B ist ein kompaktes Open-Weights-Modell von Google DeepMind, trainiert auf allgemeinen Sprachaufgaben mit Fokus auf Effizienz und lokale Nutzbarkeit. Es eignet sich für Instruction-Following, einfache Textgenerierung und Edge-Deployments, wo Ressourcen begrenzt sind.

**Stärken:** Sehr geringer Ressourcenbedarf, ideal für lokale und Edge-Deployments · Solide Instruction-Following-Fähigkeiten für ein 2B-Modell · Open-Weights ermöglichen vollständige lokale Kontrolle und Anpassung
**Einschränkungen:** Begrenzte Reasoning-Tiefe und Kontextverarbeitung aufgrund der geringen Modellgröße · Schwächer bei komplexen mehrschrittigen Aufgaben, Mathematik und Code im Vergleich zu größeren Modellen

---

### GPT-4o Mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-4o Mini ist ein kompaktes Modell von OpenAI (USA), das auf Effizienz und breite Einsetzbarkeit ausgelegt ist. Es bietet starke Instruction-Following-Fähigkeiten, solide Mehrsprachigkeit und gute Reasoning-Leistung bei deutlich niedrigeren Kosten als GPT-4o – gedacht als leistungsfähige Standardlösung für alltägliche Aufgaben.

**Stärken:** Sehr kosteneffizient bei guter Antwortqualität für Standardaufgaben · Schnelle Inferenz mit niedrigen Latenzen, geeignet für Echtzeit-Anwendungen · Solides Instruction-Following und Mehrsprachigkeit über viele Sprachen hinweg
**Einschränkungen:** Deutlich schwächer als GPT-4o bei komplexen Reasoning-, Mathematik- und Coding-Aufgaben · Kein lokaler Betrieb möglich – vollständige Abhängigkeit von OpenAIs Cloud-Infrastruktur

---

### GPT-4o
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-4o ist OpenAIs multimodales Flaggschiff-Modell (USA, 2024), das Text, Bild und Audio nativ verarbeitet. Es wurde für schnelle, kosteneffiziente Allround-Leistung entwickelt und überzeugt durch starkes Instruction-Following, Reasoning und natürliche Gesprächsführung über Modalitäten hinweg.

**Stärken:** Native Multimodalität: verarbeitet Text, Bild und Audio in einem einzigen Modell · Starkes Instruction-Following mit präzisen, kontextbewussten Antworten · Hohe Geschwindigkeit und Kosteneffizienz im Vergleich zu GPT-4 Turbo
**Einschränkungen:** Keine öffentlichen Gewichte – vollständig cloud-gebunden, keine lokale Nutzung möglich · Wissens-Cutoff begrenzt Aktualität; bei sehr aktuellen Ereignissen ohne Tool-Nutzung unzuverlässig

---

### GPT-5
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-5 ist OpenAIs Flaggschiff-Modell aus den USA, trainiert auf breiten multimodalen Datensätzen mit Fokus auf Reasoning, Instruktionsbefolgung und komplexe Aufgaben. Es vereint starke Sprachkompetenz, Code- und Analysefähigkeiten und soll menschliche Expertise in vielen Domänen erreichen oder übertreffen.

**Stärken:** Sehr starkes Reasoning und mehrstufiges Problemlösen über diverse Domänen hinweg · Hohe Instruktionstreue und konsistente Qualität bei komplexen, langen Aufgaben · Breite multimodale Fähigkeiten (Text, Bild, Code, Daten)
**Einschränkungen:** Ausschließlich über OpenAI-API verfügbar, keine lokale Ausführung oder Gewichtszugang möglich · Genaue Architektur, Trainingsdetails und Parameterzahl sind nicht öffentlich dokumentiert

---

### Grok 3 Mini
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** reasoning

Grok 3 Mini ist ein kompaktes Reasoning-Modell von xAI (USA), entwickelt als effizientere Alternative zu Grok 3. Es wurde auf logisches Schlussfolgern, Mathematik und strukturierte Problemlösung optimiert und richtet sich an Nutzer, die starke Reasoning-Fähigkeiten bei geringerer Latenz und niedrigeren Kosten benötigen.

**Stärken:** Starke Leistung bei mathematischen und logischen Reasoning-Aufgaben · Geringere Latenz und Kosten im Vergleich zum vollständigen Grok-3-Modell · Unterstützt optionales Chain-of-Thought-Denken (Thinking-Modus per API aktivierbar)
**Einschränkungen:** Nur über die xAI-API bzw. Grok-Plattform nutzbar, keine lokale Ausführung möglich · Als kompaktes Modell bei sehr komplexen, wissensintensiven oder kreativen Aufgaben schwächer als das vollständige Grok-3-Modell

---

### Grok 3
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** general

Grok 3 ist das Flaggschiff-Modell von xAI (USA), trainiert auf einem großen Datensatz inklusive Echtzeit-X-Plattformdaten. Stärken liegen in Reasoning, Mathematik und aktuellem Weltwissen. Entwickelt als direkte Konkurrenz zu GPT-4 und Claude mit Fokus auf unzensierte, direkte Antworten.

**Stärken:** Starke Reasoning- und Mathematikfähigkeiten, insbesondere mit aktiviertem Thinking-Modus · Zugang zu aktuellen Informationen über X/Twitter-Datensatz und Echtzeit-Websuche · Hohe Leistung bei komplexen mehrstufigen Aufgaben und wissenschaftlichen Fragestellungen
**Einschränkungen:** Ausschließlich über xAI-API und Grok-Weboberfläche verfügbar, keine lokale Nutzung möglich · Gelegentlich übermäßig ausführliche Antworten; Qualität kann bei sehr spezifischen Nischenbereichen hinter spezialisierten Modellen zurückbleiben

---

### Grok 4.1 Fast Reasoning
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** reasoning

Grok 4.1 Fast Reasoning ist ein Reasoning-Modell von xAI (USA), das auf schnelle Chain-of-Thought-Inferenz ausgelegt ist. Es kombiniert strukturiertes Schlussfolgern mit reduzierter Latenz und richtet sich an Anwendungsfälle, die analytische Tiefe bei vertretbarer Antwortgeschwindigkeit erfordern.

**Stärken:** Schnelle Reasoning-Inferenz mit reduzierter Latenz gegenüber vollständigen Thinking-Modellen · Strukturiertes mehrstufiges Schlussfolgern bei mathematischen und logischen Aufgaben · Integration in das xAI-Ökosystem mit Echtzeit-Datenzugang über Grok-Plattform
**Einschränkungen:** Nur über xAI-API/Cloud verfügbar, kein lokaler Betrieb möglich · Als spezialisiertes Fast-Reasoning-Modell potenziell schwächer bei kreativen oder offenen Generierungsaufgaben als Vollmodelle

---

### Grok 4 Fast (Non-Reasoning)
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** general

Grok 4 Fast (Non-Reasoning) ist ein schnelles, cloud-basiertes Sprachmodell von xAI (USA), entwickelt für latenzarme Anwendungen ohne aktivierten Chain-of-Thought-Modus. Stärken liegen in schnellen Antwortzeiten, allgemeinem Instruction-Following und der Integration in das X-Ökosystem.

**Stärken:** Sehr niedrige Latenz durch optimierten Fast-Inference-Modus · Starkes allgemeines Instruction-Following ohne Reasoning-Overhead · Integration in das X/Twitter-Ökosystem mit Echtzeit-Datenzugang
**Einschränkungen:** Kein Chain-of-Thought verfügbar – schwächere Leistung bei komplexen mehrstufigen Reasoning-Aufgaben · Ausschließlich über xAI-Cloud-API nutzbar, keine lokale Ausführung möglich

---

### Hermes 3 8B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** instruction-following

Hermes 3 8B ist ein von Nous Research feinabgestimmtes Modell auf Basis von Llama 3.1 8B. Es wurde auf einem kuratierten Datensatz für präzises Instruction-Following, Rollenspiel und agentenbasierte Aufgaben trainiert. Stärken liegen in langen Kontexten, Funktionsaufrufen und reduzierter Übervorsicht.

**Stärken:** Starkes Instruction-Following mit reduzierter Ablehnung harmloser Anfragen · Gute Leistung bei Funktionsaufrufen und strukturierten Ausgaben (JSON, Tool-Use) · Effektiv für Rollenspiel- und agentenbasierte Szenarien trotz kompakter 8B-Größe
**Einschränkungen:** Als Finetuning auf Llama 3.1 8B begrenzte Rohkapazität gegenüber größeren Modellen bei komplexem Reasoning · Reduzierte Sicherheitsfilter können bei sensiblen Themen zu unerwünschten Ausgaben führen

---

### Hermes 4 14B (Q4_K_M GGUF)
**Entwickler:** NousResearch · **Herkunft:** USA · **Fokus:** instruction-following

Hermes 4 14B ist ein von NousResearch (USA) feingetuntes Sprachmodell, das auf starkes Instruction-Following, strukturierte Ausgaben und Agenten-Workflows ausgelegt ist. Es basiert auf einem leistungsfähigen Basismodell und wurde durch RLHF und synthetische Daten auf präzise, hilfreiche Antworten optimiert. Die GGUF-Variante Q4_K_M ermöglicht effizienten lokalen Betrieb.

**Stärken:** Sehr gutes Instruction-Following mit präziser Befolgung komplexer Anweisungen · Starke Unterstützung für strukturierte Ausgaben (JSON, Funktionsaufrufe, Agenten-Frameworks) · Effizient lokal betreibbar durch quantisiertes GGUF-Format (Q4_K_M) mit geringem VRAM-Bedarf
**Einschränkungen:** Als 14B-Modell bei sehr komplexen Mehrschritt-Reasoning-Aufgaben schwächer als größere Modelle · Feintuning-Daten von NousResearch sind nicht vollständig dokumentiert, was Bias-Analyse erschwert

---

### Ministral 3B/14B Abliterated (Q8_0 GGUF)
**Entwickler:** Mistral AI (base model) / mradermacher (GGUF conversion & abliteration) · **Herkunft:** France · **Fokus:** instruction-following

Mistral-basiertes Modell in GGUF-Format (Q8_0), abliteriert durch mradermacher. Abliteration entfernt Refusal-Verhalten durch gezielte Gewichtsmanipulation. Geeignet für unzensierte Instruktionsausführung. Stärken liegen in Mehrsprachigkeit und kompakter Effizienz typischer Mistral-Architektur.

**Stärken:** Keine eingebauten Refusal-Mechanismen durch Abliteration – folgt Anweisungen ohne themenbasierte Verweigerung · Hohe Quantisierungsqualität (Q8_0) mit minimalem Qualitätsverlust gegenüber FP16 · Effizient lokal betreibbar dank GGUF-Format (llama.cpp-kompatibel)
**Einschränkungen:** Abliteration kann Sicherheitsfilter vollständig entfernen, was missbräuchliche Nutzung erleichtert und den Einsatz in produktiven Umgebungen einschränkt · Kein offiziell unterstütztes Modell – Qualität und Verhalten hängen von der Abliterations-Implementierung eines Drittanbieters ab

---

### Llama 3.3 70B Versatile
**Entwickler:** Meta · **Herkunft:** USA · **Fokus:** general

Llama 3.3 70B Versatile ist ein Open-Weights-Modell von Meta (USA), trainiert auf mehrsprachigen und vielfältigen Textdaten. Es überzeugt durch starkes Instruction-Following, solide Reasoning-Fähigkeiten und breite Aufgabenabdeckung. Meta entwickelte es als leistungsstarke, frei nutzbare Alternative zu proprietären Modellen.

**Stärken:** Starkes Instruction-Following über viele Aufgabentypen hinweg · Gute Reasoning- und Analysefähigkeiten für ein 70B-Modell · Frei verfügbare Gewichte ermöglichen lokalen, datenschutzkonformen Betrieb
**Einschränkungen:** Kontextfenster und Langdokument-Verarbeitung schwächer als bei spezialisierten Modellen · Kann bei sehr komplexen mehrstufigen Reasoning-Aufgaben hinter dedizierten Thinking-Modellen zurückbleiben

---

### Magistral Medium
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** reasoning

Magistral Medium ist Mistral AIs erstes dediziertes Reasoning-Modell, entwickelt in Frankreich. Es wurde für komplexe mehrstufige Schlussfolgerungen, mathematische Aufgaben und strukturiertes Denken trainiert. Stärken liegen in logischer Analyse, präzisen Antworten und mehrsprachigem Reasoning, insbesondere auf Europäisch.

**Stärken:** Starkes mehrstufiges Reasoning und logische Schlussfolgerungen · Solide mathematische und analytische Fähigkeiten · Mehrsprachige Kompetenz mit besonderem Fokus auf europäische Sprachen
**Einschränkungen:** Nur über Mistral-API verfügbar, keine lokale Ausführung möglich · Als neueres Reasoning-Modell noch weniger Community-Benchmarks und Praxiserfahrungen als etablierte Konkurrenten

---

### Magistral Small
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** reasoning

Magistral Small ist Mistral AIs kompaktes Reasoning-Modell aus Frankreich, entwickelt für strukturiertes Schlussfolgern und komplexe Aufgaben mit niedrigerer Latenz. Es kombiniert Chain-of-Thought-Fähigkeiten mit der Effizienz eines kleineren Modells und richtet sich an Anwendungsfälle, die schnelles, nachvollziehbares Denken erfordern.

**Stärken:** Strukturiertes mehrstufiges Schlussfolgern (Chain-of-Thought) · Geringere Latenz und Kosten im Vergleich zu größeren Reasoning-Modellen · Starke Mehrsprachigkeit, insbesondere europäische Sprachen
**Einschränkungen:** Nur über Mistral-API verfügbar, keine lokale Ausführung möglich · Als kleineres Modell bei sehr komplexen Reasoning-Ketten hinter größeren Varianten wie Magistral Medium zurück

---

### Llama 4 Scout 17B
**Entwickler:** Meta · **Herkunft:** USA · **Fokus:** general

Llama 4 Scout ist Metas erstes Mixture-of-Experts-Modell der Llama-4-Generation mit 17B aktiven Parametern und 16 Experten. Es wurde für effizientes Instruction-Following, multimodale Eingaben und langen Kontext (10M Token) entwickelt und übertrifft vergleichbare Open-Weights-Modelle in Reasoning und Sprachverständnis.

**Stärken:** Extrem langer Kontextfenster von bis zu 10 Millionen Tokens · Effiziente MoE-Architektur: hohe Leistung bei vergleichsweise geringem Rechenaufwand · Multimodale Fähigkeiten (Text und Bild als Eingabe)
**Einschränkungen:** Als MoE-Modell höherer Speicherbedarf für alle Expertengewichte trotz geringer aktiver Parameter · Multimodale Ausgabe (Bildgenerierung) nicht unterstützt – nur Textausgabe

---

### MiniMax M2.7
**Entwickler:** MiniMax · **Herkunft:** China · **Fokus:** general

MiniMax M2.7 ist ein chinesisches Mixture-of-Experts-Modell mit 2,7 Billionen Gesamtparametern, entwickelt für starke Mehrsprachigkeit, langes Kontextverständnis und allgemeine Aufgaben. Es zielt auf wettbewerbsfähige Leistung bei Reasoning, Coding und Instruktionsbefolgung mit effizienter MoE-Architektur.

**Stärken:** Sehr großes MoE-Modell mit hoher Parameterkapazität bei effizienter Inferenz · Starke Mehrsprachigkeit mit besonderem Fokus auf Chinesisch und Englisch · Langes Kontextfenster für umfangreiche Dokument- und Dialogverarbeitung
**Einschränkungen:** Als chinesisches Modell potenziell eingeschränkte oder zensierte Antworten zu politisch sensiblen Themen · Sehr hohe Hardwareanforderungen für lokales Deployment aufgrund der Modellgröße

---

### MiniMax M2.7
**Entwickler:** MiniMax · **Herkunft:** China · **Fokus:** general

MiniMax M2.7 ist ein chinesisches Sprachmodell von MiniMax, entwickelt für allgemeine Sprach- und Reasoning-Aufgaben. Es zielt auf starke Mehrsprachigkeit, Instruktionsbefolgung und Konversationsfähigkeit ab und positioniert sich als leistungsfähiges Allround-Modell im chinesischen KI-Ökosystem.

**Stärken:** Starke Mehrsprachigkeit mit besonderem Fokus auf Chinesisch und Englisch · Solide Instruktionsbefolgung für konversationelle und aufgabenorientierte Szenarien · Kompetitives Allround-Profil für Text-Generierung und Zusammenfassung
**Einschränkungen:** Gewichte nicht öffentlich verfügbar, daher keine lokale oder private Nutzung möglich · Begrenzte unabhängige Benchmarking-Daten verfügbar, Leistung in Nischen-Domänen schwer einschätzbar

---

### Ministral 3B 14B
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Ministral 3B von Mistral AI (Frankreich) ist ein kompaktes Edge-Modell, das für effiziente lokale Ausführung auf ressourcenbeschränkter Hardware optimiert wurde. Es kombiniert starkes Instruction-Following mit niedrigem Speicherbedarf und eignet sich für On-Device-Inferenz, eingebettete Systeme und latenzarme Anwendungen.

**Stärken:** Sehr geringer Speicher- und Rechenaufwand bei akzeptabler Antwortqualität · Gut geeignet für Edge- und On-Device-Deployment ohne Cloud-Abhängigkeit · Solides Instruction-Following für ein Modell dieser Größenklasse
**Einschränkungen:** Deutlich schwächere Reasoning- und Wissenstiefe im Vergleich zu größeren Modellen · Begrenzte Kontextfenstergröße und reduzierte Mehrsprachigkeitsleistung gegenüber größeren Mistral-Varianten

---

### Ministral 3B
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Ministral 3B ist ein kompaktes Sprachmodell von Mistral AI (Frankreich), optimiert für effiziente Edge- und On-Device-Nutzung. Es wurde entwickelt, um leistungsstarke Inferenz bei minimalem Ressourcenverbrauch zu ermöglichen. Stärken liegen in schneller Antwortzeit, Instruction-Following und mehrsprachiger Verarbeitung bei geringem Speicherbedarf.

**Stärken:** Sehr geringer Ressourcenbedarf – ideal für lokale und Edge-Deployments · Solides Instruction-Following trotz kompakter Modellgröße · Mehrsprachige Kompetenz, insbesondere für europäische Sprachen
**Einschränkungen:** Begrenzte Reasoning-Tiefe und Kontextverarbeitung im Vergleich zu größeren Modellen · Schwächere Leistung bei komplexen mehrstufigen Aufgaben oder langen Dokumenten

---

### Mistral Large
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Large ist das Flaggschiff-Modell des französischen KI-Unternehmens Mistral AI. Es wurde für komplexe Reasoning-, Analyse- und Mehrsprachigkeitsaufgaben entwickelt und zeichnet sich durch starke Instruktionsbefolgung, präzises Schlussfolgern und breite Sprachunterstützung aus.

**Stärken:** Starkes mehrsprachiges Verständnis und Generierung (u. a. Englisch, Französisch, Deutsch, Spanisch, Italienisch) · Hohe Leistung bei komplexen Reasoning- und Analyseaufgaben · Zuverlässiges Instruction-Following mit präzisen, strukturierten Antworten
**Einschränkungen:** Gewichte nicht öffentlich verfügbar, daher kein lokaler Betrieb möglich · Bei sehr spezialisierten Coding-Aufgaben hinter dedizierten Code-Modellen wie Codestral zurück

---

### Mistral Medium
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Medium ist ein proprietäres Cloud-Modell des französischen Unternehmens Mistral AI, positioniert zwischen den leichten und den Frontier-Modellen der Produktlinie. Es zielt auf starke allgemeine Sprachverarbeitung, Instruktionsbefolgung und mehrsprachige Aufgaben ab, mit besonderem Fokus auf europäische Nutzungsszenarien.

**Stärken:** Gute Balance zwischen Leistung und Kosten im mittleren Preissegment · Solide mehrsprachige Fähigkeiten, insbesondere für europäische Sprachen · Zuverlässiges Instruction-Following für strukturierte Aufgaben und Geschäftsanwendungen
**Einschränkungen:** Gewichte nicht öffentlich verfügbar, kein lokaler Betrieb möglich · Geringere Reasoning-Tiefe im Vergleich zu Frontier-Modellen wie Mistral Large oder GPT-4-Klasse

---

### Mistral Small
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Small ist ein kompaktes Allround-Modell des französischen Unternehmens Mistral AI, entwickelt für effiziente Inferenz bei niedrigen Kosten. Es bietet starkes Instruction-Following, solide mehrsprachige Fähigkeiten und gute Reasoning-Leistung für seine Größenklasse – konzipiert als leichtgewichtige Alternative zu größeren Frontier-Modellen.

**Stärken:** Sehr gutes Preis-Leistungs-Verhältnis für alltägliche Aufgaben · Solide mehrsprachige Fähigkeiten, insbesondere für europäische Sprachen · Geringe Latenz und hoher Durchsatz durch kompakte Architektur
**Einschränkungen:** Schwächer als größere Modelle bei komplexem mehrstufigem Reasoning und langen Kontexten · Begrenzte Leistung bei hochspezialisierten Domänen wie fortgeschrittener Mathematik oder tiefem Coding

---

### Kimi K2 Thinking
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** reasoning

Kimi K2 Thinking ist das erweiterte Reasoning-Modell in der Kimi-K2-Familie von Moonshot AI. Es basiert auf der K2-MoE-Architektur (1T Parameter) und wurde speziell für komplexe, mehrstufige Reasoning-Aufgaben, Mathematik und langfristige agentische Problemlösung optimiert.

**Stärken:** Integriertes Chain-of-Thought Reasoning (Thinking-Modus) · Starke Leistung bei mehrstufigen logischen Schlussfolgerungen · Besonders geeignet für komplexe Coding- und Planungsaufgaben · Unterstützt Tool-Use im Reasoning-Kontext
**Einschränkungen:** Höherer Token-Verbrauch durch interne Reasoning-Tokens · Als sehr großes MoE-Modell hoher Ressourcenbedarf für lokales Deployment · Mögliche Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Kimi K2
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** general

Kimi K2 ist ein großes Sprachmodell von Moonshot AI aus China, trainiert mit Fokus auf agentische Aufgaben, Werkzeugnutzung und komplexes Reasoning. Es zeichnet sich durch starke Coding-Fähigkeiten, mehrstufige Planung und Instruction-Following aus und wurde als leistungsfähige Open-Weights-Alternative für autonome KI-Agenten entwickelt.

**Stärken:** Starke Leistung bei agentischen Aufgaben und mehrstufiger Werkzeugnutzung · Hohe Coding-Kompetenz über mehrere Programmiersprachen hinweg · Gutes Instruction-Following bei komplexen, mehrteiligen Aufgaben
**Einschränkungen:** Als sehr großes MoE-Modell hoher Ressourcenbedarf für lokales Deployment · Mögliche Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Kimi K2.5
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** reasoning

Kimi K2.5 ist ein Reasoning-Modell von Moonshot AI aus China, trainiert auf komplexe mehrstufige Schlussfolgerungen, mathematische Probleme und agentenbasierte Aufgaben. Es kombiniert starkes Chain-of-Thought-Denken mit Coding- und Tool-Use-Fähigkeiten und richtet sich an anspruchsvolle analytische Anwendungsfälle.

**Stärken:** Starke mehrstufige Reasoning-Fähigkeiten bei Mathematik und Logik · Gute Performance bei agentenbasierten und Tool-Use-Szenarien · Solide Coding-Kompetenz kombiniert mit analytischem Denken
**Einschränkungen:** Thinking-Prozess erhöht Latenz und Token-Verbrauch erheblich · Mögliche Zensur oder Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Kimi K2.5
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** reasoning

Kimi K2.5 ist ein Reasoning-Modell von Moonshot AI aus China, entwickelt für komplexe mehrstufige Schlussfolgerungen, mathematische Aufgaben und Code-Analyse. Es kombiniert starkes logisches Denken mit langen Kontextfenstern und wurde als Weiterentwicklung der Kimi-Reihe für anspruchsvolle analytische Aufgaben konzipiert.

**Stärken:** Starke Leistung bei mehrstufigen Reasoning-Aufgaben und mathematischen Problemen · Unterstützung sehr langer Kontextfenster für umfangreiche Dokumentenanalyse · Gute Mehrsprachigkeit mit besonderem Fokus auf Chinesisch und Englisch
**Einschränkungen:** Nur über Moonshot-API verfügbar, keine lokale Ausführung möglich · Weniger transparent bezüglich Trainingsdaten und Modellarchitektur als Open-Weights-Alternativen

---

### Kimi K2.6
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** general

Kimi K2.6 ist ein großes Sprachmodell von Moonshot AI aus China, trainiert auf breiten Wissens- und Reasoning-Aufgaben. Es zeichnet sich durch starke Agentic-Fähigkeiten, Werkzeugnutzung und mehrsprachige Kompetenz aus. Entwickelt als leistungsstarke Open-Weights-Alternative für komplexe Aufgaben.

**Stärken:** Starke Agentic- und Tool-Use-Fähigkeiten für autonome Aufgabenbearbeitung · Gute Mehrsprachigkeit mit besonderer Stärke in Chinesisch und Englisch · Hohe Leistung bei Reasoning- und Coding-Aufgaben trotz Open-Weights-Verfügbarkeit
**Einschränkungen:** Als chinesisches Modell potenziell eingeschränkt bei politisch sensiblen Themen mit China-Bezug · Sehr große Modellgröße erschwert lokales Deployment ohne spezialisierte Hardware erheblich

---

### Hermes 4 405B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** instruction-following

Hermes 4 405B von Nous Research ist ein US-amerikanisches Open-Weights-Modell auf Basis von Llama 3.1 405B, feinabgestimmt auf präzises Instruction-Following, strukturierte Ausgaben und agentenbasierte Anwendungen. Es wurde entwickelt, um Zensurbeschränkungen zu reduzieren und Rollenspiel sowie komplexe Aufgaben zuverlässig zu unterstützen.

**Stärken:** Sehr starkes Instruction-Following mit präziser Befolgung komplexer Anweisungen · Optimiert für strukturierte JSON-Ausgaben und Function-Calling in Agenten-Pipelines · Reduzierte Ablehnung von Anfragen durch gezieltes Uncensored-Finetuning
**Einschränkungen:** Durch reduzierte Sicherheitsfilter erhöhtes Risiko für missbräuchliche Nutzung bei sensiblen Themen · Lokaler Betrieb des 405B-Modells erfordert erhebliche Hardware-Ressourcen (mehrere High-End-GPUs)

---

### Hermes 4 70B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** instruction-following

Hermes 4 70B von Nous Research ist ein US-amerikanisches Open-Weights-Modell, das auf einem starken Basismodell (vermutlich Llama-3-70B) mit kuratiertem Instruction-Tuning-Datensatz trainiert wurde. Es zielt auf präzises Instruction-Following, strukturierte Ausgaben und reduzierte Zensur für professionelle und kreative Anwendungsfälle.

**Stärken:** Starkes Instruction-Following mit präzisen, strukturierten Antworten · Reduzierte Überrefusal-Rate durch gezieltes Uncensored-Finetuning · Gute Leistung bei Rollenspiel, Agenten-Workflows und Function-Calling
**Einschränkungen:** Als Fine-Tune eines Basismodells abhängig von dessen Wissensgrenzen und Trainingsdaten-Cutoff · 70B-Parametergröße erfordert erhebliche Hardware-Ressourcen für lokalen Betrieb

---

### OpenAI o1
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

OpenAI o1 ist ein US-amerikanisches Reasoning-Modell, das durch reinforcement learning auf verlängertes internes Denken trainiert wurde. Es glänzt bei komplexer Mathematik, Logik und wissenschaftlichen Aufgaben. Entwickelt, um menschliches Schritt-für-Schritt-Denken zu imitieren und schwierige Probleme zuverlässiger zu lösen.

**Stärken:** Herausragende Leistung bei komplexen mathematischen und logischen Aufgaben · Robustes mehrstufiges Schlussfolgern durch internes Chain-of-Thought · Starke Leistung bei wissenschaftlichen und programmiertechnischen Problemstellungen
**Einschränkungen:** Deutlich langsamer und teurer als GPT-4o durch internen Reasoning-Overhead · Kein Zugriff auf Echtzeit-Informationen; Wissenstand auf Trainings-Cutoff begrenzt

---

### o3-mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

o3-mini ist ein kompaktes Reasoning-Modell von OpenAI (USA), das auf STEM-Aufgaben, Mathematik und Coding spezialisiert ist. Es nutzt internes Chain-of-Thought und bietet drei Reasoning-Stufen (low/medium/high). Entwickelt als kosteneffiziente Alternative zu o3 für rechenintensive Denkaufgaben.

**Stärken:** Herausragende Leistung bei mathematischen und wissenschaftlichen Reasoning-Aufgaben · Drei einstellbare Reasoning-Intensitätsstufen (low, medium, high) für Kosten-Leistungs-Optimierung · Deutlich schneller und günstiger als o3 bei vergleichbarer Reasoning-Qualität in vielen Benchmarks
**Einschränkungen:** Kein nativer Multimodal-Support (kein Bild-Input in der Basisversion) · Schwächer als größere Modelle bei kreativen, nuancierten Sprach- und Schreibaufgaben

---

### o4-mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

o4-mini ist ein kompaktes Reasoning-Modell von OpenAI (USA), das auf mathematisches, wissenschaftliches und logisches Schlussfolgern spezialisiert ist. Es bietet starke Chain-of-Thought-Fähigkeiten bei geringerer Latenz und niedrigeren Kosten als o3, und wurde als effiziente Alternative für anspruchsvolle Reasoning-Aufgaben entwickelt.

**Stärken:** Herausragende Leistung bei Mathematik, Naturwissenschaften und formalem Schlussfolgern · Deutlich schneller und kostengünstiger als o3 bei vergleichbarer Reasoning-Qualität · Starke Coding-Fähigkeiten durch integriertes Chain-of-Thought-Training
**Einschränkungen:** Kein Zugriff auf Modellgewichte – ausschließlich über OpenAI-API nutzbar · Kann bei kreativen, offenen oder nuancierten Sprachaufgaben hinter generalistischen Modellen zurückbleiben

---

### Qwen 2.5 Coder 7B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** coding

Qwen 2.5 Coder 7B ist ein von Alibaba Cloud (China) entwickeltes Open-Weights-Modell, spezialisiert auf Code-Generierung, Debugging und technische Erklärungen. Es wurde auf umfangreichen Code-Corpora trainiert und bietet starke Leistung bei gängigen Programmiersprachen in kompakter 7B-Parametergröße.

**Stärken:** Starke Code-Generierung und Vervollständigung in gängigen Sprachen wie Python, JavaScript, Java und C++ · Kompakte 7B-Größe ermöglicht effiziente lokale Ausführung auf Consumer-Hardware · Gutes Verständnis von Code-Kontext, Debugging-Aufgaben und technischen Erklärungen
**Einschränkungen:** Bei sehr komplexen, mehrstufigen Architekturentscheidungen oder großen Codebasen stoßen 7B-Modelle schnell an Kontextgrenzen · Nicht-technische oder kreative Aufgaben außerhalb des Coding-Bereichs werden deutlich schwächer abgedeckt als bei General-Purpose-Modellen

---

### Qwen 2.5 3B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 2.5 3B ist ein kompaktes Sprachmodell von Alibaba Cloud (China), trainiert auf einem breiten mehrsprachigen Datensatz mit Schwerpunkt auf Instruction-Following, Coding und Mathematik. Es richtet sich an ressourcenbeschränkte Umgebungen und lokale Deployments, wo ein gutes Leistungs-Effizienz-Verhältnis gefragt ist.

**Stärken:** Sehr geringer Ressourcenbedarf – lokal auf Consumer-Hardware betreibbar · Solide Mehrsprachigkeit, insbesondere Chinesisch und Englisch · Gute Leistung in Coding- und Mathematikaufgaben für die Modellgröße
**Einschränkungen:** Begrenzte Kontextlänge und Reasoning-Tiefe im Vergleich zu größeren Modellen der gleichen Familie · Kann bei komplexen Mehrstufenaufgaben oder langen Dokumenten an Kapazitätsgrenzen stoßen

---

### Qwen 3 14B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 14B ist ein von Alibaba Cloud (China) entwickeltes Sprachmodell mit 14 Milliarden Parametern. Es wurde auf mehrsprachigen Daten trainiert und zeichnet sich durch starkes Reasoning, Instruction-Following und Coding aus. Optional aktivierbares Chain-of-Thought ermöglicht tiefere Denkprozesse bei komplexen Aufgaben.

**Stärken:** Optionales Chain-of-Thought (Thinking-Modus) für komplexe Reasoning-Aufgaben zuschaltbar · Starke mehrsprachige Fähigkeiten, insbesondere für Chinesisch und Englisch · Gute Balance zwischen Modellgröße und Leistung – lokal auf Consumer-Hardware betreibbar
**Einschränkungen:** Kann in sensiblen politischen Themen mit Bezug zu China zensierte oder ausweichende Antworten liefern · Thinking-Modus erhöht Latenz und Token-Verbrauch deutlich, was bei einfachen Aufgaben ineffizient ist

---

### Qwen 3 4B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 4B ist ein kompaktes Sprachmodell von Alibaba Cloud (China) aus der Qwen-3-Serie. Es wurde auf mehrsprachigen Daten mit Fokus auf Instruction-Following, Reasoning und Code trainiert. Stärken liegen in effizienter lokaler Ausführung und optionalem Chain-of-Thought-Denken bei geringem Ressourcenbedarf.

**Stärken:** Optionales Thinking-Modus (Chain-of-Thought an-/abschaltbar) für komplexere Aufgaben · Sehr ressourceneffizient – lokal auf Consumer-Hardware betreibbar · Solide Mehrsprachigkeit, besonders Chinesisch und Englisch
**Einschränkungen:** Als 4B-Modell bei komplexen Reasoning- und Wissensaufgaben deutlich schwächer als größere Modelle · Kann bei sensiblen oder politisch heiklen Themen mit China-Bezug zensierte oder ausweichende Antworten liefern

---

### Qwen 3.5 397B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 397B ist ein großes Sprachmodell von Alibaba Cloud aus China. Es wurde für allgemeine Sprachverständnis- und Reasoning-Aufgaben entwickelt, mit Stärken in Mehrsprachigkeit, Instruktionsbefolgung und komplexen Analysen. Als Cloud-only-Variante ist es ausschließlich über API nutzbar.

**Stärken:** Sehr hohe Kapazität durch 397B Parameter für komplexe Reasoning-Aufgaben · Starke Mehrsprachigkeit, insbesondere Chinesisch und Englisch · Robustes Instruction-Following bei langen und strukturierten Prompts
**Einschränkungen:** Ausschließlich als Cloud-Dienst verfügbar, keine lokale Ausführung möglich · Mögliche Zensur oder Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Qwen 3.5 9B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 9B ist ein von Alibaba Cloud (China) entwickeltes Sprachmodell der Qwen-3.5-Serie. Es wurde auf mehrsprachige Instruktionsbefolgung und allgemeine Aufgaben trainiert. Stärken liegen in Reasoning, Coding und Chinesisch/Englisch-Verarbeitung. Ziel ist ein kompaktes, lokal betreibbares Modell mit starker Allround-Leistung.

**Stärken:** Starke mehrsprachige Fähigkeiten, insbesondere Chinesisch und Englisch · Gutes Verhältnis von Modellgröße zu Leistung im 9B-Segment · Unterstützt optionales Chain-of-Thought-Reasoning (Thinking-Optional)
**Einschränkungen:** Kann bei komplexen, langen Reasoning-Ketten ohne aktiviertes Thinking-Modus an Grenzen stoßen · Mögliche Zensur oder Auslassungen bei politisch sensiblen Themen mit Bezug zu China

---

### Qwen 3 32B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 32B ist ein von Alibaba Cloud (China) entwickeltes Sprachmodell mit Stärken in Mehrsprachigkeit, Reasoning und Instruction-Following. Es unterstützt optionales Chain-of-Thought-Denken und wurde für breite Anwendungsfälle von Code bis Analyse konzipiert.

**Stärken:** Starke mehrsprachige Fähigkeiten, insbesondere für Chinesisch und Englisch · Optionales Thinking-Modus ermöglicht tieferes Reasoning bei komplexen Aufgaben · Gute Balance zwischen Modellgröße und Leistung für lokales Deployment
**Einschränkungen:** Kann bei politisch sensiblen Themen mit Bezug zu China zensierte oder ausweichende Antworten liefern · Thinking-Modus erhöht Latenz und Token-Verbrauch deutlich

---

### GLM 4.6
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM 4.6 ist ein Open-Weights-Modell von Zhipu AI (China), entwickelt als leistungsstarkes Allround-Modell mit Fokus auf mehrsprachige Fähigkeiten, insbesondere Chinesisch und Englisch. Stärken liegen in Instruktionsbefolgung, Textverständnis und Dialogkompetenz. Ziel ist ein konkurrenzfähiges, lokal betreibbares Modell.

**Stärken:** Starke Chinesisch- und Englischkompetenz durch gezieltes mehrsprachiges Training · Gute Instruktionsbefolgung und Dialogfähigkeit · Open-Weights-Verfügbarkeit ermöglicht lokalen, datenschutzkonformen Betrieb
**Einschränkungen:** Leistung in weniger verbreiteten Sprachen deutlich schwächer als in Chinesisch/Englisch · Kann bei politisch sensiblen Themen mit Bezug zu China eingeschränkte oder ausweichende Antworten liefern

---

### GLM-4.7
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM-4.7 ist ein chinesisches Open-Weights-Modell von Zhipu AI, entwickelt auf Basis der GLM-Architektur. Es wurde auf mehrsprachige Instruktionsbefolgung, Reasoning und allgemeine Aufgaben trainiert. Stärken liegen in Chinesisch-Englisch-Bilingualität und Dialogfähigkeit.

**Stärken:** Starke Leistung in chinesisch-englischen bilingualen Aufgaben · Gute Instruktionsbefolgung für allgemeine Dialog- und Assistenzaufgaben · Open-Weights-Verfügbarkeit ermöglicht lokalen Betrieb ohne Cloud-Abhängigkeit
**Einschränkungen:** Kann bei westlich-kulturellen Kontexten oder nicht-chinesischen Sprachen schwächer abschneiden als bei Chinesisch · Mögliche Zensur oder Zurückhaltung bei politisch sensiblen Themen mit Bezug zu China

---

### GLM-5 Turbo
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM-5 Turbo ist ein Sprachmodell von Zhipu AI aus China, entwickelt als schnelle, effiziente Variante der GLM-5-Familie. Es ist auf mehrsprachige Instruktionsbefolgung und allgemeine Aufgaben ausgerichtet, mit Stärken in Chinesisch und Englisch sowie bei strukturierten Antworten.

**Stärken:** Starke Leistung in chinesischer und englischer Sprache · Schnelle Inferenz als Turbo-Variante der GLM-5-Familie · Gute Instruktionsbefolgung bei alltäglichen und geschäftlichen Aufgaben
**Einschränkungen:** Gewichte nicht öffentlich verfügbar, nur über API nutzbar · Mögliche Zensur oder Einschränkungen bei politisch sensiblen Themen gemäß chinesischer Regulierung

---

### GLM-5 Turbo
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM-5 Turbo ist ein chinesisches Sprachmodell von Zhipu AI, entwickelt als schnelle, kosteneffiziente Variante der GLM-5-Familie. Trainiert auf mehrsprachigen Daten mit Fokus auf Chinesisch und Englisch, eignet es sich für Konversation, Textverarbeitung und leichte Reasoning-Aufgaben im API-Betrieb.

**Stärken:** Starke Leistung in chinesisch-sprachigen Aufgaben und Nuancen · Schnelle Inferenzgeschwindigkeit als Turbo-Variante · Gute Allround-Fähigkeiten für Konversation und Textgenerierung
**Einschränkungen:** Nur über Cloud-API verfügbar, keine lokale Ausführung möglich · Mögliche Zensur oder Einschränkungen bei politisch sensiblen Themen gemäß chinesischer Regulierung

---
