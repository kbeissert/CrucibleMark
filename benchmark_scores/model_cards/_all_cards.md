# Model Cards – Alle Modelle

### Claude Haiku 4.5
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** instruction-following

Claude Haiku 4.5 ist Anthropics kompaktes Schnellmodell der vierten Claude-Generation – ausgelegt für latenzarme, kosteneffiziente Anwendungen wie Echtzeit-Interaktionen, Klassifikation und einfache Agenten-Aufgaben. Das Modell ist ausschließlich über die Anthropic-API verfügbar und eignet sich besonders für Teams, die hohen Durchsatz bei überschaubaren Kosten benötigen.

**Stärken:** Sehr niedrige Latenz und hoher Durchsatz für Echtzeit-Anwendungen · Kosteneffizient bei hohem Anfragevolumen · Solides Instruction-Following und präzise Kurzantworten
**Einschränkungen:** Geringere Tiefe bei komplexen mehrstufigen Reasoning-Aufgaben im Vergleich zu Claude Sonnet oder Opus · Eingeschränkte Leistung bei sehr langen, kontextintensiven Dokumentenanalysen

---

### Claude Opus 4.5
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Opus 4.5 ist Anthropics leistungsstärkstes Modell der Claude-4-Generation – entwickelt für komplexes Reasoning, tiefgreifende Analysen und agentenbasierte Workflows. Es ist ausschließlich über die Anthropic-API verfügbar und richtet sich an Anwendungen, bei denen Zuverlässigkeit und Tiefe Vorrang vor Geschwindigkeit haben.

**Stärken:** Herausragende Leistung bei komplexen Reasoning- und Analyseaufgaben mit langen Kontexten · Optimiert für agentic Workflows und Multi-Step-Aufgaben mit hoher Zuverlässigkeit · Starke Fähigkeiten in nuanciertem, kohärentem Langform-Schreiben und Instruktionsbefolgung
**Einschränkungen:** Nur über Anthropic API verfügbar, kein lokaler Betrieb möglich · Höhere Latenz und Kosten im Vergleich zu kleineren Claude-Modellen, was Echtzeit-Anwendungen einschränken kann

---

### Claude Opus 4.6
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Opus 4.6 ist Anthropics Flaggschiff für komplexes Reasoning und mehrstufige Agenten-Workflows. Veröffentlicht am 5. Februar 2026, ist es das erste Opus-Modell mit einem 1-Million-Token-Kontextfenster (Beta). Es überzeugt bei autonomem Software-Engineering, wissenschaftlicher Forschung und professioneller Wissensarbeit. Ausschließlich über die Anthropic-API verfügbar, optimiert für Agenten-Orchestrierung und komplexe Aufgabenplanung.

**Stärken:** State-of-the-Art für autonomes Software-Engineering mit hoher Präzision · 1M-Token-Kontextfenster (Beta): qualitativ hochwertige Long-Context-Verarbeitung · Herausragende Leistung auf wirtschaftlich wertvollen Wissensarbeits-Aufgaben · Optimiert für mehrstufige Agenten-Workflows und komplexe Aufgabenplanung
**Einschränkungen:** Ausschließlich über Anthropic-API verfügbar – kein lokaler Betrieb, keine Gewichtsexport möglich · Hohe Latenz und Kosten im Vergleich zu kleineren Claude-Modellen (Sonnet, Haiku); Premium-Modell · Datenschutzrisiko: US-Anbieter unterliegt dem CLOUD Act, EU-Daten können US-Behörden zugänglich sein

---

### Claude Opus 4.7
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** coding

Claude Opus 4.7 ist Anthropics Frontier-Reasoning-Modell der Opus-Familie, veröffentlicht am 16. April 2026. Es wurde speziell für langlaufende, asynchrone Agenten-Workflows und hochkomplexes Software-Engineering optimiert. Multiplikative Verbesserungen auf CursorBench (70% vs. 58% für Opus 4.6), Hex 93-Task-Benchmark (+13% gegenüber Opus 4.6) und Hebbia's Multi-Step-Tool-Use-Benchmarks (+14%, ⅓ Tool-Errors). Multimodal mit deutlich verbesserter Vision-Auflösung (3-fach), 1M-Token-Kontextfenster. Erste Anthropic-Veröffentlichung mit automatischen Cybersecurity-Safeguards (Projekt Glasswing).

**Stärken:** Führend bei autonomem Software-Engineering über lange Zeiträume – CursorBench 70%, Rakuten-SWE-Bench 3x vs Opus 4.6 · 1M-Token-Kontextfenster mit neuer Tokenizer-Generation (bis zu 35% effizienter) · Herausragende Multimodal-Verarbeitung: Chemische Strukturen, Patent-Workflows, Life-Science-Dokumente · Cyber-Safeguards als First-Class-Feature (automatische Erkennung und Blockierung riskanter Security-Anfragen) · Signifikante Verbesserungen bei Multi-Step-Tool-Use und Disclosed-Data-Discipline
**Einschränkungen:** Closed-Source: keine Gewichte verfügbar, ausschließlich Anthropic-API · Nicht das stärkste Anthropic-Modell – Claude Mythos Preview ist breit fähiger (eingeschränkte Verfügbarkeit) · Premium-Pricing: $5 Input / $25 Output pro 1M Tokens · Datenschutzrisiko: US-Anbieter unterliegt CLOUD Act

---

### Claude Sonnet 4.5
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude Sonnet 4.5 ist Anthropics ausgewogenes Allround-Modell der Claude-4-Generation – ein guter Kompromiss zwischen Leistung, Latenz und Kosten. Es eignet sich für komplexe Reasoning-Aufgaben, Instruction-Following und agentenbasierte Workflows. Verfügbar ausschließlich über die Anthropic-API.

**Stärken:** Starkes Reasoning und mehrstufiges Problemlösen · Zuverlässiges Instruction-Following auch bei komplexen, langen Prompts · Gut geeignet für agentenbasierte und Tool-Use-Szenarien
**Einschränkungen:** Nur über Anthropic-API verfügbar, kein lokaler Betrieb möglich · Wissenstand begrenzt auf Trainingsdaten-Cutoff; aktuelle Ereignisse erfordern externe Tools

---

### Claude Sonnet 4.6
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** coding

Claude Sonnet 4.6 ist Anthropics stärkstes Sonnet-Klassen-Modell, veröffentlicht am 17. Februar 2026. Es überzeugt mit Frontier-Leistung bei Coding, Agenten und professioneller Arbeit. Besondere Stärken bei iterativer Entwicklung, komplexer Codebase-Navigation und End-to-End-Projektmanagement. 1M-Token-Kontextfenster, multimodale Eingabe (Text, Bild, File), Tool-Use nativ unterstützt. Verfügbar über Anthropic-API, Amazon Bedrock, Google Vertex AI und Microsoft Foundry.

**Stärken:** Frontier-Leistung in der mittleren Preisklasse: $3 Input / $15 Output pro 1M Tokens · 1M-Token-Kontextfenster mit multimodalen Eingaben (Text + Bild + File) · Herausragende Coding-Fähigkeiten – SWE-bench-Verified, CursorBench und vergleichbare Benchmarks an der Spitze · Optimiert für iterative Entwicklungs-Workflows und komplexe Codebase-Navigation · Multi-Cloud-Verfügbarkeit: Anthropic-API, AWS Bedrock, Google Vertex AI, Microsoft Foundry
**Einschränkungen:** Closed-Source: keine Gewichte verfügbar · Datenschutzrisiko: US-Anbieter unterliegt CLOUD Act · Teurer als kleinere Claude-Modelle (Haiku), günstiger als Opus-Klasse · Inference-Geo-Constraint: Bei expliziter US-Routing 10% Aufpreis

---

### Codestral
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** coding

Codestral ist Mistral AIs spezialisiertes Code-Modell aus Frankreich – trainiert auf über 80 Programmiersprachen und ausgelegt auf Code-Vervollständigung, Debugging und Code-Erklärungen. Es lässt sich lokal betreiben und ist über die Mistral-API verfügbar.

**Stärken:** Hervorragende Code-Vervollständigung und Fill-in-the-Middle (FIM) für viele Sprachen · Breite Sprachabdeckung mit über 80 Programmiersprachen inkl. Python, JS, Rust, Go · Schnelle Inferenz bei gleichzeitig hoher Code-Qualität dank optimierter Architektur
**Einschränkungen:** Gewichte unter Mistral Non-Production License (MNPL) — kein kommerzieller Einsatz ohne Mistral-Vertrag; lokaler Betrieb für Research/Entwicklung möglich · Schwächer bei komplexen Reasoning-Aufgaben außerhalb des Code-Kontexts

---

### DeepSeek R1 8B
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** reasoning

DeepSeek R1 8B ist ein kompaktes Open-Weights-Reasoning-Modell von DeepSeek aus China, das lokal betreibbar und über Cloud-Provider verfügbar ist. Es nutzt sichtbares Chain-of-Thought-Reasoning und eignet sich für strukturierte Denkaufgaben und STEM-Probleme auf ressourcenarmer Hardware.

**Stärken:** Sichtbares Chain-of-Thought-Reasoning mit <thinking>-Blöcken ermöglicht nachvollziehbare Lösungswege · Starke Leistung bei Mathematik, Logik und STEM-Aufgaben relativ zur Modellgröße · Lokal betreibbar auf Consumer-Hardware dank 8B-Parametergröße
**Einschränkungen:** Thinking-Prozess kann sehr ausführlich und langsam sein, was bei einfachen Aufgaben ineffizient ist · Zensur bei politisch sensiblen Themen mit China-Bezug (z.B. Tiananmen, Taiwan) ist im Modell verankert

---

### DeepSeek V3.1-671B
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** general

DeepSeek V3.1 (Mai 2025) ist ein 671B-Parameter-MoE-Modell (37B aktiv) von DeepSeek (China) unter DeepSeek License. Starker Code-Generator mit Engram-Memory-Architektur, 128K-Token-Kontextfenster. Chinesische Herkunft und NSL sind bei der Datenrisikoeinschätzung zu berücksichtigen.

**Stärken:** Starke Coding-Leistung für ein MoE-Modell mit hoher Präzision · MoE-Architektur: 671B Gesamtparameter, nur 37B aktiv – hoher Durchsatz bei geringem Inferenz-Overhead · Training-Kosten: nur $5.6M – deutlich günstiger als typische Frontier-Modelle, Kosteneffizienz-Record · Engram-Memory-Architektur für verbesserte Langzeit-Code-Konsistenz, 128K-Token-Kontextfenster
**Einschränkungen:** Chinesisches Nationales Sicherheitsgesetz (NSL): bei Cloud-Nutzung kann staatlicher Zugriff auf Daten bestehen; BSI-Warnung vom 04.02.2025 · Lokaler Betrieb der vollen 671B-Variante erfordert erhebliche GPU-Infrastruktur (mehrere High-End-GPUs, z. B. A100/H100) · Kann bei politisch sensiblen Themen mit China-Bezug zensierte oder ausweichende Antworten liefern

---

### DeepSeek V3-2
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** general

DeepSeek V3.2 ist ein chinesisches Frontier-Modell von DeepSeek mit Open-Weights-Lizenz, ausgelegt auf Sprach-, Code- und Reasoning-Aufgaben. Es lässt sich lokal betreiben und ist über verschiedene Cloud-Provider kostengünstig nutzbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke Leistung bei Coding- und Mathematikaufgaben · Sehr gutes Preis-Leistungs-Verhältnis im Vergleich zu Konkurrenzmodellen · Breites Allgemeinwissen mit guter mehrsprachiger Kompetenz
**Einschränkungen:** Unterliegt chinesischer Zensur bei politisch sensiblen Themen (z.B. Tiananmen, Taiwan) · Als V3.2 möglicherweise noch nicht vollständig dokumentiert – Architekturdetails gegenüber V3 unklar

---

### DeepSeek V4 Flash
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** reasoning

DeepSeek V4 Flash ist die schnelle Reasoning-Variante der DeepSeek V4-Familie aus China – mit internem Chain-of-Thought und Open-Weights-Lizenz. Das Modell ist über Cloud-Provider kostengünstig verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Schnelle Inferenz dank optimierter Flash-Architektur bei gleichzeitigem Reasoning-Support · Kosteneffiziente Alternative zu DeepSeek V4 Pro für Aufgaben mit moderatem Komplexitätsgrad · Gute Mehrsprachigkeit und Code-Verständnis aus der DeepSeek-Modellfamilie
**Einschränkungen:** Ausschließlich über Cloud-API verfügbar, kein lokaler Betrieb möglich · Chinesische Herkunft birgt potenzielle Zensur bei politisch sensiblen Themen mit China-Bezug · Reasoning-Qualität liegt unter dem größeren Pro-Modell der selben Familie

---

### DeepSeek V4 Pro
**Entwickler:** DeepSeek · **Herkunft:** China · **Fokus:** reasoning

DeepSeek V4 Pro ist das Flagship-Reasoning-Modell der DeepSeek V4-Familie aus China – mit internem Chain-of-Thought und Open-Weights-Lizenz. Das Modell ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Höchste Reasoning-Qualität der DeepSeek V4-Familie mit internen reasoning_tokens · Stark bei Code-Generierung, Mathematik und mehrsprachigem Reasoning · Open-Weights-Modell mit kommerzielle Nutzung erlaubender Lizenz
**Einschränkungen:** Ausschließlich über Cloud-API verfügbar, kein lokaler Betrieb möglich · Chinesische Herkunft birgt potenzielle Zensur bei politisch sensiblen Themen mit China-Bezug · Höhere Latenz und Kosten gegenüber der Flash-Variante

---

### Devstral 2
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** coding

Devstral 2 (123B) ist ein spezialisiertes Coding-Agent-Modell von Mistral AI in Kooperation mit All Hands AI. Als Dense-Transformer optimiert es auf agentische Software-Engineering-Aufgaben wie Codebase-Exploration, Multi-File-Änderungen und Debugging. Unterstützt 256K Kontext und steht unter der modified MIT-Lizenz bereit.

**Stärken:** Spezialisiert auf agentisches Software-Engineering · Effiziente Navigation und Bearbeitung komplexer Multi-File-Codebases · Tracking von Framework-Abhängigkeiten · Automatisierte Fehlerkorrektur und Retry-Logik · Großes Kontextfenster (256K) für umfangreiche Projekte · Open Weights (modified MIT)
**Einschränkungen:** Eingeschränkt bei allgemeinen Aufgaben außerhalb des Coding-Bereichs · Kein natives Reasoning (Chain-of-Thought) · Qualitätsverlust bei komplexen Multi-Tool-Workflows durch potenzielle Parsing-Fehler bei Tool-Calls

---

### Gemini 2.5 Flash
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemini 2.5 Flash ist Googles schnelles Multimodal-Modell der 2.5-Generation – ausgelegt auf kosteneffiziente Inferenz über Text, Bild und Code hinweg. Es unterstützt sehr lange Kontextfenster und optionales Chain-of-Thought-Reasoning. Verfügbar ausschließlich über die Google-API.

**Stärken:** Sehr großes Kontextfenster von bis zu 1 Million Token · Optionales Chain-of-Thought-Reasoning (Thinking-Modus) per API aktivierbar · Starke multimodale Fähigkeiten (Text, Bild, Audio, Video, Code)
**Einschränkungen:** Nur über Google-Cloud-API nutzbar, keine lokale Ausführung möglich · Wie alle Flash-Varianten qualitativ unterhalb des schwereren Gemini 2.5 Pro bei komplexen Reasoning-Aufgaben

---

### Gemini 2.5 Pro
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** reasoning

Gemini 2.5 Pro ist Googles leistungsstärkstes Modell der 2.5-Generation – ausgelegt auf komplexes Reasoning, Coding und Analyse mit sehr langen Kontextfenstern. Optionales Chain-of-Thought-Reasoning lässt sich per API aktivieren. Verfügbar ausschließlich über die Google-API.

**Stärken:** Sehr starkes mathematisches und wissenschaftliches Reasoning mit optionalem Extended Thinking · Extrem großes Kontextfenster (bis zu 1 Million Token) für Dokumentenanalyse und lange Konversationen · Herausragende Coding-Fähigkeiten inkl. komplexer Multi-File-Projekte und Debugging
**Einschränkungen:** Ausschließlich über Google-Cloud-API verfügbar, keine lokale Ausführung möglich · Latenz im Thinking-Modus deutlich erhöht; bei einfachen Aufgaben oft überdimensioniert

---

### Gemini 3 Flash Preview
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemini 3 Flash Preview ist Googles schnelles Multimodal-Modell der dritten Generation in einer experimentellen Vorschauversion – ausgelegt auf niedrige Latenz und kosteneffiziente Verarbeitung langer Kontexte. Verfügbar ausschließlich über die Google-API.

**Stärken:** Sehr niedrige Latenz bei hohem Durchsatz, geeignet für Echtzeit-Anwendungen · Starke multimodale Fähigkeiten (Text, Bild, Audio, Video) · Effiziente Verarbeitung sehr langer Kontextfenster
**Einschränkungen:** Preview-Status bedeutet Leistungsschwankungen und mögliche API-Instabilität · Schwächer als größere Gemini-Varianten bei komplexen mehrstufigen Reasoning-Aufgaben

---

### Gemini 3.1 Flash Lite Preview
**Entwickler:** Google · **Herkunft:** USA · **Fokus:** general

Gemini 3.1 Flash Lite Preview (veröffentlicht März 2026) ist Googles kostengünstigstes Modell für High-Volume- und Low-Latency-Workloads. Optimiert für Klassifikation, einfache Extraktion, Tagging, ASR und andere kostensensitive Automatisierungsaufgaben. 1M-Token-Kontext, nativ multimodal, deutlich günstiger als Gemini 3.5 Flash. Verfügbar ausschließlich über die Google-API.

**Stärken:** Niedrigster Preis pro 1M Tokens in der Gemini-Familie ($0.25 Input, $1.50 Output) · Optimiert für High-Volume- und Low-Latency-Automatisierung · 1M-Token-Kontextfenster, nativ multimodal (Text, Bild, Video, Audio) · Funktion-Calling und strukturierte Outputs werden unterstützt
**Einschränkungen:** Preview-Status: mögliche API-Änderungen, Verhalten kann variieren · Schwächer als Gemini 3.5 Flash und Gemini 3.1 Pro bei komplexem Reasoning und Coding · Ausschließlich über Google-Cloud-API verfügbar, keine lokale Ausführung möglich · Abhängigkeit von Google-Infrastruktur; US-Anbieter unterliegt CLOUD Act

---

### Gemini 3.1 Pro Preview
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemini 3.1 Pro Preview (veröffentlicht Februar 2026) ist Googles aktuelles Flaggschiff-Pro-Modell – optimiert für komplexes Reasoning, fortgeschrittene Code-Generierung und mehrstufige Agentic-Workflows. Mit 1M-Token-Kontext, nativ multimodal (Text, Bild, Video, Audio, PDF) und starkem Tool-Use ist es das stärkste Gemini-Modell im Frontier-Bereich. Preis: $2/$12 pro 1M Tokens (≤200K Kontext). Verfügbar ausschließlich über die Google-API.

**Stärken:** Stärkstes Gemini-Modell für komplexes Reasoning, Coding und Agentic-Workflows · 1M-Token-Kontextfenster mit starkem Long-Context-Performance · Nativ multimodal (Text, Bild, Video, Audio, PDF) ohne Zusatzverarbeitung · Robustheit bei mehrstufiger Planung und Tool-Use-Aufgaben
**Einschränkungen:** Preview-Status: inkonsistente Leistung, mögliche API-Änderungen ohne Vorankündigung · Ausschließlich über Google-Cloud-API nutzbar, keine lokale Ausführung möglich · Preis-Limit >200K Kontext: $4/$18 pro 1M Tokens – teurer als Gemini 3.5 Flash · Abhängigkeit von Google-Infrastruktur; US-Anbieter unterliegt CLOUD Act

---

### Gemini 3.5 Flash
**Entwickler:** Google · **Herkunft:** USA · **Fokus:** general

Gemini 3.5 Flash ist Googles schnellstes Flash-Modell, veröffentlicht am 19. Mai 2026 auf Google I/O. Es übertrifft Gemini 3.1 Pro auf den meisten Coding- und Agenten-Aufgaben, bei 4× schnellerer Inferenz und oft weniger als der halben Kosten. 1M-Token-Kontextfenster, nativ multimodal (Text, Bild, Video, Audio). Erstmals im Gemini 3.5-Family, optimiert für Coding und autonome Agenten – nicht für maximale Reasoning-Tiefe. Ausschließlich über Google Cloud-API verfügbar.

**Stärken:** Übertrifft Gemini 3.1 Pro auf Coding- und Agenten-Aufgaben · 4× schnellere Inferenz als vergleichbare Frontier-Modelle, oft weniger als die halben Kosten · Nativ multimodal (Text, Bild, Video, Audio) ohne zusätzliche Verarbeitung · 1M-Token-Kontextfenster, kosteneffizientester Flash im Frontier-Bereich
**Einschränkungen:** Ausschließlich über Google Cloud-API verfügbar – kein lokaler Betrieb, keine Gewichtsexporte · Regression auf harte Reasoning- und Long-Context-Aufgaben im Vergleich zu Gemini 3.1 Pro · Abhängigkeit von Google-Infrastruktur; US-Anbieter unterliegt CLOUD Act, EU-Datenrisiko vorhanden

---

### Gemma 3 12B IT (llama.cpp, Q8_0) [Spark]
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 3 12B IT als Q8_0-GGUF via llama.cpp auf DGX Spark betrieben. Q8_0 ist die höchste gängige GGUF-Quantisierungsstufe und kommt der vollen FP16-Präzision sehr nahe – bei minimalen Qualitätseinbußen. Identische Gewichte wie gemma-3-12b-it-q8, jedoch auf dedizierter NVIDIA-Hardware (DGX Spark) mit entsprechend höherem Durchsatz betrieben.

**Stärken:** Starkes Instruction-Following durch gezieltes Fine-Tuning (Gemma-IT-Variante) · Q8_0-Quantisierung: nahezu verlustfreie Qualität gegenüber FP16-Referenz · Lokaler Betrieb auf dedizierter NVIDIA-Hardware (DGX Spark) – höherer Durchsatz als M-Series · Solide Mehrsprachigkeit und gutes Textverstehen über diverse Domänen hinweg
**Einschränkungen:** Kontextfenster und Reasoning-Tiefe hinter größeren Frontier-Modellen zurück · Neigt bei komplexen mehrstufigen Aufgaben zu Vereinfachungen oder Auslassungen · Höherer VRAM-Bedarf gegenüber Q4_K_M-Variante

---

### Gemma 3 12B IT (llama.cpp, Q8_0)
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 3 12B ist ein Modell von Google DeepMind mit öffentlich verfügbaren Gewichten (Google Gemma Terms of Use). Dieses Modell läuft als GGUF-Quantisierung (Q8_0), direkt von Hugging Face bezogen und via llama.cpp betrieben. Q8_0 ist die höchste gängige GGUF-Quantisierungsstufe und kommt der vollen FP16-Präzision sehr nahe – bei minimalen Qualitätseinbußen gegenüber der Referenzimplementierung.

**Stärken:** Starkes Instruction-Following durch gezieltes Fine-Tuning (Gemma-IT-Variante) · Effizient lokal betreibbar – läuft auf Consumer-Hardware mit ausreichend VRAM · Solide Mehrsprachigkeit und gutes Textverstehen über diverse Domänen hinweg · Q8_0-Quantisierung: nahezu verlustfreie Qualität gegenüber FP16-Referenz
**Einschränkungen:** Kontextfenster und Reasoning-Tiefe hinter größeren Frontier-Modellen (z.B. Gemini 1.5 Pro) zurück · Neigt bei komplexen mehrstufigen Aufgaben zu Vereinfachungen oder Auslassungen · Höherer VRAM-Bedarf gegenüber Q4_K_M-Variante

---

### Gemma 3 12B IT (llama.cpp, Q4_K_M) [Spark]
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 3 12B IT (Q4_K_M GGUF) via llama.cpp auf DGX Spark. Identische Gewichte wie gemma-3-12b-it, jedoch auf NVIDIA DGX Spark Hardware betrieben. Solide Abdeckung von Instruction-Following, Textverstehen und mehrsprachigen Aufgaben.

**Stärken:** Starkes Instruction-Following durch gezieltes Fine-Tuning (Gemma-IT-Variante) · Lokaler Betrieb auf dedizierter NVIDIA-Hardware (DGX Spark) · Solide Mehrsprachigkeit und gutes Textverstehen über diverse Domänen hinweg
**Einschränkungen:** Kontextfenster und Reasoning-Tiefe hinter größeren Frontier-Modellen zurück · Q4_K_M-Quantisierung kann minimale Qualitätsunterschiede gegenüber Vollpräzision zeigen

---

### Gemma 3 12B IT (llama.cpp, Q4_K_M)
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 3 12B ist ein Modell von Google DeepMind mit öffentlich verfügbaren Gewichten (Google Gemma Terms of Use). Dieses Modell läuft als GGUF-Quantisierung (Q4_K_M), direkt von Hugging Face bezogen und via llama.cpp betrieben. Mit 12 Milliarden Parametern deckt es ein breites Spektrum von Instruction-Following, Textverstehen und mehrsprachigen Aufgaben ab.

**Stärken:** Starkes Instruction-Following durch gezieltes Fine-Tuning (Gemma-IT-Variante) · Effizient lokal betreibbar – läuft auf Consumer-Hardware mit ausreichend VRAM · Solide Mehrsprachigkeit und gutes Textverstehen über diverse Domänen hinweg
**Einschränkungen:** Kontextfenster und Reasoning-Tiefe hinter größeren Frontier-Modellen (z.B. Gemini 1.5 Pro) zurück · Neigt bei komplexen mehrstufigen Aufgaben zu Vereinfachungen oder Auslassungen

---

### Gemma 4 12B Instruct Q4_K_XL (GGUF, UndiX-Derivative)
**Entwickler:** Google DeepMind (Base) / UndiX (Community-Distribution) · **Herkunft:** USA · **Fokus:** general

Gemma 4 12B Instruct (Q4_K_XL-GGUF, UndiX-Distribution) ist ein Mid-Size-Modell (12B) von Google DeepMind mit restriktiver Gemma-Lizenz, hier als 4-Bit-GGUF-Quantisierung via llama.cpp. 12B Parameter, 128K Token Kontextfenster, multimodale Unterstützung (Text + Bild + Video), 140+ Sprachen, konfigurierbarer Thinking-Modus. Lizenz: Google Gemma Terms of Use (restriktiv, kommerzielle Nutzung mit Auflagen).

**Stärken:** Geringer Speicherbedarf durch Q4_K_XL-Quantisierung – läuft auf Consumer-GPUs · Solides Instruction-Following durch gezieltes IT-Fine-Tuning · Multimodal mit nativem Bild- und Videoverständnis · UndiX-Distribution: bewährte Community-Wartung mit häufigen Updates · Kommerzielle Nutzung erlaubt unter Gemma-Lizenz (mit Auflagen)
**Einschränkungen:** Gemma-Lizenz ist restriktiv (nicht Apache 2.0) – kommerzielle Nutzung mit Auflagen · Q4-Quantisierung führt zu leichtem Qualitätsverlust gegenüber FP16-Vollpräzision · Im Vergleich zu größeren Gemma-4-Varianten (26B, 31B) reduzierte Kapazität für komplexe Reasoning-Ketten · Datenschutz: Google-Origin mit CLOUD-Act-Exposition (bei API-Nutzung)

---

### Gemma 4 12B Instruct Q6_K_XL (GGUF, UndiX-Derivative)
**Entwickler:** Google DeepMind (Base) / UndiX (Community-Distribution) · **Herkunft:** USA · **Fokus:** general

Gemma 4 12B Instruct (Q6_K_XL-GGUF, UndiX-Distribution) ist ein Mid-Size-Modell (12B) von Google DeepMind mit restriktiver Gemma-Lizenz als 6-Bit-GGUF-Quantisierung via llama.cpp. 12B Parameter, 128K Token Kontextfenster, multimodale Unterstützung (Text + Bild + Video), 140+ Sprachen, konfigurierbarer Thinking-Modus. Q6-Quantisierung: bessere Qualität als Q4 bei ~50% mehr Speicherbedarf. Lizenz: Google Gemma Terms of Use (restriktiv).

**Stärken:** Q6_K-Quantisierung: nahe FP16-Qualität bei deutlich reduziertem Speicherbedarf · Solides Instruction-Following durch gezieltes IT-Fine-Tuning · Multimodal mit nativem Bild- und Videoverständnis · UndiX-Distribution: bewährte Community-Wartung mit häufigen Updates · Guter Kompromiss zwischen Qualität und Deployment-Größe
**Einschränkungen:** Gemma-Lizenz ist restriktiv (nicht Apache 2.0) – kommerzielle Nutzung mit Auflagen · Q6-Quantisierung erfordert mehr VRAM als Q4-Versionen (~50% mehr) · Im Vergleich zu größeren Gemma-4-Varianten (26B, 31B) reduzierte Kapazität für komplexe Reasoning-Ketten · Datenschutz: Google-Origin mit CLOUD-Act-Exposition (bei API-Nutzung)

---

### Gemma 4 12B Instruct Q8_K_XL (GGUF, UndiX-Derivative)
**Entwickler:** Google DeepMind (Base) / UndiX (Community-Distribution) · **Herkunft:** USA · **Fokus:** general

Gemma 4 12B Instruct (Q8_K_XL-GGUF, UndiX-Distribution) ist ein Mid-Size-Modell (12B) von Google DeepMind mit restriktiver Gemma-Lizenz, hier als 8-Bit-GGUF-Quantisierung via llama.cpp. 12B Parameter, 128K Token Kontextfenster, multimodale Unterstützung (Text + Bild + Video), 140+ Sprachen, konfigurierbarer Thinking-Modus. Q8-Quantisierung: nahe FP16-Qualität bei moderatem Speichermehrbedarf gegenüber Q4/Q6.

**Stärken:** Q8_K_XL-Quantisierung: nahe FP16-Qualität bei reduziertem Speicherbedarf · Solides Instruction-Following durch gezieltes IT-Fine-Tuning · Multimodal mit nativem Bild- und Videoverständnis · UndiX-Distribution: bewährte Community-Wartung mit häufigen Updates · Kommerzielle Nutzung erlaubt unter Gemma-Lizenz (mit Auflagen)
**Einschränkungen:** Gemma-Lizenz ist restriktiv (nicht Apache 2.0) – kommerzielle Nutzung mit Auflagen · Q8-Quantisierung benötigt deutlich mehr VRAM als Q4/Q6-Versionen · Im Vergleich zu größeren Gemma-4-Varianten (26B, 31B) reduzierte Kapazität für komplexe Reasoning-Ketten · Datenschutz: Google-Origin mit CLOUD-Act-Exposition (bei API-Nutzung)

---

### Gemma 4 26B-A4B Instruct (QAT, UD-Q4) [Spark]
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 26B-A4B Instruct als QAT UD-Q4 GGUF via llama.cpp auf DGX Spark betrieben. QAT (Quantization-Aware Training) produziert eine präzisere Q4-Variante als nachträgliche Quantisierung. MoE-Architektur: 25,2B Gesamtparameter, ~4B aktiv pro Token. UD-Q4 (Unsloth Dynamic Q4) ist ein optimiertes Mixed-Precision-Format das Qualität bei geringem VRAM-Bedarf maximiert.

**Stärken:** MoE-Design: Hohe Intelligenz bei geringer Rechenlast (~4B aktive Parameter) · QAT-Quantisierung: Signifikant bessere Qualität als Post-Training-Q4 – Gewichte wurden quantisierungsbewusst trainiert · UD-Q4 (Unsloth Dynamic): Optimiertes Mixed-Precision-Format mit per-Layer-Entscheidung · Lokaler Betrieb auf NVIDIA DGX Spark – hoher Durchsatz durch dedizierte GPU-Hardware · Reasoning: Integrierte Thinking Modes (reasoning_tokens in provider metadata bestätigt)
**Einschränkungen:** Q4-Quantisierung zeigt gegenüber Q8 messbare Qualitätsunterschiede bei komplexen Code/Security-Audits · Audio-Input nicht unterstützt (nur E2B/E4B Variante) · Vision-Eingaben setzen korrektes mmproj-Loading in llama.cpp voraus · Thinking-Probe: 2/3 Probes lieferten 0 chars Output bei reasoning_tokens=512 — wahrscheinlich Cold-Start beim ersten Modell-Load auf dem DGX Spark. Probe sollte bei warmem Server wiederholt werden (Option B). Thinking-Nachweis basiert primär auf math-Probe (627 chars Inline-CoT).

---

### Gemma 4 26B-A4B Instruct Q8_K_XL (GGUF)
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 26B-A4B Instruct ist ein multimodales MoE-Modell (Mixture-of-Experts) von Google DeepMind mit Google Gemma Terms of Use (restriktiv). Es nutzt 25,2B Gesamtparameter, wovon ca. 4B pro Token aktiv sind. Als Q8_K_XL-GGUF via llama.cpp bietet es höchste Präzision. Verarbeitet Text, Bilder und Videos (bis 60s bei 1fps) sowie ein 256K-Kontextfenster.

**Stärken:** MoE-Design: Hohe Intelligenz (GPQA Diamond: 79,2 %) bei geringer Rechenlast (~4B aktive Parameter) · Multimodalität: Natives Verständnis von Text, Bildern und Videos · Dual Attention: Sliding-Window und globale Attention für Geschwindigkeit und Kontexttreue · Großes Kontextfenster: 256K Token für komplexe Dokumente und Code · Reasoning: Integrierte Thinking Modes für strukturierte Logikaufgaben · Hohe Präzision: Q8_K_XL-Quantisierung minimiert Informationsverlust · Entwicklerfreundlich: natives Function Calling und System-Prompts; Gewichte lokal betreibbar
**Einschränkungen:** Audio-Input wird von der 26B-Variante nicht unterstützt (nur E2B/E4B) · Video-Analyse in GGUF erfolgt als Sequenz von Einzelbildern · 256K-Kontextfenster und Q8-Quantisierung erfordern signifikanten VRAM

---

### Gemma 4 31B Instruct (QAT, UD-Q4) [Spark]
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 31B Instruct als QAT UD-Q4 GGUF via llama.cpp auf DGX Spark betrieben. QAT (Quantization-Aware Training) produziert eine präzisere Q4-Variante als nachträgliche Post-Training-Quantisierung. Dense-Architektur mit 31B Parametern. UD-Q4 (Unsloth Dynamic Q4) ist ein optimiertes Mixed-Precision-Format das Qualität bei geringem VRAM-Bedarf maximiert.

**Stärken:** QAT-Quantisierung: Signifikant bessere Qualität als Post-Training-Q4 – Gewichte wurden quantisierungsbewusst trainiert · UD-Q4 (Unsloth Dynamic): Optimiertes Mixed-Precision-Format mit per-Layer-Entscheidung · Lokaler Betrieb auf NVIDIA DGX Spark – dedizierte GPU-Hardware · Multimodal: Unterstützt Text- und Bildeingaben · Solide Instruktionsbefolgung und strukturierte Antwortgenerierung bei mittlerer Modellgröße
**Einschränkungen:** Q4-Quantisierung zeigt gegenüber Q8 messbare Qualitätsunterschiede bei komplexen Code/Security-Audits · Kein echtes Chain-of-Thought Reasoning (thinking_probe_detected=false – Inline-Probe-Signal war Signal C / Antwortlänge, kein gültiger Nachweis) · Sehr niedrige Tokens/s (~7,67) auf DGX Spark – Speed Profile ❌ Unusable für interaktive Anwendungsfälle · Audio-Input nicht unterstützt

---

### Gemma 4 ARA 26B-A4B APEX Q5_K_M (GGUF)
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 ARA 26B-A4B APEX ist eine Community-Variante des multimodalen MoE-Modells Gemma 4 26B-A4B Instruct von Google DeepMind (USA). Basis: 25,2B Gesamt- / 4B aktive Parameter, Google Gemma Terms of Use (restriktiv), Dual-Attention (Sliding Window + Global). ARA-Suffix und 2-Pass-APEX-Verarbeitung deuten auf einen Community-Quant-Workflow mit potenziell modifiziertem Alignment hin. Q5_K_M-Quantisierung (~20 GB) bietet guten Tradeoff zwischen Größe und Präzision. 256K Kontextfenster, multimodale Fähigkeiten (Text, Bild, Video).

**Stärken:** MoE-Design: Hohe Intelligenz bei geringer Rechenlast (~4B aktive Parameter) · Multimodalität: Natives Verständnis von Text, Bildern und Videos · Dual Attention: Sliding-Window und globale Attention für Geschwindigkeit und Kontexttreue · 256K-Kontextfenster für komplexe Dokumente und Code · Q5_K_M-Quantisierung: spürbar kleinerer Footprint als Q8-Variante bei moderatem Qualitätsverlust · Gewichte lokal betreibbar, natives Function Calling und System-Prompts
**Einschränkungen:** Community-Quant (ARA/APEX) – Modifikationen ggü. Original-Release nicht offiziell dokumentiert · Audio-Input wird von der 26B-Variante nicht unterstützt (nur E2B/E4B) · Video-Analyse in GGUF erfolgt als Sequenz von Einzelbildern · Thinking-Mode wurde in der Config nicht explizit gesetzt (analog zur Q8-Schwester) – Smoke-Test lieferte direkten "OK"-Output ohne Think-Tags, aber Gemma 4 26B-A4B hat native Thinking-Modi. Live-Probe vor produktivem Run nachholen.

---

### Gemma 4 E4B (llama.cpp, GGUF)
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 E4B ist eine Desktop-optimierte Variante der Gemma-4-Familie von Google DeepMind (Google Gemma Lizenz). Das "E" steht für "Effective" – mit ca. 4,5 Milliarden aktiven Parametern bei insgesamt 8 Milliarden Gesamtparametern (dichte Architektur mit PLE: Per-Layer Embeddings). Dieses Modell läuft als GGUF-Datei, direkt von Hugging Face bezogen und via llama.cpp betrieben. Der RAM-Footprint beträgt ca. 9,6 GB.

**Stärken:** Sehr ressourceneffizient durch PLE-Architektur (nur 4,5B aktive Parameter pro Forward Pass bei 8B Gesamtparametern) · Lokal auf Desktop-Hardware mit ~12 GB RAM betreibbar · Solides Instruction-Following für alltägliche Aufgaben
**Einschränkungen:** Begrenzte Kapazität bei komplexen Reasoning- oder Mehrschritt-Aufgaben im Vergleich zu größeren Modellen · Spezifische Modellvariante 'E4B' ist wenig dokumentiert, Leistungscharakteristik kann von Standard-Gemma-4-Varianten abweichen

---

### Gemma 4 31B
**Entwickler:** Google DeepMind · **Herkunft:** USA · **Fokus:** general

Gemma 4 31B ist ein Cloud-Modell von Google DeepMind (Google Gemma Lizenz) der vierten Generation – ausgelegt auf allgemeine Instruktionsbefolgung und Reasoning. Es ist ausschließlich über Cloud-Provider nutzbar; die Weights sind nicht öffentlich zugänglich.

**Stärken:** Starke Instruktionsbefolgung durch gezieltes RLHF-Training · Solide Mehrsprachigkeit dank Googles umfangreicher Trainingsdaten · Gutes Reasoning und strukturierte Antwortgenerierung bei mittlerer Modellgröße
**Einschränkungen:** Nur über Cloud-API nutzbar, kein lokaler Betrieb möglich · Als neueres Modell mit begrenzter öffentlicher Dokumentation – Leistungsprofil noch nicht vollständig etabliert

---

### GPT-4o Mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-4o Mini ist OpenAIs kompaktes Einstiegsmodell der GPT-4o-Familie – ausgelegt auf niedrige Kosten und schnelle Antwortzeiten. Es ist ausschließlich über die OpenAI-API verfügbar und eignet sich für alltägliche Aufgaben wie Klassifikation, einfache Textgenerierung und kosteneffiziente Automatisierungen.

**Stärken:** Sehr kosteneffizient bei guter Antwortqualität für Standardaufgaben · Schnelle Inferenz mit niedrigen Latenzen, geeignet für Echtzeit-Anwendungen · Solides Instruction-Following und Mehrsprachigkeit über viele Sprachen hinweg
**Einschränkungen:** Deutlich schwächer als GPT-4o bei komplexen Reasoning-, Mathematik- und Coding-Aufgaben · Kein lokaler Betrieb möglich – vollständige Abhängigkeit von OpenAIs Cloud-Infrastruktur

---

### GPT-4o
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-4o ist OpenAIs multimodales Allround-Modell – ausgelegt auf schnelle, kosteneffiziente Nutzung über Text, Bild und Code hinweg. Es ist ausschließlich über die OpenAI-API verfügbar und eignet sich für ein breites Spektrum produktiver Anwendungen, von Analyse und Coding bis hin zu natürlicher Gesprächsführung.

**Stärken:** Native Multimodalität: verarbeitet Text, Bild und Audio in einem einzigen Modell · Starkes Instruction-Following mit präzisen, kontextbewussten Antworten · Hohe Geschwindigkeit und Kosteneffizienz im Vergleich zu GPT-4 Turbo
**Einschränkungen:** Keine öffentlichen Gewichte – vollständig cloud-gebunden, keine lokale Nutzung möglich · Wissens-Cutoff begrenzt Aktualität; bei sehr aktuellen Ereignissen ohne Tool-Nutzung unzuverlässig · max_completion_tokens auf 4096 begrenzt (gpt-4o-2024-05-13 lehnt Werte > 4096 mit HTTP 400 ab, verifiziert im Tooluse-Test 2026-05-25)

---

### GPT-5 Mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-5 Mini ist OpenAIs kompaktes Modell der GPT-5-Familie – konzipiert als kosteneffiziente Alternative zum vollständigen GPT-5. Es ist ausschließlich über die OpenAI-API verfügbar und richtet sich an Anwendungen, die GPT-5-Qualität bei reduziertem Ressourceneinsatz benötigen.

**Stärken:** Kosteneffiziente API-Nutzung bei guter Allgemeinleistung · Schnelle Inferenzzeiten durch kompakte Architektur · Solides Instruction-Following für alltägliche Aufgaben
**Einschränkungen:** Geringere Reasoning-Tiefe und Kontextverarbeitungskapazität im Vergleich zum vollständigen GPT-5 · Keine lokale Ausführung möglich, vollständige Abhängigkeit von OpenAI-Infrastruktur

---

### GPT-5
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-5 ist OpenAIs Flaggschiff-Modell – entwickelt für anspruchsvolles Reasoning, multimodale Aufgaben und komplexe Instruktionsbefolgung. Es ist ausschließlich über die OpenAI-API verfügbar; genaue Architektur- und Trainingsdetails sind nicht öffentlich dokumentiert.

**Stärken:** Sehr starkes Reasoning und mehrstufiges Problemlösen über diverse Domänen hinweg · Hohe Instruktionstreue und konsistente Qualität bei komplexen, langen Aufgaben · Breite multimodale Fähigkeiten (Text, Bild, Code, Daten)
**Einschränkungen:** Ausschließlich über OpenAI-API verfügbar, keine lokale Ausführung oder Gewichtszugang möglich · Genaue Architektur, Trainingsdetails und Parameterzahl sind nicht öffentlich dokumentiert

---

### GPT-5.4 Mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-5.4 Mini ist OpenAIs kompakte Variante der GPT-5.4-Linie – ausgelegt auf effiziente Alltagsnutzung mit niedrigen Latenz- und Kostenprofilen. Es ist ausschließlich über die OpenAI-API verfügbar und bietet solide Instruction-Following-Qualität für Standardaufgaben.

**Stärken:** Kosteneffiziente Alternative zu größeren GPT-5-Varianten bei vergleichbarer Antwortqualität für Standardaufgaben · Schnelle Inferenz mit geringer Latenz, geeignet für produktive Echtzeit-Anwendungen · Starkes Instruction-Following und strukturierte Ausgaben (JSON, Funktionsaufrufe)
**Einschränkungen:** Als 'Mini'-Variante bei komplexen Mehrschritt-Reasoning-Aufgaben schwächer als größere Modelle der GPT-5-Familie · Nur über OpenAI-API verfügbar, kein lokaler Betrieb oder Gewichtszugang möglich

---

### GPT-5.4 Nano
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** generalist

GPT-5.4 Nano ist die leichteste und kosteneffizienteste Variante der GPT-5.4-Familie, veröffentlicht am 17. März 2026. Optimiert für geschwindigkeitskritische und hochvolumige Aufgaben wie Klassifikation, Data-Extraction, Ranking und Sub-Agent-Orchestrierung. Unterstützt 1.1M-Token-Kontext, 128K max Output, Text-/Bild-/PDF-Eingaben. 152 t/s Throughput (laut CloudPrice) — schnellste GPT-5.4-Variante.

**Stärken:** Niedrigstes Pricing in der GPT-5.4-Familie: $0.20 Input / $1.25 Output pro 1M Tokens (12× günstiger als GPT-5.4 mini) · Höchste Throughput-Rate in der GPT-5.4-Familie: 152 t/s Output-Geschwindigkeit · 1.1M-Token-Kontextfenster — größer als bei GPT-5.4 mini (400K) bei deutlich niedrigerem Preis · Optimiert für hochvolumige Batch- und Echtzeit-Pipelines mit minimaler Latenz · Unterstützt Function Calling, Parallel Function Calling, Structured Outputs, Native JSON Schema, Web Search, Prompt Caching
**Einschränkungen:** Niedrigste Qualität in der GPT-5.4-Familie (Intelligence Index 44.0, Coding Index 43.9 vs. 57+ bei Standard-GPT-5.4) · Nicht für tiefes Reasoning oder komplexe Mehrschritt-Workflows geeignet — bewusst auf Geschwindigkeit/Kosten optimiert · TTFT 3.88s — relativ langsam beim Time-to-First-Token im Vergleich zur Output-Geschwindigkeit · Keine Computer-Use-Fähigkeit (vs. GPT-5.4 Standard/Pro) · Closed-Source, keine Gewichtsexporte verfügbar – ausschließlich über OpenAI-API

---

### GPT-5.4 Pro
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** generalist

GPT-5.4 Pro ist die hochpräzise Pro-Variante von GPT-5.4 für präzisionskritische professionelle Workloads, veröffentlicht am 5. März 2026. Es nutzt zusätzliche Compute-Ressourcen für genauere und konsistentere Antworten als das Standard-GPT-5.4-Modell — empfohlen für Aufgaben, bei denen Antwortqualität über Kosten steht. 1.05M-Token-Kontextfenster, 128K max Output, Text- und Bildeingaben. Ausschließlich über die OpenAI-API verfügbar.

**Stärken:** Höhere Präzision als GPT-5.4 Standard durch zusätzliche Compute-Iterationen — weniger Halluzinationen · 1.05M-Token-Kontextfenster (größtes der GPT-5.4-Familie) mit 128K max Output · Native Computer-Use-Fähigkeit (75% OSWorld, schlägt menschliche Baseline von 72.4%) — erste GPT-Variante mit produktiv nutzbarem Computer Use · Starke SWE-Bench Pro Performance (57.7%) für reale GitHub-Style Issue-Fixes · Tool-Search-Feature reduziert Token-Verbrauch um 47% bei gleicher Accuracy
**Einschränkungen:** Höchstes Pricing: $30 Input / $180 Output pro 1M Tokens (12× teurer als GPT-5.4 Standard) · Input >272K Tokens: 2× Input-Preis, 1.5× Output-Preis · Tendenz zu längeren Antworten als GPT-5.4 (Ø 3.311 vs 2.676 Zeichen) — höhere effektive Kosten pro Anfrage · HealthBench-Score etwas niedriger als GPT-5.2 (62.6% vs 63.3%) · Closed-Source, keine Gewichtsexporte verfügbar – ausschließlich über OpenAI-API

---

### GPT-5.4
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** generalist

GPT-5.4 ist die Standardvariante der GPT-5.4-Familie von OpenAI für allgemeine professionelle Workloads, veröffentlicht am 5. März 2026. Es bietet ein 1.05M-Token-Kontextfenster mit 128K max Output, native Bildverarbeitung und Tool-Use-Fähigkeit — ein ausgewogenes Verhältnis von Qualität, Latenz und Preis für die meisten produktiven Anwendungsfälle. Ausschließlich über die OpenAI-API verfügbar.

**Stärken:** Großzügiges 1.05M-Token-Kontextfenster (1050k) — eines der größten kommerziell verfügbaren Kontextfenster · Starke Multimodalität: Text- und Bildeingaben, Textausgabe · Solide Tool-Use- und Function-Calling-Fähigkeiten für strukturierte Ausgaben · Gutes Preis-Leistungs-Verhältnis: $2.50 Input / $15 Output pro 1M Tokens · Stabile Instruction-Following-Qualität auf Standardaufgaben
**Einschränkungen:** Pro-Variante liefert bei präzisionskritischen Aufgaben konsistent bessere Ergebnisse (höhere Compute-Iterationen) · Input >272K Tokens: 2× Input-Preis, 1.5× Output-Preis · Closed-Source, keine Gewichtsexporte verfügbar – ausschließlich über OpenAI-API · CLOUD-Act-Risiko: Daten können US-Behörden zugänglich gemacht werden

---

### GPT-5.5 Pro
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** generalist

GPT-5.5 Pro ist die hochpräzise Variante von GPT-5.5 für komplexe, hochriskante Workloads, veröffentlicht am 24. April 2026 (zeitgleich mit GPT-5.5). Es nutzt zusätzliche Compute-Ressourcen, um präzisere und konsistentere Antworten zu produzieren — explizit positioniert für long-horizon problem solving, agentic coding und mehrstufige Workflows mit hohem Fehlerrisiko. 1M+ Token Kontext (922K Input, 128K Output), Text- und Bildeingaben. Ausschließlich über die OpenAI-API verfügbar.

**Stärken:** Höchste Präzision in der GPT-5-Familie durch zusätzliche Compute-Iterationen — weniger Halluzinationen und konsistentere Outputs · 1M+ Token Kontextfenster (922K Input, 128K Output) für long-horizon agentic coding · Optimiert für high-stakes Workloads, bei denen Antwortqualität über Kosten steht · Starke Tool-Use-Fähigkeiten und multimodale Eingaben (Text + Bild) · Bevorzugt für präzisionskritische Aufgaben in professionellen und wissenschaftlichen Domänen
**Einschränkungen:** Höchstes Pricing im OpenAI-Portfolio: $30 Input / $180 Output pro 1M Tokens (6× teurer als GPT-5.5 Standard) · Input >272K Tokens: doppelter Input-Preis, 1.5× Output-Preis · Closed-Source, keine Gewichtsexporte verfügbar – ausschließlich über OpenAI-API · Längere Antworten und damit höhere effektive Kosten pro Anfrage im Vergleich zu GPT-5.5 · Datenschutzrisiko: US-Anbieter unterliegt CLOUD Act, EU-Daten können US-Behörden zugänglich sein

---

### GPT-5.5
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** generalist

GPT-5.5 ist OpenAIs frontier-Modell für komplexe professionelle Workloads, veröffentlicht am 23. April 2026. Es ist das erste vollständig neu trainierte Basis-Modell seit GPT-4.5 – alle Versionen dazwischen waren inkrementelle Post-Training-Iterationen. Es überzeugt bei agentic coding, wissenschaftlicher Forschung und Arzneimittelentwicklung. Unterstützt ein 1.05M-Token-Kontextfenster, Text- und Bildeingaben. Ausschließlich über die OpenAI-API verfügbar.

**Stärken:** Führendes agentic coding mit hoher Präzision und Zuverlässigkeit · 1.05M-Token-Kontextfenster mit 128K max Output – größtes Kontextfenster im Frontier-Bereich · Erstes vollständig neu trainiertes Basis-Modell seit GPT-4.5 (nicht nur Post-Training-Iteration) · Starke Tool-Use-Fähigkeiten und multimodale Eingaben (Text + Bild) · Bedeutende Fortschritte in wissenschaftlicher Forschung und Arzneimittelentwicklung
**Einschränkungen:** Closed-Source, keine Gewichtsexporte verfügbar – ausschließlich über OpenAI-API · Premium-Pricing ($5/$30 pro 1M Tokens), Verdopplung gegenüber GPT-5.4; Input >272K Tokens: 2× Aufschlag · Datenschutzrisiko: US-Anbieter unterliegt CLOUD Act, EU-Daten können US-Behörden zugänglich sein · Internes Reasoning wird nicht in der API-Antwort zurückgegeben – der LLM-Judge kann das Chain-of-Thought nicht bewerten, was bei reasoning-intensiven Aufgaben zu systematischen Bewertungsabzügen führt

---

### GPT OSS 120B Cloud
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

GPT OSS 120B ist OpenAIs erstes großes Open-Weights-Modell (Apache-2.0-Lizenz) mit Mixture-of-Experts-Architektur. Die Weights sind frei verfügbar und das Modell lässt sich über Cloud-Provider kostengünstig nutzen; für den lokalen Betrieb wird leistungsstarke Server-Hardware benötigt. Schwerpunkte liegen auf Reasoning und agentischen Aufgaben mit konfigurierbarer Denktiefe.

**Stärken:** MoE-Architektur: 117B Gesamtparameter, nur 5,1B aktiv — effiziente Inferenz auf einer H100 · Konfigurierbare Reasoning-Intensität (low / medium / high) über System-Prompt · Voller Chain-of-Thought-Zugriff für Debugging und nachvollziehbare Entscheidungen · Native agentic Capabilities: Function Calling, Web Browsing, Python Code Execution, Structured Outputs · Apache-2.0-Lizenz: kommerzielle Nutzung und Fine-Tuning ohne Einschränkungen · Fine-Tuning auf einer einzelnen H100 möglich; Ollama-Support für lokalen Betrieb
**Einschränkungen:** Harmony Response Format zwingend erforderlich — ohne korrekte Template-Anwendung degradierte Outputs · Chain-of-Thought ist nicht für Endnutzer gedacht und sollte intern bleiben · MXFP4-Quantisierung der MoE-Weights kann bei sehr präzisen numerischen Aufgaben marginale Qualitätseinbußen verursachen

---

### GPT OSS 20B Cloud
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

GPT OSS 20B ist OpenAIs kleineres Open-Weights-Modell (Apache-2.0-Lizenz) mit Mixture-of-Experts-Architektur. Es lässt sich lokal betreiben und ist über verschiedene Cloud-Provider verfügbar. Die Reasoning-Intensität ist konfigurierbar – eine gute Wahl für lokale Deployments und Szenarien, die Fine-Tuning oder vollständige Datenkontrolle erfordern.

**Stärken:** Sehr effizienter MoE-Betrieb: 21B Parameter, nur 3,6B aktiv — läuft in 16 GB RAM · Konfigurierbare Reasoning-Intensität (low / medium / high) über System-Prompt · Fine-Tuning auch auf Consumer-Hardware möglich · Native agentic Capabilities: Function Calling, Web Browsing, Python Code Execution · Apache-2.0-Lizenz: kommerzielle Nutzung ohne Einschränkungen · Ollama-Support: einfacher lokaler Betrieb mit `ollama pull gpt-oss:20b`
**Einschränkungen:** Harmony Response Format zwingend erforderlich — ohne korrekte Template-Anwendung degradierte Outputs · Geringere Reasoning-Kapazität als das 120B-Modell bei komplexen mehrstufigen Aufgaben

---

### Grok 3 Mini
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** reasoning

Grok 3 Mini ist xAIs kompaktes Reasoning-Modell aus den USA – ausgelegt auf logisches Schlussfolgern und Mathematik mit niedrigerer Latenz. Optionales Chain-of-Thought-Reasoning ist aktivierbar. Das Modell ist ausschließlich über die xAI-API verfügbar.

**Stärken:** Starke Leistung bei mathematischen und logischen Reasoning-Aufgaben · Geringere Latenz und Kosten im Vergleich zum vollständigen Grok-3-Modell · Unterstützt optionales Chain-of-Thought-Denken (Thinking-Modus per API aktivierbar)
**Einschränkungen:** Nur über die xAI-API bzw. Grok-Plattform nutzbar, keine lokale Ausführung möglich · Als kompaktes Modell bei sehr komplexen, wissensintensiven oder kreativen Aufgaben schwächer als das vollständige Grok-3-Modell

---

### Grok 3
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** general

Grok 3 ist das textbasierte Flaggschiff-Modell von xAI, optimiert für komplexes Reasoning, Coding und wissenschaftliche Aufgaben. Es unterstützt ein Kontextfenster von 1 Million Token und ist ausschließlich über die xAI-API oder die Grok-Weboberfläche verfügbar. Das Modell ist rein textbasiert und besitzt keine multimodalen Fähigkeiten (kein Bildverständnis).

**Stärken:** Exzellente Leistungen in Mathematik, Coding und wissenschaftlichem Reasoning · Großes Kontextfenster von 1 Million Token für umfangreiche Dokumente · Unterstützung von Agenten-Funktionen durch Tool Use und Code Execution · Zugriff auf Echtzeit-Informationen via X-Datensatz und Websuche · Optionale Steigerung der Antwortqualität durch dedizierten Thinking-Modus (Test-time Compute)
**Einschränkungen:** Keine Multimodalität: Das Modell kann keine Bilder, Audio oder Videos verarbeiten oder generieren · Keine lokale Installation; Nutzung erfordert Internetverbindung zur API/Weboberfläche · Erhöhte Latenz bei Nutzung des Thinking-Modus aufgrund des zusätzlichen Rechenaufwands

---

### Grok 4.1 Fast Reasoning
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** reasoning

Grok 4.1 Fast Reasoning (Release Nov. 2025) von xAI ist für agentische Workflows und hohe Geschwindigkeit optimiert. Es bietet ein 2-Millionen-Token-Kontextfenster sowie native Funktionen für Web-Suche, Code-Ausführung und Tool-Nutzung. Das Modell ist proprietär und nur via API verfügbar. Hinweis: Das Modell ist als "deprecated" markiert; eine Migration ist bis zum 15. August 2026 erforderlich.

**Stärken:** Hohe Inferenzgeschwindigkeit bei optimierter Logik- und Mathematikfähigkeit · Extrem großes Kontextfenster (2 Mio. Tokens) und 30k maximale Output-Tokens · Native Unterstützung für Tool-Calling, Web-Suche und Code-Execution · Signifikant reduzierte Halluzinationsrate (ca. 3x weniger als Vorgänger) · Eignung für parallele Prozesse in agentischen Workflows
**Einschränkungen:** Status: Deprecated (Migration bis 15.08.2026 notwendig) · Kein lokaler Betrieb möglich (nur Cloud/API) · Latenz-Optimierung kann bei komplexen Problemen zu oberflächlichen Argumentationsketten führen · Geringere kreative Tiefe im Vergleich zu reinen Vollmodellen

---

### Grok 4 Fast Non-Reasoning
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** general

Grok 4 Fast Non-Reasoning ist xAIs schnellste Inferenzvariante – ohne explizites Thinking/Reasoning, aber mit hoher Geschwindigkeit und guter Qualität für allgemeine Aufgaben. Es ist ausschließlich über die xAI-API verfügbar und richtet sich an Anwendungen mit niedrigen Latenzanforderungen.

**Stärken:** Sehr schnelle Inferenz ohne Reasoning-Overhead · Gute Qualität für alltägliche Aufgaben, Zusammenfassungen und einfache Fragen · Echtzeit-Zugriff auf X-Plattform-Daten für aktuelle Informationen · Kosteneffizient aufgrund niedrigerer Rechenanforderungen
**Einschränkungen:** Nur über xAIs Cloud-API verfügbar, kein lokaler Betrieb möglich · Kein explizites Thinking/Reasoning – bei komplexen logischen oder mathematischen Aufgaben schwächer · Der unzensierte Stil kann bei sensiblen Themen zu kontroversen Antworten führen

---

### Grok 4 (Non-Reasoning)
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** general

Grok 4 (2025-03-09, non-reasoning) ist die Standard-Variante der Grok-4-Generation von xAI aus den USA – ohne aktives Chain-of-Thought, ausgelegt auf schnelle direkte Antworten. 1000K Kontextfenster, Tool-Use-Unterstützung. Das Modell ist ausschließlich über die xAI-API verfügbar.

**Stärken:** Niedrige Latenz durch deaktiviertes Chain-of-Thought-Reasoning · Breite Allround-Fähigkeiten für Konversation und Textaufgaben · Unterstützung von Tool Use / Function Calling für Agentenanwendungen
**Einschränkungen:** Schwächere Leistung bei komplexen mehrstufigen Schlussfolgerungsaufgaben im Vergleich zur Reasoning-Variante · Nur über xAI-Cloud-API verfügbar, kein lokaler Betrieb möglich

---

### Grok 4 Reasoning (März 2025)
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** reasoning

Grok 4 (2025-03-09, reasoning) ist die Reasoning-Variante der Grok-4-Generation von xAI aus den USA – mit aktivem Chain-of-Thought für komplexe mehrstufige Aufgaben. 1000K Kontextfenster, Tool-Use-Unterstützung. Das Modell ist ausschließlich über die xAI-API verfügbar.

**Stärken:** Starkes mehrstufiges Schlussfolgern bei Mathematik- und Logikaufgaben · Explizite Reasoning-Traces erhöhen Nachvollziehbarkeit der Antworten · Gute Performance bei wissenschaftlichen und technischen Fragestellungen
**Einschränkungen:** Ausschließlich über xAI-Cloud verfügbar, kein lokaler Betrieb möglich · Reasoning-Modus erhöht Latenz und Token-Verbrauch gegenüber Standard-Modellen

---

### Grok 4.3
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** general

Grok 4.3 ist xAIs aktuelles Flaggschiff-Modell, veröffentlicht am 30. April 2026 (Beta: 17. April 2026). Es ist xAIs intelligentestes und schnellstes Modell. Erstmals mit nativem Video-Input, 1M-Token-Kontextfenster und günstigeren Input-Preisen. MoE-Architektur, optimiert für allgemeine Sprachaufgaben, Reasoning und Echtzeit-Wissenszugriff via X-Plattform. Ausschließlich über xAI-API verfügbar. Starke agentic performance für Routine-Aufgaben, direkter Antwortstil.

**Stärken:** IAIs intelligentestes und schnellstes Modell mit hoher Gesamtqualität · Erstmals nativ multimodal: Text, Bild und Video-Input in einem Modell · 1M-Token-Kontextfenster und günstigere Input-Preise als Vorgänger · Echtzeit-Zugriff auf X-Plattform-Daten für aktuelle Informationen und kontextuelle Antworten · Starke agentic performance für Routine-Aufgaben, direkter Antwortstil
**Einschränkungen:** Ausschließlich über xAI-API verfügbar – kein lokaler Betrieb, keine Gewichtsexporte · Schwächer bei komplexem Software-Engineering im Vergleich zu spezialisierten Coding-Modellen · Direkter, unzensierter Stil kann bei sensiblen Themen zu kontroversen oder einseitigen Antworten führen · Begrenzte Transparenz bezüglich Modellarchitektur und Parametergröße

---

### Hermes 3 8B (llama.cpp, Q6_K_L)
**Entwickler:** NousResearch · **Herkunft:** USA · **Fokus:** instruction-following

Hermes 3 8B von NousResearch (USA), basierend auf Meta Llama 3.1 8B, veröffentlicht August 2024. Instruction-Fine-Tune mit bewusst reduzierten Ablehnungsraten für agentische und Rollenspiel-Aufgaben. Läuft hier als Q6_K_L-GGUF via llama.cpp. Q6_K_L (6-Bit-K-Quant, Large-Variante) hält Attention-Schichten auf höherer Präzision und gilt als nahezu verlustfrei – Community-Bewertung: sehr hohe Qualität bei kompakter Größe.

**Stärken:** Starkes Instruction-Following mit niedrigen Ablehnungsraten für ambivalente oder kreative Anfragen · Gute Funktion bei Tool-Use und strukturierten Ausgaben (JSON, Funktionsaufrufen) · Q6_K_L: höherpräzise Attention-Schichten, noch näher an BF16-Vollpräzision als Standard-Q6_K
**Einschränkungen:** Als Finetuning auf Llama 3.1 8B begrenzte Reasoning-Kapazität gegenüber größeren Modellen · Reduzierte Sicherheitsfilter – ungeeignet für unbeaufsichtigte oder produktive Deployments

---

### Hermes 4 14B (llama.cpp, Q6_K, Abliterated)
**Entwickler:** NousResearch · **Herkunft:** USA · **Fokus:** reasoning

Hermes 4 14B (Q6_K, Abliterated) ist eine Community-Variante (mradermacher) von NousResearch' Qwen3-basiertem Modell. Es nutzt ein massiv erweitertes Post-Training (~60B Tokens). Diese Version wurde durch Abliteration von allen Sicherheitsfiltern befreit – maximale Kreativität und Flexibilität, aber keine Eignung für produktive Umgebungen.

**Stärken:** Hohe Reasoning-Kapazität durch massiv erweitertes Post-Training · Hybrid-Reasoning: Explizite Denktraces via Thinking-Tags auf Anfrage möglich · Unzensierte Nutzung durch Abliteration für Forschung und spezialisierte Workloads · Minimale Qualitätseinbußen durch Q6_K-Quantisierung gegenüber BF16
**Einschränkungen:** Keine Sicherheitsmechanismen: Ungeeignet für unüberwachte oder produktive Umgebungen · Community-Modifikation: Keine offizielle Veröffentlichung von NousResearch · Abliteration führt zu extrem niedrigen Ablehnungsraten – keine Filterung bei kritischen Themen

---

### Hermes 4 14B (llama.cpp, Q4_K_M)
**Entwickler:** NousResearch · **Herkunft:** USA · **Fokus:** reasoning

Hermes 4 14B von NousResearch, basierend auf Qwen3-14B (Apache 2.0). Hybrid-Reasoning-Modell mit optionalem Thinking-Modus. Deutlich gesteigertes Post-Training für verbesserte Reasoning-Fähigkeiten. Läuft hier als Q4_K_M-GGUF via llama.cpp – Community-Standard für lokale Deployments mit guter Balance aus Qualität und Speicherbedarf. Besonderes Merkmal: Safety-Filter durch Training austrainiert, nicht entfernt – hohe Kreativität ohne Qualitätsverlust.

**Stärken:** Hybrid-Reasoning: Optionaler Thinking-Modus mit expliziten Denktraces bei Bedarf · Minimale Ablehnungsrate durch gezieltes Alignment – maximale Hilfsbereitschaft · Safety-Training: Filter durch Training austrainiert, nicht entfernt – hohe Kreativität ohne Qualitätsverlust · Effizient: Q4_K_M Quantisierung für Consumer-Hardware mit begrenztem VRAM
**Einschränkungen:** Quantisierungsverlust: Q4_K_M zeigt messbare Qualitätseinbußen gegenüber Q6_K bei komplexem Reasoning · Skalierung: Bei extrem langen Reasoning-Ketten unterlegen gegenüber größeren Modellen · VRAM-Bedarf: Benötigt ca. 15GB VRAM für stabile Ausführung

---

### Hermes 4.3 36B Q6_K (GGUF)
**Entwickler:** NousResearch · **Herkunft:** USA · **Fokus:** general

Hermes 4.3 36B ist ein Open-Weights-Modell von NousResearch (USA) mit Apache-2.0-Lizenz. Es ist ein Dense-Transformer mit 36B Parametern, optimiert für Instruction-Following und agentische Aufgaben. Q6_K-GGUF via llama.cpp bietet hohe Präzision mit moderatem Speicherbedarf.

**Stärken:** Sehr gutes Instruction-Following mit präziser Befolgung komplexer Anweisungen · Starke Unterstützung für strukturierte Ausgaben (JSON, Funktionsaufrufe, Agenten-Frameworks) · Q6_K-Quantisierung: hohe Präzision bei moderatem VRAM-Bedarf · Agentische Fähigkeiten für Tool-Use und Multi-Step-Workflows · Apache 2.0 Lizenz – kommerzielle Nutzung erlaubt · Effizient lokal betreibbar auf Consumer-Hardware
**Einschränkungen:** Als 36B-Modell bei sehr komplexen Mehrschritt-Reasoning-Aufgaben schwächer als Frontier-Modelle · US-Unterliegenschaft unter CLOUD Act bei Cloud-Nutzung · Kein natives Thinking/CoT-Modus · Dense-Architektur erfordert mehr VRAM als vergleichbare MoE-Modelle

---

### Llama 3.3 70B Versatile
**Entwickler:** Meta · **Herkunft:** USA · **Fokus:** general

Llama 3.3 70B Versatile ist Metas Modell mit öffentlich verfügbaren Gewichten (Meta Llama Community License) und 70 Milliarden Parametern der Llama-3.3-Generation aus den USA. Es ist über Cloud-Provider kostengünstig nutzbar; für den lokalen Betrieb wird leistungsstarke Hardware benötigt.

**Stärken:** Starkes Instruction-Following über viele Aufgabentypen hinweg · Gute Reasoning- und Analysefähigkeiten für ein 70B-Modell · Frei verfügbare Gewichte ermöglichen lokalen, datenschutzkonformen Betrieb
**Einschränkungen:** Kontextfenster und Langdokument-Verarbeitung schwächer als bei spezialisierten Modellen · Kann bei sehr komplexen mehrstufigen Reasoning-Aufgaben hinter dedizierten Thinking-Modellen zurückbleiben

---

### Magistral Medium
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** reasoning

Magistral Medium ist das spezialisierte Reasoning-Modell von Mistral AI (Juni 2025) für komplexe Logik, Mathematik und strukturierte Entscheidungsfindung. Es ist ausschließlich über die Mistral-API (Le Chat/Enterprise) verfügbar; die Gewichte sind nicht öffentlich zugänglich. Es unterstützt ein 40k Kontextfenster und bietet durch Flash Answers beschleunigte Antwortzeiten.

**Stärken:** Herausragende mathematische Logik (73,6 % AIME2024) · Transparente Nachvollziehbarkeit durch explizite Darstellung des Denkprozesses · Starke mehrsprachige Kompetenz (u. a. EN, FR, ES, DE, CN) · Hohe Kapazität für lange Ausgaben (bis zu 131,1k Tokens)
**Einschränkungen:** Keine lokale Ausführung möglich (proprietäres API-Modell) · Kein Zugriff auf die Modellgewichte (im Gegensatz zur Small-Variante)

---

### Magistral Small
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** reasoning

Magistral Small ist Mistral AIs kompaktes Reasoning-Modell aus Frankreich – ausgelegt auf strukturiertes Schlussfolgern mit niedrigerer Latenz. 128K Kontextfenster, Apache-2.0-Lizenz. Verfügbar über die Mistral-API; die Weights sind frei zugänglich.

**Stärken:** Strukturiertes mehrstufiges Schlussfolgern (Chain-of-Thought) · Geringere Latenz und Kosten im Vergleich zu größeren Reasoning-Modellen · Starke Mehrsprachigkeit, insbesondere europäische Sprachen
**Einschränkungen:** Nur über Mistral-API verfügbar, keine lokale Ausführung möglich · Als kleineres Modell bei sehr komplexen Reasoning-Ketten hinter größeren Varianten wie Magistral Medium zurück

---

### Llama 4 Scout 17B
**Entwickler:** Meta · **Herkunft:** USA · **Fokus:** general

Llama 4 Scout ist Metas offenes Multimodal-Modell der vierten Llama-Generation aus den USA – ausgelegt auf allgemeine Sprachaufgaben und Bildverständnis. 10M Token Kontext, MoE-Architektur (109B total / 17B aktiv). Die Weights sind frei verfügbar.

**Stärken:** Extrem langer Kontextfenster von bis zu 10 Millionen Tokens · Effiziente MoE-Architektur: hohe Leistung bei vergleichsweise geringem Rechenaufwand · Multimodale Fähigkeiten (Text und Bild als Eingabe)
**Einschränkungen:** Als MoE-Modell höherer Speicherbedarf für alle Expertengewichte trotz geringer aktiver Parameter · Multimodale Ausgabe (Bildgenerierung) nicht unterstützt – nur Textausgabe

---

### MiniMax M2.7
**Entwickler:** MiniMax · **Herkunft:** China · **Fokus:** general

MiniMax M2.7 ist ein Sprachmodell des chinesischen Unternehmens MiniMax – ausgelegt auf allgemeine Sprach- und Reasoning-Aufgaben. Das Modell ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Sehr großes MoE-Modell mit hoher Parameterkapazität bei effizienter Inferenz · Starke Mehrsprachigkeit mit besonderem Fokus auf Chinesisch und Englisch · Langes Kontextfenster für umfangreiche Dokument- und Dialogverarbeitung
**Einschränkungen:** Als chinesisches Modell potenziell eingeschränkte oder zensierte Antworten zu politisch sensiblen Themen · Sehr hohe Hardwareanforderungen für lokales Deployment aufgrund der Modellgröße

---

### MiniMax M3
**Entwickler:** MiniMax · **Herkunft:** China · **Fokus:** agentic

MiniMax M3 ist ein multimodales MoE-Modell (Text, Bild, Video Input; Text Output) mit 1M Token Kontext. Durch die MSA-Architektur (KV-Block Selection) bietet es extrem schnelles Prefill und Decoding. Fokus: Agentische Workflows, Coding und Tool-Use. Chinesisches Modell; Open-Weights ca. 10 Tage nach API-Launch.

**Stärken:** Herausragendes Coding & Agentic Reasoning: Führende Benchmarks (SWE-Bench Pro: 59%, BrowseComp: 83.5) · Effiziente Multimodalität: Native Verarbeitung von Text, Bild und Video · Extreme Skalierbarkeit: 1M Token Kontext mit massiver Geschwindigkeitssteigerung (MSA-Architektur)
**Einschränkungen:** Inhaltliche Restriktionen: Mögliche Zensur oder eingeschränkte Antworten bei politisch sensiblen Themen (chinesische Herkunft) · Verfügbarkeit: Gewichte (Weights) sind erst kurz nach dem API-Launch verfügbar

---

### Ministral 3B 14B
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Ministral 14B ist ein Modell von Mistral AI mit öffentlich verfügbaren Gewichten (Mistral Research License, kein kommerzieller Einsatz) aus Frankreich – konzipiert für effiziente lokale Ausführung bei gutem Instruction-Following. Es lässt sich lokal betreiben und ist über Cloud-Provider verfügbar.

**Stärken:** Sehr geringer Speicher- und Rechenaufwand bei akzeptabler Antwortqualität · Gut geeignet für Edge- und On-Device-Deployment ohne Cloud-Abhängigkeit · Solides Instruction-Following für ein Modell dieser Größenklasse
**Einschränkungen:** Deutlich schwächere Reasoning- und Wissenstiefe im Vergleich zu größeren Modellen · Begrenzte Kontextfenstergröße und reduzierte Mehrsprachigkeitsleistung gegenüber größeren Mistral-Varianten

---

### Ministral 3B
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Ministral 3B ist ein Modell von Mistral AI mit öffentlich verfügbaren Gewichten (Mistral Research License, kein kommerzieller Einsatz) aus Frankreich – optimiert für Edge- und lokale Anwendungen mit minimalem Ressourcenbedarf. Es lässt sich lokal betreiben und ist über Cloud-Provider verfügbar.

**Stärken:** Sehr geringer Ressourcenbedarf – ideal für lokale und Edge-Deployments · Solides Instruction-Following trotz kompakter Modellgröße · Mehrsprachige Kompetenz, insbesondere für europäische Sprachen
**Einschränkungen:** Begrenzte Reasoning-Tiefe und Kontextverarbeitung im Vergleich zu größeren Modellen · Schwächere Leistung bei komplexen mehrstufigen Aufgaben oder langen Dokumenten

---

### Mistral Large 3
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Large 3 (November 2024, 123B) ist das Flaggschiff-Modell von Mistral AI aus Frankreich – entwickelt für komplexes Reasoning, Analyse und mehrsprachige Aufgaben. Open Weights unter der Mistral Research License (nicht-kommerziell), für kommerzielle Nutzung über die Mistral-API verfügbar.

**Stärken:** Starkes mehrsprachiges Verständnis und Generierung (u. a. Englisch, Französisch, Deutsch, Spanisch, Italienisch) · Hohe Leistung bei komplexen Reasoning- und Analyseaufgaben · Zuverlässiges Instruction-Following mit präzisen, strukturierten Antworten · EU-Entwicklung: kein US CLOUD Act- oder chinesisches NSL-Risiko für Gewichte
**Einschränkungen:** Gewichte unter Mistral Research License (MRL) — Weights nicht für kommerzielle Zwecke; für kommerzielle Nutzung ist ein Mistral-API-Vertrag erforderlich · Bei sehr spezialisierten Coding-Aufgaben hinter dedizierten Code-Modellen wie Codestral zurück

---

### Mistral Large 3
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** generalist

Mistral Large 3 ist Mistrals leistungsfähigstes Modell (Stand Dezember 2025), basierend auf einer Sparse-MoE-Architektur mit 675B Gesamtparametern (41B aktiv). Es unterstützt multimodale Eingaben und lange Kontextfenster von 256K Tokens. Das Modell ist unter Apache 2.0 lizenziert und für lokales Deployment verfügbar.

**Stärken:** Starke generelle Reasoning-Fähigkeiten · Sehr großes Kontextfenster (256K) · Open Weights unter Apache 2.0 · Effiziente MoE-Architektur · Tool Use und strukturierte Ausgaben · Multimodal (Text + Bild)
**Einschränkungen:** Höherer Tool-Call-Error-Rate als GPT-Modelle · Keine nativen Reasoning-Tokens (kein CoT-Thinking)

---

### Mistral Medium 1.0
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Medium 1.0 (Dezember 2023) war Mistral AIs erste proprietäre Mittelklasse-API ohne öffentliche Gewichte – Legacy-Modell, abgelöst durch Mistral Medium 3.5. 32K Kontextfenster, multilingual. Historische Daten unter API-Preisen verfügbar.

**Stärken:** Gute Balance zwischen Leistung und Kosten im mittleren Preissegment · Solide mehrsprachige Fähigkeiten, insbesondere für europäische Sprachen · Zuverlässiges Instruction-Following für strukturierte Aufgaben und Geschäftsanwendungen
**Einschränkungen:** Gewichte nicht öffentlich verfügbar, kein lokaler Betrieb möglich · Legacy/Deprecated – durch Mistral Medium 3.5 abgelöst (April 2026) · Geringere Reasoning-Tiefe im Vergleich zu Frontier-Modellen wie Mistral Large oder GPT-4-Klasse

---

### Mistral Medium 3.5
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Medium 3.5 ist Mistral AIs aktuelles Open-Weights-Frontier-Modell aus Frankreich – optimiert für agentische Workflows und Coding-Aufgaben. Als Open Weights (Modified MIT) lokal betreibbar und über die Mistral-API verfügbar. Kontext: 256k. Multimodal.

**Stärken:** Open Weights (Modified MIT) – lokal betreibbar, ohne Nutzungseinschränkungen kommerziell einsetzbar · Frontier-Leistung mit Fokus auf agentische und Coding-Aufgaben · 256k Kontextfenster und multimodale Fähigkeiten · EU-Entwicklung: kein US CLOUD Act- oder chinesisches NSL-Risiko für Gewichte
**Einschränkungen:** Relativ neu (April 2026) – weniger etablierte Community-Erfahrungen als ältere Modelle · Lokaler Betrieb erfordert erhebliche Hardware-Ressourcen bei Frontier-Modellgröße · Agentische Optimierung kann bei rein kreativen oder narrativen Aufgaben Abstriche bedeuten

---

### Mistral Small 3.1
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Small 3.1 (März 2025, 24B) ist ein kompaktes Open-Weights-Modell von Mistral AI aus Frankreich (Apache-2.0-Lizenz) – ausgelegt auf effiziente Inferenz bei niedrigen Kosten. Lokal betreibbar und über Cloud-Provider verfügbar. Abgelöst durch Mistral Small 4 (2603) im März 2026.

**Stärken:** Sehr gutes Preis-Leistungs-Verhältnis für alltägliche Aufgaben · Solide mehrsprachige Fähigkeiten, insbesondere für europäische Sprachen · Geringe Latenz und hoher Durchsatz durch kompakte Architektur (24B) · Open Weights (Apache-2.0) – lokal betreibbar ohne Nutzungseinschränkungen
**Einschränkungen:** Schwächer als größere Modelle bei komplexem mehrstufigem Reasoning und langen Kontexten · Begrenzte Leistung bei hochspezialisierten Domänen wie fortgeschrittener Mathematik oder tiefem Coding · Legacy/Deprecated – durch Mistral Small 4 (mistral-small-2603) abgelöst

---

### Mistral Small 4
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Small 4 (März 2026, 24B) ist das aktuelle kompakte Open-Weights-Modell von Mistral AI aus Frankreich (Apache-2.0-Lizenz). Nachfolger von Mistral Small 3.1 mit verbesserter Instruction-Following-Qualität und Effizienz. Lokal betreibbar und über die Mistral-API verfügbar.

**Stärken:** Open Weights (Apache-2.0) – lokal betreibbar ohne Nutzungseinschränkungen · Verbesserte Instruction-Following-Qualität gegenüber Small 3.1 · Sehr gutes Preis-Leistungs-Verhältnis für alltägliche und agentic Aufgaben · EU-Entwicklung: kein US CLOUD Act- oder chinesisches NSL-Risiko für Gewichte
**Einschränkungen:** Schwächer als größere Modelle bei komplexem mehrstufigem Reasoning und langen Kontexten · Begrenzte Leistung bei hochspezialisierten Domänen wie fortgeschrittener Mathematik · Tool-Use: Generiert natives Mistral-Tool-Call-Format statt MCP-JSON-Format

---

### Kimi K2 Thinking
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** reasoning

Kimi K2 Thinking ist die Reasoning-Variante der Kimi-K2-Familie von Moonshot AI aus China – mit internem Chain-of-Thought für komplexe Denkaufgaben. Es ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Integriertes Chain-of-Thought Reasoning (Thinking-Modus) · Starke Leistung bei mehrstufigen logischen Schlussfolgerungen · Besonders geeignet für komplexe Coding- und Planungsaufgaben · Unterstützt Tool-Use im Reasoning-Kontext
**Einschränkungen:** Höherer Token-Verbrauch durch interne Reasoning-Tokens · Als sehr großes MoE-Modell hoher Ressourcenbedarf für lokales Deployment · Mögliche Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Kimi K2
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** general

Kimi K2 ist das Flaggschiff-Modell von Moonshot AI aus China – mit Open-Weights-Lizenz und Fokus auf agentische Aufgaben, Coding und mehrstufiges Reasoning. Es lässt sich lokal betreiben und ist über Cloud-Provider kostengünstig nutzbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke Leistung bei agentischen Aufgaben und mehrstufiger Werkzeugnutzung · Hohe Coding-Kompetenz über mehrere Programmiersprachen hinweg · Gutes Instruction-Following bei komplexen, mehrteiligen Aufgaben
**Einschränkungen:** Als sehr großes MoE-Modell hoher Ressourcenbedarf für lokales Deployment · Mögliche Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Kimi K2.5
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** reasoning

Kimi K2 (Version 0127) ist ein großes Open-Weights-Modell von Moonshot AI aus China – mit Fokus auf agentische Aufgaben, Coding und mehrstufiges Reasoning. Es ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke mehrstufige Reasoning-Fähigkeiten bei Mathematik und Logik · Gute Performance bei agentenbasierten und Tool-Use-Szenarien · Solide Coding-Kompetenz kombiniert mit analytischem Denken
**Einschränkungen:** Thinking-Prozess erhöht Latenz und Token-Verbrauch erheblich · Mögliche Zensur oder Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Kimi K2.6
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** general

Kimi K2.6 ist ein Open-Weights-Modell von Moonshot AI aus China der K2-Generation – ausgelegt auf agentische Aufgaben, Coding und Reasoning. Es ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke Agentic- und Tool-Use-Fähigkeiten für autonome Aufgabenbearbeitung · Gute Mehrsprachigkeit mit besonderer Stärke in Chinesisch und Englisch · Hohe Leistung bei Reasoning- und Coding-Aufgaben trotz Open-Weights-Verfügbarkeit
**Einschränkungen:** Als chinesisches Modell potenziell eingeschränkt bei politisch sensiblen Themen mit China-Bezug · Sehr große Modellgröße erschwert lokales Deployment ohne spezialisierte Hardware erheblich

---

### Hermes 4 405B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** reasoning

Hermes 4 405B von NousResearch, basierend auf Meta-Llama-3.1-405B. Das Flaggschiff der Hermes-4-Familie mit massivem Parameter-Upgrade. Hybrid-Reasoning mit optionalem Thinking-Modus, veröffentlicht August 2025. Stark reduzierte Ablehnungsraten. Das größte open-weights Modell der Familie.

**Stärken:** Exzellentes Reasoning und STEM-Leistung durch hybriden Thinking-Modus. · Maximale Kreativität bei Rollenspielen, Szenengestaltung und komplexem Prompting. · Niedrigste Ablehnungsrate – maximale Hilfsbereitschaft und Freiheit. · Starke Adhärenz bei JSON-Strukturen, Function-Calling und komplexen Agenten-Pipelines.
**Einschränkungen:** Wissensstand bis Januar 2025; keine Informationen über aktuellere Ereignisse. · Hoher Ressourcenbedarf: ~405GB VRAM (FP8) oder ~200GB (Q4) erforderlich. · Erhöhtes Risiko für missbräuchliche Nutzung durch bewusst reduzierte Sicherheitsfilter. · Kommerzielle Nutzung unterliegt den spezifischen Bedingungen der Meta Llama Lizenz.

---

### Hermes 4 70B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** reasoning

Hermes 4 70B (August 2025) ist ein Hybrid-Reasoning-Modell auf Basis von Meta-Llama-3.1-70B. Es nutzt ein massiv erweitertes Post-Training-Korpus für verbesserte Logik und Code-Leistung. Das Modell unterstützt einen optionalen Thinking-Modus, JSON-Modus, Function-Calling und ein 131k Token-Kontextfenster. Besonderes Merkmal: Safety-Filter durch Training austrainiert – besonders kreativ bei Rollenspielen, Szenengestaltung und unkonventionellen Themen.

**Stärken:** Hybrid-Reasoning: Optionaler Thinking-Modus mit expliziten Denktraces für komplexe Aufgaben. · Hohe Fachleistung: Signifikante Steigerung in Mathematik, Code und STEM durch verifizierte Reasoning-Traces. · Safety-Training: Filter durch Training austrainiert, nicht entfernt – hohe Kreativität · Agenten-Optimierung: Hohe Adhärenz bei JSON-Strukturen und Tool-Use/Function-Calling.
**Einschränkungen:** Wissensstand: Cutoff Januar 2025. · Hardware-Anforderungen: Hoher VRAM-Bedarf (BF16: ~141GB; FP8: ~75GB; Q4: ~35GB). · Lizenz: Kommerzielle Nutzung unterliegt den spezifischen Bedingungen der Meta Llama Community License.

---

### NVIDIA Nemotron 3 Ultra 550B A55B
**Entwickler:** NVIDIA · **Herkunft:** USA · **Fokus:** reasoning

NVIDIA Nemotron 3 Ultra ist ein Open-Frontier-Reasoning- und Orchestrierungsmodell von NVIDIA mit 55B aktiven Parametern (550B gesamt, MoE). Hybrid Transformer-Mamba Mixture-of-Experts-Architektur, 1M-Token-Kontextfenster, multimodaler Text-zu-Text-Workflow. Veröffentlicht am 4. Juni 2026. Speziell optimiert für Reasoning, Agenten-Orchestrierung und Frontier-Wissensarbeit. Verfügbar als Open Weights auf Hugging Face.

**Stärken:** Open Weights mit NVIDIA Open Model License – kommerzielle Nutzung erlaubt · 550B MoE-Architektur mit 55B aktiven Parametern – effiziente Inferenz bei Frontier-Kapazität · Hybrid Transformer-Mamba-Architektur für hohe Throughput-Effizienz · 1M-Token-Kontextfenster mit Reasoning- und Tool-Use-Support · Speziell für Agent-Orchestrierung und Multi-Step-Reasoning optimiert
**Einschränkungen:** Hoher Hardware-Aufwand trotz MoE (550B total) – Multi-GPU-Server erforderlich · US-Anbieter (NVIDIA) – Datenschutz bei API-Nutzung zu prüfen · Knowledge Cutoff Juni 2026 – möglicherweise nicht tagesaktuell · Im Vergleich zu M1/M2.7-Varianten komplexer aufzusetzen wegen MoE + Mamba-Hybrid

---

### OpenAI o1
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

OpenAI o1 ist OpenAIs erstes dediziertes Reasoning-Modell – trainiert auf internem Chain-of-Thought und ausgelegt auf komplexe Mathematik-, Logik- und Wissenschaftsaufgaben. Es ist ausschließlich über die OpenAI-API verfügbar und eignet sich besonders dort, wo gründliches mehrstufiges Schlussfolgern wichtiger ist als niedrige Latenz.

**Stärken:** Herausragende Leistung bei komplexen mathematischen und logischen Aufgaben · Robustes mehrstufiges Schlussfolgern durch internes Chain-of-Thought · Starke Leistung bei wissenschaftlichen und programmiertechnischen Problemstellungen
**Einschränkungen:** Deutlich langsamer und teurer als GPT-4o durch internen Reasoning-Overhead · Kein Zugriff auf Echtzeit-Informationen; Wissenstand auf Trainings-Cutoff begrenzt

---

### o3-mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

o3-mini ist OpenAIs kompaktes Reasoning-Modell mit internem Chain-of-Thought, spezialisiert auf STEM-Aufgaben, Mathematik und Coding. Die Reasoning-Intensität lässt sich in drei Stufen einstellen. Es ist ausschließlich über die OpenAI-API verfügbar – eine kosteneffiziente Option für rechenintensive Denkaufgaben.

**Stärken:** Herausragende Leistung bei mathematischen und wissenschaftlichen Reasoning-Aufgaben · Drei einstellbare Reasoning-Intensitätsstufen (low, medium, high) für Kosten-Leistungs-Optimierung · Deutlich schneller und günstiger als o3
**Einschränkungen:** Kein nativer Multimodal-Support (kein Bild-Input in der Basisversion) · Schwächer als größere Modelle bei kreativen, nuancierten Sprach- und Schreibaufgaben

---

### o4-mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** reasoning

o4-mini ist OpenAIs kompaktes Reasoning-Modell mit internem Chain-of-Thought, ausgelegt auf mathematisches, wissenschaftliches und logisches Schlussfolgern. Es ist ausschließlich über die OpenAI-API verfügbar und bietet starke Reasoning-Qualität bei geringerer Latenz und niedrigeren Kosten als größere Modelle der o-Series.

**Stärken:** Herausragende Leistung bei Mathematik, Naturwissenschaften und formalem Schlussfolgern · Deutlich schneller und kostengünstiger als o3 bei vergleichbarer Reasoning-Qualität · Starke Coding-Fähigkeiten durch integriertes Chain-of-Thought-Training
**Einschränkungen:** Kein Zugriff auf Modellgewichte – ausschließlich über OpenAI-API nutzbar · Kann bei kreativen, offenen oder nuancierten Sprachaufgaben hinter generalistischen Modellen zurückbleiben

---

### Qwen 2.5 Coder 7B (llama.cpp, Q6_K)
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** coding

Qwen 2.5 Coder 7B ist ein auf Code spezialisiertes Open-Weights-Modell von Alibaba (China), lokal via llama.cpp betrieben. Es unterstützt Code-Generierung, Debugging und Erklärungen für gängige Sprachen. Läuft hier als Q6_K-GGUF. Q6_K (6-Bit-K-Quant) gilt als nahezu verlustfrei gegenüber FP16 und wird von der Community als sehr hochwertige Quantisierung für lokale Nutzung empfohlen.

**Stärken:** Starke Code-Generierung und Vervollständigung in gängigen Sprachen wie Python, JavaScript, Java und C++ · Kompakte 7B-Größe ermöglicht effiziente lokale Ausführung auf Consumer-Hardware · Q6_K: nahezu verlustfreie Qualität gegenüber FP16 – Community-Bewertung: sehr gutes Qualitäts-/Größenverhältnis
**Einschränkungen:** Bei sehr komplexen, mehrstufigen Architekturentscheidungen stoßen 7B-Modelle schnell an Kontextgrenzen · Nicht-technische oder kreative Aufgaben werden deutlich schwächer abgedeckt als bei General-Purpose-Modellen

---

### Qwen 3 14B (llama.cpp, Q6_K)
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 14B ist ein Open-Weights-Modell von Alibaba (China) für allgemeine Sprach- und Reasoning-Aufgaben mit optionalem Thinking-Modus. Läuft hier als Q6_K-GGUF via llama.cpp. Q6_K (6-Bit-K-Quant) gilt als nahezu verlustfrei gegenüber FP16/BF16 und wird von der Community als sehr hochwertige Quantisierung für lokale Nutzung eingestuft.

**Stärken:** Optionaler Chain-of-Thought-Modus (Thinking-Optional) für komplexe Reasoning-Aufgaben zuschaltbar · Gute Balance zwischen Modellgröße und Leistung – lokal auf Consumer-Hardware betreibbar · Q6_K: nahezu verlustfreie Qualität, Community-empfohlen als Standard-Quant für Qualitätspriorität
**Einschränkungen:** Kann in sensiblen politischen Themen mit Bezug zu China zensierte oder ausweichende Antworten liefern · Thinking-Modus erhöht Latenz und Token-Verbrauch deutlich – bei einfachen Aufgaben ineffizient

---

### Qwen 3 4B (llama.cpp, Q6_K)
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 4B ist ein kompaktes Open-Weights-Modell von Alibaba (China) mit optionalem Thinking-Modus (Chain-of-Thought an-/abschaltbar). Läuft hier als Q6_K-GGUF via llama.cpp. Q6_K (6-Bit-K-Quant) gilt als nahezu verlustfrei und wird von der Community als sehr gute Wahl für maximale Qualität im kompakten Format bewertet.

**Stärken:** Optionaler Thinking-Modus (Chain-of-Thought an-/abschaltbar) für komplexere Aufgaben · Sehr ressourceneffizient – läuft auf Consumer-Hardware mit minimalem VRAM-Bedarf · Q6_K: nahezu verlustfreie Qualität gegenüber FP16 – besonders bei einem 4B-Modell spürbar
**Einschränkungen:** Als 4B-Modell bei komplexen Reasoning- und Wissensaufgaben deutlich schwächer als größere Modelle · Kann bei sensiblen politischen Themen mit China-Bezug zensierte oder ausweichende Antworten liefern

---

### Qwen 3 Coder 30B-A3B Instruct Q8_K_XL (GGUF)
**Entwickler:** Alibaba Group (Qwen Team) · **Herkunft:** China · **Fokus:** coding

Qwen 3 Coder 30B-A3B Instruct ist ein auf Code spezialisiertes MoE-Modell von Alibaba (China) mit Apache-2.0-Lizenz. 30.5B total / 3.3B aktiv, 256K Kontext. Q8_K_XL-GGUF: präziseste Quantisierung mit minimalem Qualitätsverlust. Native Multimodalität: Text, Bild, Audio.

**Stärken:** UD-Q8_K_XL-Quantisierung: nahezu verlustfrei gegenüber FP16-Baseline · Spezialisiert auf Code-Generierung, -Verständnis und -Debugging · Unterstützt 80+ Programmiersprachen · Function Calling für Tool-Integration · Extrem effiziente MoE-Architektur (30.5B total / 3.3B aktiv) · 256K Kontextfenster – ideal für große Codebasen · Apache 2.0 Lizenz – kommerzielle Nutzung erlaubt
**Einschränkungen:** Chinesische Herkunft mit potenziellen Compliance-Risiken (NSL) · MoE-Architektur erfordert schnelle GPU-Bandbreite für optimale Performance · Code-spezifisch – weniger optimiert für allgemeine Dialogaufgaben · Wissensstand auf Mai 2025

---

### Qwen 3 Coder Next Q4_K_XL (GGUF)
**Entwickler:** Alibaba Group (Qwen Team) · **Herkunft:** China · **Fokus:** coding

Qwen3-Coder-Next ist ein auf Code spezialisiertes MoE-Modell von Alibaba (China) mit Apache-2.0-Lizenz. Es nutzt 80B Gesamtparameter, davon nur 3B aktiv pro Token dank Hybrid-Gated-DeltaNet-Architektur. 256K Kontextfenster, SWE-Bench Verified: 70.6%. Kein Thinking-Modus, aber starke Agentic Capabilities für Coding-Agents und IDE-Integration.

**Stärken:** Extrem effiziente MoE-Architektur (80B total / 3B aktiv) – Hybrid-Gated-DeltaNet · Starke Agentic Capabilities: langfristiges Reasoning, komplexe Tool-Nutzung, IDE-Integration · Hohes Benchmark-Ergebnis (SWE-Bench Verified: 70.6%) für ein offenes Coding-Modell · 256K Kontextfenster – ideal für große Codebasen
**Einschränkungen:** Chinesische Herkunft mit potenziellen Compliance-Risiken (NSL) · Q4-Quantisierung führt zu höherem Qualitätsverlust als Q8-Varianten · Kein Thinking-Modus verfügbar · Code-spezifisch – weniger optimiert für allgemeine Dialogaufgaben

---

### Qwen 3 Coder Next Q8_K_XL (GGUF)
**Entwickler:** Alibaba Group (Qwen Team) · **Herkunft:** China · **Fokus:** coding

Qwen3-Coder-Next ist ein auf Code spezialisiertes MoE-Modell von Alibaba (China) mit Apache-2.0-Lizenz. Es nutzt 80B Gesamtparameter, davon nur 3B aktiv pro Token dank Hybrid-Gated-DeltaNet-Architektur. 256K Kontextfenster, SWE-Bench Verified: 70.6%. Kein Thinking-Modus, aber starke Agentic Capabilities für Coding-Agents und IDE-Integration. Diese Variante ist als Q8_K_XL Unsloth-Dynamic-Quant in 3 GGUF-Shards aufgeteilt (~81 GB total) und läuft auf Hardware mit großem Unified-Memory (DGX Spark, 128 GB).

**Stärken:** Extrem effiziente MoE-Architektur (80B total / 3B aktiv) – Hybrid-Gated-DeltaNet · Starke Agentic Capabilities: langfristiges Reasoning, komplexe Tool-Nutzung, IDE-Integration · Hohes Benchmark-Ergebnis (SWE-Bench Verified: 70.6%) für ein offenes Coding-Modell · 256K Kontextfenster – ideal für große Codebasen · Q8_K_XL-Quantisierung: nahezu verlustfrei gegenüber FP16-Baseline (deutlich weniger Qualitätsverlust als Q4-Variante)
**Einschränkungen:** Chinesische Herkunft mit potenziellen Compliance-Risiken (NSL) · Multi-File-GGUF (3 Shards, ~81 GB total) – nur auf Workstation/Server-Hardware mit ≥96 GB Unified-Memory lauffähig · Kein Thinking-Modus verfügbar · Code-spezifisch – weniger optimiert für allgemeine Dialogaufgaben

---

### Qwen 3.5 35B-A3B Q4_K_XL (GGUF)
**Entwickler:** Alibaba Group (Qwen Team) · **Herkunft:** China · **Fokus:** general

Qwen 3.5 35B-A3B ist ein multimodales MoE-Modell von Alibaba (China) mit Apache-2.0-Lizenz. 35B total / 3B aktiv, 262K Kontext, Thinking-Modus. Q4_K_XL-GGUF: gute Balance zwischen Größe und Qualität. Native Multimodalität: Text, Bild, Audio.

**Stärken:** Q4_K_XL-Quantisierung: gute Balance zwischen Größe und Qualität – ideal für GPUs mit begrenztem VRAM · Extrem effiziente MoE-Architektur (35B total / nur 3B aktiv) für schnelle Inferenz · Multimodal mit nativem Bildverständnis (Vision) · Thinking Preservation – behält Denkkette auch nach System-Prompt-Wechsel · Apache 2.0 Lizenz – kommerzielle Nutzung erlaubt · Geringerer Speicherbedarf ermöglicht Deployment auf Consumer-Hardware
**Einschränkungen:** Chinesische Herkunft mit potenziellen Compliance-Risiken (NSL) · Q4-Quantisierung führt zu höherem Qualitätsverlust als Q8-Varianten · MoE-Architektur erfordert schnelle GPU-Bandbreite für optimale Performance · Vision-Fähigkeiten bei Text-only-Deployments nicht nutzbar · Vorgängermodell – Qwen 3.6 bietet verbesserte Fähigkeiten

---

### Qwen 3.5 35B-A3B Q8_K_XL (GGUF)
**Entwickler:** Alibaba Group (Qwen Team) · **Herkunft:** China · **Fokus:** general

Qwen 3.5 35B-A3B ist ein multimodales MoE-Modell von Alibaba (China) mit Apache-2.0-Lizenz. 35B total / 3B aktiv, 262K Kontext, Thinking-Modus. Q8_K_XL-GGUF: präziseste Quantisierung mit minimalem Qualitätsverlust. Native Multimodalität: Text, Bild, Audio.

**Stärken:** Extrem effiziente MoE-Architektur (35B total / nur 3B aktiv) für schnelle Inferenz · UD-Q8_K_XL-Quantisierung: nahezu verlustfrei gegenüber FP16-Baseline · Multimodal mit nativem Bildverständnis (Vision) · Thinking Preservation – behält Denkkette auch nach System-Prompt-Wechsel · Starkes Instruction-Following, Reasoning und mehrsprachige Unterstützung · Apache 2.0 Lizenz – kommerzielle Nutzung erlaubt
**Einschränkungen:** Chinesische Herkunft mit potenziellen Compliance-Risiken (NSL) · MoE-Architektur erfordert schnelle GPU-Bandbreite für optimale Performance · Vision-Fähigkeiten bei Text-only-Deployments nicht nutzbar · Vorgängermodell – Qwen 3.6 bietet verbesserte Fähigkeiten

---

### Qwen 3.5 4B (llama.cpp, UD-Q4_K_XL)
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 4B ist ein kompaktes Open-Weights-Modell von Alibaba (China) mit Thinking-Optional-Architektur. Läuft hier als UD-Q4_K_XL-GGUF via llama.cpp. UD (Unsloth Dynamic) nutzt eine XL-Wichtigkeitsmatrix für wichtigkeitsbasierte, gemischte Bittiefenverteilung pro Schicht.

**Stärken:** Optionaler Thinking-Modus (Chain-of-Thought) für komplexere Aufgaben zuschaltbar · UD-Q4_K_XL: Unsloth-Dynamic-Quantisierung – wichtigkeitsbasierte, gemischte Bittiefenverteilung pro Schicht · Kleinste Variante der drei Qwen3.5-4B-Quants – minimal VRAM-Bedarf
**Einschränkungen:** 4-Bit-Quantisierung zeigt bei sehr langen Kontexten und komplexem Reasoning messbare Qualitätseinbußen vs. Q8 · Kann bei sensiblen politischen Themen mit China-Bezug zensierte oder ausweichende Antworten liefern

---

### Qwen 3.5 4B (llama.cpp, UD-Q6_K_XL)
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 4B ist ein kompaktes Open-Weights-Modell von Alibaba (China) mit Thinking-Optional-Architektur. Läuft hier als UD-Q6_K_XL-GGUF via llama.cpp. UD-Q6_K_XL (Unsloth Dynamic, 6-Bit, XL-Wichtigkeitsmatrix) gilt als nahezu verlustfrei gegenüber FP16 – empfohlene mittlere Variante für hohe Qualität bei vertretbarem Speicherbedarf.

**Stärken:** Optionaler Thinking-Modus (Chain-of-Thought) für komplexere Aufgaben zuschaltbar · UD-Q6_K_XL: nahezu verlustfreie Unsloth-Dynamic-Quantisierung – Community empfiehlt diese Stufe für beste lokale Qualität · Gutes Gleichgewicht zwischen Qualität (Q6) und Größe für ein 4B-Modell
**Einschränkungen:** Als 4B-Modell bei komplexen Reasoning- und Wissensaufgaben deutlich schwächer als größere Modelle · Kann bei sensiblen politischen Themen mit China-Bezug zensierte oder ausweichende Antworten liefern

---

### Qwen 3.5 4B (llama.cpp, UD-Q8_K_XL)
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 4B ist ein kompaktes Open-Weights-Modell von Alibaba (China) mit Thinking-Optional-Architektur. Läuft hier als UD-Q8_K_XL-GGUF via llama.cpp. UD-Q8_K_XL (Unsloth Dynamic, 8-Bit, XL-Wichtigkeitsmatrix) entspricht praktisch der Vollpräzision – höchste Qualitätsstufe der drei 4B-Varianten, für Vergleichsläufe als Referenz geeignet.

**Stärken:** Optionaler Thinking-Modus (Chain-of-Thought) für komplexere Aufgaben zuschaltbar · UD-Q8_K_XL: praktisch identisch mit BF16-Vollpräzision – kein messbarer Qualitätsverlust durch Quantisierung · Referenz-Variante der 4B-Quant-Reihe für direkte Qualitätsvergleiche
**Einschränkungen:** Höchster VRAM-Bedarf der drei 4B-Varianten – für Edge-Geräte mit knappem Speicher weniger geeignet · Als 4B-Modell bei komplexen Reasoning-Aufgaben deutlich schwächer als größere Modelle

---

### Qwen 3.5 9B (llama.cpp, UD-Q6_K_XL)
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 9B ist ein Open-Weights-Modell von Alibaba (China) für allgemeine Sprach- und Reasoning-Aufgaben mit optionalem Thinking-Modus. Läuft hier als UD-Q6_K_XL-GGUF via llama.cpp. UD-Q6_K_XL (Unsloth Dynamic, 6-Bit, XL-Wichtigkeitsmatrix) gilt als nahezu verlustfrei – Community-Bewertung: sehr hochwertige Quantisierung, die Standard-Q6 meist übertrifft.

**Stärken:** Optionaler Chain-of-Thought-Modus (Thinking-Optional) für anspruchsvolle Aufgaben zuschaltbar · Gutes Verhältnis von Modellgröße zu Leistung im 9B-Segment · UD-Q6_K_XL: nahezu verlustfreie Unsloth-Dynamic-Quant – Community empfiehlt diese Stufe für beste Qualität
**Einschränkungen:** Kann bei komplexen, langen Reasoning-Ketten ohne aktiviertes Thinking an Grenzen stoßen · Mögliche Zensur oder Auslassungen bei politisch sensiblen Themen mit Bezug zu China

---

### Qwen 3.5 397B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 397B ist Alibabas großes Open-Weights-Modell aus China. Die Weights sind frei verfügbar und das Modell ist über Cloud-Provider kostengünstig nutzbar; für den lokalen Betrieb wird erhebliche Server-Hardware benötigt. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Sehr hohe Kapazität durch 397B Parameter für komplexe Reasoning-Aufgaben · Starke Mehrsprachigkeit, insbesondere Chinesisch und Englisch · Robustes Instruction-Following bei langen und strukturierten Prompts
**Einschränkungen:** Ausschließlich als Cloud-Dienst verfügbar, keine lokale Ausführung möglich · Mögliche Zensur oder Einschränkungen bei politisch sensiblen Themen mit China-Bezug

---

### Qwen 3.6 35B-A3B Q8_K_XL (GGUF)
**Entwickler:** Alibaba Group (Qwen Team) · **Herkunft:** China · **Fokus:** general

Qwen 3.6 35B-A3B ist ein multimodales MoE-Modell von Alibaba (China) mit Apache-2.0-Lizenz. 35B total / 3B aktiv, 262K Kontext, Thinking-Modus. Q8_K_XL-GGUF: präziseste Quantisierung mit minimalem Qualitätsverlust. Native Multimodalität: Text, Bild, Audio.

**Stärken:** Extrem effiziente MoE-Architektur (35B total / nur 3B aktiv) für schnelle Inferenz · UD-Q8_K_XL-Quantisierung: nahezu verlustfrei gegenüber FP16-Baseline · Multimodal mit nativem Bildverständnis (Vision) · Thinking Preservation – behält Denkkette auch nach System-Prompt-Wechsel · Starkes Instruction-Following, Reasoning und mehrsprachige Unterstützung · Apache 2.0 Lizenz – kommerzielle Nutzung erlaubt
**Einschränkungen:** Chinesische Herkunft mit potenziellen Compliance-Risiken (NSL) · MoE-Architektur erfordert schnelle GPU-Bandbreite für optimale Performance · Vision-Fähigkeiten bei Text-only-Deployments nicht nutzbar

---

### Qwen 3.6 35B-A3B Uncensored HauhauCS Aggressive Q8_K_P (GGUF)
**Entwickler:** Alibaba Group (Qwen Team) / HauhauCS (Community Fine-Tune) · **Herkunft:** China · **Fokus:** general

Qwen 3.6 35B-A3B Uncensored HauhauCS Aggressive ist eine Community-Fine-Tune-Variante des Qwen 3.6 35B-A3B. Es läuft hier als Q8_K_XL-GGUF via llama.cpp. Q8_K_XL (8-Bit-K-Quant, XL) ist die präziseste GGUF-Quantisierung mit minimalem Qualitätsverlust. MoE-Architektur: 35B Gesamtparameter, nur 3,8B aktiv – hoher Durchsatz bei geringem Inferenz-Overhead. Native Multimodalität: Text, Bild, Audio.

**Stärken:** Q8_K_P-Quantisierung: per-layer Quantisierung nahe FP16-Vollpräzision · Vollständig ungefiltert – keine Safety-Refusals oder Inhaltsblockaden · imtagetraining für Aggressivität – direkte, ungeschönte Antworten · MoE-Architektur (35B total / 3B aktiv) für effiziente Inferenz · Multimodal mit nativem Bildverständnis (Vision) · Apache 2.0 Basis-Lizenz – kommerzielle Nutzung der Basis erlaubt
**Einschränkungen:** Uncensored – keine Inhaltsfilterung, potenziell problematische Ausgaben · Community-Fine-Tune ohne offizielle Qualitäts- oder Sicherheitsgarantie · Chinesische Herkunft mit potenziellen Compliance-Risiken (NSL) · MoE-Architektur erfordert schnelle GPU-Bandbreite für optimale Performance · Kein offizielles Support- oder Update-Garantie von HauhauCS

---

### Qwen 3 32B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 32B ist ein Open-Weights-Modell von Alibaba aus China – ausgelegt auf allgemeines Reasoning, Coding und mehrsprachige Aufgaben. Es ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke mehrsprachige Fähigkeiten, insbesondere für Chinesisch und Englisch · Optionales Thinking-Modus ermöglicht tieferes Reasoning bei komplexen Aufgaben · Gute Balance zwischen Modellgröße und Leistung für lokales Deployment
**Einschränkungen:** Kann bei politisch sensiblen Themen mit Bezug zu China zensierte oder ausweichende Antworten liefern · Thinking-Modus erhöht Latenz und Token-Verbrauch deutlich

---

### Qwen 3.5 397B A17B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3.5 397B A17B ist Alibabas Flaggschiff-MoE-Modell mit 397 Mrd. Parametern (17 Mrd. aktiviert) und nativer Multimodalität (Text, Bild, Video). Das Modell kombiniert Gated Delta Networks mit Sparse MoE für hocheffiziente Inferenz. Es bietet starke Leistung bei Reasoning, Coding, Agentic Tasks und visuellem Verständnis. Über OpenRouter verfügbar mit ermäßigten Preisen auf Standardtarifen. Chinesische Herkunft und NSL sind bei der Datenrisikoeinschätzung zu berücksichtigen.

**Stärken:** 397B Parameter MoE (17B aktiviert) für exzellente Kapazität bei effizienter Inferenz · Native Multimodalität: Text, Bild und Video Input · 262K Token Kontextfenster, erweiterbar auf 1.01M Token · Starke Leistung in Coding, Reasoning und Agentic Tasks · Open Weights unter Apache 2.0, lokale Bereitstellung möglich via vLLM/SGLang · Unterstützt Thinking- und Non-Thinking-Modus
**Einschränkungen:** Chinesische Herkunft: potenzielle Zensur bei politisch sensiblen Themen mit China-Bezug · Lokale Bereitstellung erfordert erhebliche Hardware (Multi-GPU) · OpenRouter-Routing kann je nach Provider variieren · Gelegentliche leere API-Antworten via OpenRouter (response_length=0 trotz gesetztem Token-Budget) – beobachtet bei cultural_intel_005; bei einem Retest behoben

---

### Qwen 3.6 Plus
**Entwickler:** Alibaba Cloud (Qwen Team) · **Herkunft:** China · **Fokus:** agentic

Qwen 3.6 Plus ist Alibabas proprietäres Frontier-Modell aus der Qwen-3.6-Serie, primär für agentische Coding- und Tool-Use-Workflows optimiert. Hybrid-Architektur kombiniert effiziente lineare Attention mit Sparse-MoE-Routing. Multimodal mit Text-, Bild- und Video-Eingabe, 1M-Token-Kontextfenster, optionaler Thinking-Modus, Tool-Use-Support. Verfügbar als API-only-SKU, Preise $0.325 Input / $1.95 Output pro 1M Tokens.

**Stärken:** Hybrid lineare Attention + Sparse MoE für hohe Inferenz-Effizienz bei Frontier-Kapazität · 1M-Token-Kontextfenster mit multimodalen Eingaben (Text + Bild + Video) · Optimiert für agentische Coding- und Multi-Step-Tool-Workflows · Optionaler Thinking-Modus für Reasoning-intensive Aufgaben · Starke Verbesserungen gegenüber Qwen 3.5-Serie in Coding und Tool-Use
**Einschränkungen:** Proprietäre API: keine Gewichte verfügbar, vollständige Abhängigkeit von Alibaba-Infrastruktur · Chinesische Herkunft (NSL): potenzielle Zensur bei politisch sensiblen Themen mit China-Bezug · Datenschutz: Nutzerdaten werden auf chinesischen Servern verarbeitet (BSI-Warnung 2025) · Im Vergleich zu Qwen 3.7 Max (Nachfolger) bereits überholt

---

### Qwen 3.7 Max
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** agentic

Qwen 3.7 Max ist das proprietäre Flagship-Modell der Qwen-3.7-Serie von Alibaba Cloud und auf agentische Workloads mit Stärken in Coding, Produktivitätsaufgaben und langfristiger autonomer Ausführung ausgelegt. Das Modell bietet ein 1M-Token-Kontextfenster, unterstützt Prompt Caching und wird über Cloud-API bereitgestellt. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Exzellente Leistung bei agentischen Coding-Aufgaben und Tool-Use · Optimiert für lange, autonome Task-Chains (long-horizon execution) · Unterstützt explizites Prompt-Caching für effiziente wiederholte Kontexte · 1M-Token-Kontextfenster mit bis zu 65.5K Output-Tokens · Deutliche Verbesserungen gegenüber früheren Qwen-Generationen in Coding und Agentic Tasks
**Einschränkungen:** Ausschließlich über Cloud-API verfügbar, kein lokaler Betrieb möglich · Keine Open Weights, vollständige Abhängigkeit von Alibaba-Infrastruktur · Chinesische Herkunft birgt potenzielle Zensur bei politisch sensiblen Themen mit China-Bezug · OpenRouter-Tool-Use und Thinking-Verhalten können provider- oder routingabhängig variieren

---

### GLM 4.6
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM-4.6 ist ein Sprachmodell von Zhipu AI (Z-AI) aus China – ausgelegt auf allgemeine Sprach- und Reasoning-Aufgaben. Das Modell ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke Chinesisch- und Englischkompetenz durch gezieltes mehrsprachiges Training · Gute Instruktionsbefolgung und Dialogfähigkeit · Open-Weights-Verfügbarkeit ermöglicht lokalen, datenschutzkonformen Betrieb
**Einschränkungen:** Leistung in weniger verbreiteten Sprachen deutlich schwächer als in Chinesisch/Englisch · Kann bei politisch sensiblen Themen mit Bezug zu China eingeschränkte oder ausweichende Antworten liefern

---

### GLM-4.7
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM-4.7 ist ein iteratives Update der GLM-4-Reihe von Zhipu AI (Z-AI) aus China – ausgelegt auf allgemeine Sprach- und Reasoning-Aufgaben. Das Modell ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke Leistung in chinesisch-englischen bilingualen Aufgaben · Gute Instruktionsbefolgung für allgemeine Dialog- und Assistenzaufgaben · Open-Weights-Verfügbarkeit ermöglicht lokalen Betrieb ohne Cloud-Abhängigkeit
**Einschränkungen:** Kann bei westlich-kulturellen Kontexten oder nicht-chinesischen Sprachen schwächer abschneiden als bei Chinesisch · Mögliche Zensur oder Zurückhaltung bei politisch sensiblen Themen mit Bezug zu China

---

### GLM-5 (2026-02-11)
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** coding

GLM-5 ist Z.ais Flaggschiff-Open-Source-Foundation-Model, veröffentlicht am 11. Februar 2026. Konzipiert für komplexe System-Design-Aufgaben und langlaufende Agenten-Workflows. Produktionsreife Leistung bei großskaligen Programmieraufgaben, vergleichbar mit führenden Closed-Source-Modellen. Mixture-of-Experts-Architektur (wie GLM-4.5/4.6), 202K-Token-Kontext, Reasoning-Support. Gewichte verfügbar auf Hugging Face.

**Stärken:** Open Weights: vollständig offen für lokales Deployment und kommerzielle Nutzung · Mixture-of-Experts-Architektur für effiziente Inferenz · Frontier-codierende Leistung – vergleichbar mit führenden Closed-Source-Modellen · Optimiert für komplexe System-Design- und Agent-Workflows · 202K-Token-Kontextfenster für langlaufende Aufgaben
**Einschränkungen:** Chinesische Herkunft (Zhipu AI) mit Compliance-Risiken (NSL) · Custom Z.ai License – kommerzielle Nutzung mit Lizenzbedingungen, weniger Standard als Apache 2.0 · Im Vergleich zu GLM-5.1 (April 2026) bereits von Nachfolger überholt · Detailed architecture specs (parameter counts) bisher nicht offiziell publiziert

---

### GLM-5 Turbo
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM-5 Turbo ist Zhipu AIs (Z-AI) schnelle Variante des GLM-5-Modells aus China – ausgelegt auf kosteneffiziente Inferenz bei niedrigerer Latenz. Das Modell ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke Leistung in chinesischer und englischer Sprache · Schnelle Inferenz als Turbo-Variante der GLM-5-Familie · Gute Instruktionsbefolgung bei alltäglichen und geschäftlichen Aufgaben
**Einschränkungen:** Gewichte nicht öffentlich verfügbar, nur über API nutzbar · Mögliche Zensur oder Einschränkungen bei politisch sensiblen Themen gemäß chinesischer Regulierung

---

### GLM 5.1
**Entwickler:** Zhipu AI · **Herkunft:** China · **Fokus:** general

GLM-5.1 ist ein Sprachmodell von Zhipu AI (Z-AI) aus China aus der fünften GLM-Generation – ausgelegt auf allgemeine Sprachaufgaben und Reasoning. Das Modell ist über Cloud-Provider verfügbar. Chinesische Herkunft und das nationale Sicherheitsgesetz (NSL) sind bei der Einschätzung des Datenrisikos zu berücksichtigen.

**Stärken:** Starke Leistung in chinesisch- und englischsprachigen Aufgaben · Gutes Instruction-Following und Dialogverhalten · Verfügbar via OpenRouter für einfache API-Integration
**Einschränkungen:** Detaillierte technische Spezifikationen und Trainingsdaten sind nicht vollständig öffentlich dokumentiert · Leistung bei spezialisierten westlichen Tests kann hinter US-Modellen vergleichbarer Größe zurückbleiben

---
