# Model Cards – Alle Modelle

### Ministral 3 14B Abliterated
**Entwickler:** Community / chargoddard · **Herkunft:** France / Community · **Fokus:** reasoning

Dieses experimentelle Community-Modell basiert auf der Mistral-Architektur und wurde mittels 'Abliteration' erstellt, bei der gezielt Schichten entfernt werden. Der Fokus liegt auf der Verbesserung von logischem Denken und Effizienz. Es entstand aus dem Bestreben, durch unkonventionelle Modell-Kombinationen neue Leistungsgrenzen zu erreichen.

**Stärken:** Hohe Effizienz durch reduzierte Architektur · Starke Fähigkeiten im logischen Denken (Reasoning) · Gute Performance auf Consumer-Hardware (CPU/GPU)
**Einschränkungen:** Experimenteller Charakter kann zu unvorhersehbarem Verhalten oder Artefakten führen. · Das Entfernen von Layern kann zu Wissenslücken oder reduzierter Fakten-Treue führen.

---

### Hermes 4 14B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** instruction-following

Hermes 4 14B von Nous Research (USA) ist ein auf Anweisungen spezialisiertes Modell. Es wurde auf einem sorgfältig kuratierten Datensatz aus synthetischen und echten Daten trainiert, um komplexe Anweisungen präzise zu befolgen. Seine Stärken liegen in der Texterstellung, im logischen Denken und in der Rollenspiel-Fähigkeit. Entwickelt wurde es als leistungsstarkes, offenes Forschungsmodell.

**Stärken:** Präzises Befolgen komplexer und nuancierter Anweisungen · Hohe Qualität bei kreativen Schreibaufgaben und Rollenspielen · Starke Fähigkeiten im logischen Schließen und bei der Problemlösung
**Einschränkungen:** Kann bei sehr spezifischen Fach- oder Nischenthemen ungenaue Informationen generieren (Halluzinationen). · Die GGUF-Quantisierung (Q4_K_M) führt zu einem leichten Präzisionsverlust im Vergleich zum Originalmodell.

---

### Claude 4.5 Haiku
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** general

Claude 4.5 Haiku ist ein hypothetisches Modell von Anthropic (USA), das als schnellste und kosteneffizienteste Variante der Claude-4.5-Familie konzipiert wäre. Der Fokus liegt auf der schnellen Verarbeitung von Anfragen und der Skalierbarkeit für Echtzeitanwendungen, wie z.B. im Kundenservice, bei gleichzeitig soliden allgemeinen Fähigkeiten.

**Stärken:** Extrem hohe Verarbeitungsgeschwindigkeit und geringe Latenz · Hervorragendes Preis-Leistungs-Verhältnis für skalierbare KI-Anwendungen · Starke Leistung bei der Informationsgewinnung aus unstrukturierten Daten
**Einschränkungen:** Geringere Tiefe im logischen Schließen bei komplexen, mehrstufigen Aufgaben im Vergleich zu größeren Modellen der Familie. · Potenziell anfälliger für Faktenfehler bei Nischenthemen aufgrund einer kompakteren Wissensbasis.

---

### Claude 3.5 Sonnet
**Entwickler:** Anthropic · **Herkunft:** USA · **Fokus:** reasoning

Das von Anthropic (USA) entwickelte Modell Claude 3.5 Sonnet ist als schnelles und kosteneffizientes Spitzenmodell konzipiert. Der Fokus liegt auf anspruchsvollem Reasoning, Code-Generierung und visueller Analyse. Es wurde entwickelt, um die Intelligenz des Vorgängers Opus zu übertreffen und komplexe Aufgaben effizient zu lösen.

**Stärken:** Hochentwickeltes visuelles Verständnis (z.B. Interpretation von Diagrammen) · Überlegene Leistung bei Code-Generierung, -Bearbeitung und -Fehlerbehebung · Schnelles und nuanciertes logisches Schlussfolgern bei komplexen Problemen
**Einschränkungen:** Kann wie alle LLMs sachliche Fehler (Halluzinationen) produzieren. · Wissen ist auf den Stand der Trainingsdaten begrenzt (kein Echtzeit-Internetzugriff).

---

### DeepSeek V3.2
**Entwickler:** DeepSeek AI · **Herkunft:** China · **Fokus:** coding

DeepSeek V3.2 ist ein von DeepSeek AI in China entwickeltes Sprachmodell. Es wurde auf einem umfangreichen Datensatz mit einem starken Fokus auf Code und Mathematik trainiert, um eine hohe Kompetenz in Programmierung und logischem Denken zu erreichen. Seine Stärken liegen in der Code-Generierung und komplexen Problemlösung.

**Stärken:** Hervorragende Code-Generierung und -Vervollständigung · Starke Fähigkeiten im logischen Denken und bei mathematischen Aufgaben · Hohe Effizienz und Leistung bei vergleichsweise geringerem Ressourcenbedarf
**Einschränkungen:** Kann wie andere LLMs Fakten halluzinieren oder veraltete Informationen wiedergeben. · Obwohl mehrsprachig, ist die Leistung in weniger verbreiteten Sprachen möglicherweise nicht so robust wie in Englisch oder Chinesisch.

---

### Dolphin Mistral Nemo
**Entwickler:** Eric Hartford (cognitivecomputations) · **Herkunft:** USA · **Fokus:** instruction-following

Dolphin Mistral Nemo ist ein von Eric Hartford (USA) entwickelter Fine-Tune des Mistral-7B-v0.2. Das Modell wurde auf dem kuratierten "Nemo"-Datensatz trainiert, um Zensur zu minimieren und die Befolgung komplexer Anweisungen zu verbessern. Seine Stärken liegen in kreativen Aufgaben und detaillierten, nuancierten Antworten. Ziel war die Schaffung eines offeneren, hilfreichen KI-Assistenten.

**Stärken:** Geringe Zensur und weniger verweigerte Antworten · Hohe Kreativität bei Schreibaufgaben und Rollenspielen · Gutes Verständnis für komplexe und nuancierte Anweisungen
**Einschränkungen:** Kann potenziell schädliche, unethische oder falsche Inhalte generieren. · Als 7B-Modell anfällig für Faktenfehler (Halluzinationen) und begrenzte Tiefe bei komplexem Reasoning.

---

### Gemini 3 Flash Preview
**Entwickler:** Google · **Herkunft:** USA · **Fokus:** general

Gemini 3 Flash Preview von Google (USA) ist ein multimodales Modell, das für maximale Geschwindigkeit und Effizienz optimiert wurde. Seine Stärken liegen in schnellen, kostengünstigen Antworten für Aufgaben wie Zusammenfassungen, Chatbots oder Datenextraktion. Es wurde für hochfrequente Anwendungen mit geringer Latenz entwickelt.

**Stärken:** Hohe Geschwindigkeit und geringe Latenz für schnelle Antworten · Kosteneffizienz bei hohem Anfragevolumen und Skalierung · Starke Leistung bei Zusammenfassungen, Chat und Datenextraktion
**Einschränkungen:** Geringere Tiefe bei sehr komplexem Reasoning im Vergleich zu größeren Modellen wie Gemini 3 Pro · Als Preview-Version können sich Fähigkeiten und API noch ändern

---

### Gemini 3.1 Pro Preview
**Entwickler:** Google · **Herkunft:** USA · **Fokus:** general

Entwickelt von Google in den USA, ist Gemini 3.1 Pro auf multimodales Verständnis und komplexe Schlussfolgerungen trainiert. Seine Stärken liegen in der Verarbeitung langer Kontexte, der Code-Generierung und der Analyse von Text, Bild und Audio. Ziel der Entwicklung war ein effizienteres und vielseitigeres Modell der nächsten Generation.

**Stärken:** Langes Kontextfenster mit hoher Abrufgenauigkeit (Needle-in-a-Haystack) · Native multimodale Fähigkeiten (Text, Bild, Audio, Video) · Verbesserte Effizienz und geringere Latenz im Vergleich zu Vorgängern
**Einschränkungen:** Als Preview-Version potenziell instabil und mit unvorhersehbarem Verhalten. · Kann wie alle LLMs Fakten halluzinieren oder gesellschaftliche Vorurteile aus den Trainingsdaten reproduzieren.

---

### Gemma 3 12B Abliterated v2
**Entwickler:** Google (Base Model), bartowski (Fine-tune) · **Herkunft:** USA · **Fokus:** creative

Dieses Modell basiert auf Googles Gemma 3 12B und wurde von der Community ('bartowski') durch 'Abliteration' modifiziert. Der Fokus liegt auf der Entfernung von Zensur und Sicherheitsfiltern, um eine uneingeschränkte, kreative Texterstellung zu ermöglichen. Es eignet sich besonders für Rollenspiele und das Generieren von Inhalten ohne die üblichen KI-Leitplanken.

**Stärken:** Generiert unzensierte und weniger gefilterte Antworten · Hohe Kreativität bei Storytelling und Rollenspielen · Folgt komplexen, kreativen Anweisungen ohne moralische Bewertungen
**Einschränkungen:** Kann potenziell schädliche, voreingenommene oder anstößige Inhalte erzeugen · Geringere Fähigkeit zu komplexem logischem Schließen im Vergleich zu größeren Modellen

---

### Gemma 3 12B
**Entwickler:** Google · **Herkunft:** USA · **Fokus:** general

Gemma 3 12B ist ein von Google (USA) entwickeltes, offenes Sprachmodell. Es wurde für eine ausgewogene, hochqualitative Leistung in Logik, Codierung und mehrsprachigen Aufgaben trainiert. Seine Stärken liegen in der effizienten Inferenz und starken Performance trotz kompakter Größe, um modernste KI-Fähigkeiten zugänglicher zu machen.

**Stärken:** Hohe Leistung in Logik- und Programmier-Benchmarks für seine Größenklasse. · Effiziente Architektur, die den Einsatz auf unterschiedlicher Hardware ermöglicht. · Starke mehrsprachige Fähigkeiten durch ein diverses Trainings-Set.
**Einschränkungen:** Kann wie alle LLMs faktisch falsche Informationen generieren (Halluzinationen). · Kann in den Trainingsdaten vorhandene gesellschaftliche Vorurteile reproduzieren.

---

### GPT-4o mini
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-4o mini ist ein von OpenAI (USA) entwickeltes, multimodales Sprachmodell. Es wurde als schnellere und kostengünstigere Alternative zu GPT-4o konzipiert, um eine breite Palette von allgemeinen Aufgaben effizient zu bewältigen. Seine Stärken liegen in der schnellen Text-, Bild- und Audioverarbeitung bei solider Leistung.

**Stärken:** Hohe Kosteneffizienz und Geschwindigkeit · Native multimodale Fähigkeiten (Text, Bild, Audio) · Starke allgemeine Leistung für alltägliche Aufgaben
**Einschränkungen:** Geringere Leistungsfähigkeit bei komplexen logischen Schlussfolgerungen im Vergleich zu Top-Modellen · Potenziell weniger präzise bei sehr spezifischen oder Nischenthemen

---

### GPT-4o
**Entwickler:** OpenAI · **Herkunft:** USA · **Fokus:** general

GPT-4o von OpenAI (USA) ist ein multimodales Modell, trainiert für nahtlose Interaktion mit Text, Audio und Bild. Seine Stärken liegen in der schnellen Verarbeitung komplexer, gemischter Eingaben und hoher Leistung bei allgemeinen Aufgaben. Entwickelt wurde es für eine natürlichere und effizientere Mensch-Computer-Interaktion.

**Stärken:** Native Multimodalität (Text, Audio, Bild) in einem einzigen Modell · Geringe Latenz und hohe Geschwindigkeit, optimiert für Echtzeit-Interaktionen · Leistung auf GPT-4 Turbo-Niveau bei Text-, Logik- und Programmieraufgaben
**Einschränkungen:** Kann wie alle LLMs faktisch falsche oder unsinnige Informationen (Halluzinationen) generieren. · Die fortgeschrittenen Audio- und Bildfähigkeiten unterliegen Sicherheitsbeschränkungen und werden schrittweise eingeführt.

---

### Grok 3 Mini
**Entwickler:** xAI · **Herkunft:** USA · **Fokus:** general

Grok-3-mini ist ein von xAI in den USA entwickeltes Sprachmodell. Es ist auf Effizienz und allgemeine Anwendungsfälle mit einem Schwerpunkt auf logischem Denken und Mathematik optimiert. Seine Hauptstärke ist der Echtzeit-Zugriff auf Informationen über die Plattform X. Das Modell wurde als schnelle, ressourcenschonende Alternative für alltägliche Aufgaben konzipiert.

**Stärken:** Echtzeit-Informationszugriff über die Plattform X · Solide Fähigkeiten in Logik und Mathematik · Hohe Effizienz und schnelle Antwortzeiten für alltägliche Aufgaben
**Einschränkungen:** Geringere Tiefe bei sehr komplexen, mehrstufigen Aufgaben im Vergleich zu größeren Modellen · Potenzial für unkonventionelle oder kontroverse Antworten aufgrund der Trainingsphilosophie

---

### Hermes 3 8B
**Entwickler:** Nous Research · **Herkunft:** USA · **Fokus:** reasoning

Hermes 3 8B von Nous Research ist ein Fine-Tune von Metas Llama 3 8B. Das Modell wurde auf einem großen, kuratierten Datensatz mit synthetischen, qualitativ hochwertigen Instruktionen trainiert. Seine Stärken liegen in komplexem Reasoning, Function Calling und Konversation. Ziel war die Entwicklung eines leistungsstarken Open-Source-Modells für anspruchsvolle Aufgaben.

**Stärken:** Starkes logisches Schlussfolgern und Reasoning · Exzellentes Befolgen komplexer, mehrstufiger Anweisungen · Hochwertige Konversationsfähigkeiten und kreative Texterstellung
**Einschränkungen:** Neigt wie alle Modelle dieser Größe zu faktischen Ungenauigkeiten (Halluzinationen). · Kann Voreingenommenheiten (Biases) aus dem Basismodell (Llama 3) und den Trainingsdaten übernehmen.

---

### Llama 3.3 70B Versatile
**Entwickler:** Meta · **Herkunft:** USA · **Fokus:** general

Llama 3.3 70B Versatile ist ein von Meta in den USA entwickeltes Allzweckmodell. Es baut auf der Llama-3-Architektur auf und wurde für eine ausgewogene, vielseitige Leistung über verschiedene Domänen hinweg optimiert. Zu seinen Stärken zählen nuanciertes Sprachverständnis, logisches Schlussfolgern und das Befolgen komplexer Anweisungen.

**Stärken:** Hohe allgemeine Leistungsfähigkeit und Weltwissen · Starkes logisches Schlussfolgern und Befolgen von Anweisungen · Ausgewogene Fähigkeiten in Textgenerierung, Zusammenfassung und Dialog
**Einschränkungen:** Kann wie alle LLMs sachliche Fehler (Halluzinationen) generieren. · Wissen ist auf den Stand der Trainingsdaten begrenzt (Knowledge Cutoff).

---

### MiniMax abab6.5
**Entwickler:** MiniMax · **Herkunft:** China · **Fokus:** general

Das vom chinesischen Unternehmen MiniMax entwickelte Modell ist ein leistungsstarkes Allzweck-Basismodell. Es wurde mit dem Ziel entwickelt, eine global wettbewerbsfähige KI zu schaffen, die sich durch starkes logisches Denken und das Befolgen komplexer Anweisungen auszeichnet. Seine Stärken liegen in der hochwertigen Textgenerierung auf Chinesisch und Englisch.

**Stärken:** Starkes logisches Schlussfolgern und Problemlösen · Hohe Qualität bei der Befolgung komplexer und langer Anweisungen · Exzellente Fähigkeiten in chinesischer und englischer Sprache
**Einschränkungen:** Potenzial für Faktenfehler (Halluzinationen), insbesondere bei Nischenthemen. · Wissensstand ist auf den Zeitpunkt des Trainingsdatensatzes beschränkt.

---

### Mistral Large
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** reasoning

Mistral Large ist ein in Frankreich von Mistral AI entwickeltes Flaggschiff-Modell. Es wurde für komplexe, multilinguale Aufgaben mit erstklassigen Reasoning-Fähigkeiten trainiert. Seine Stärken liegen in der logischen Schlussfolgerung, dem Code-Verständnis und der nativen Beherrschung mehrerer Sprachen.

**Stärken:** Hervorragende Reasoning-Fähigkeiten bei komplexen Aufgaben · Native Unterstützung für mehrere Sprachen (EN, FR, DE, ES, IT) · Starke Leistung bei Code-Generierung und mathematischen Problemen
**Einschränkungen:** Kann wie alle LLMs sachliche Fehler (Halluzinationen) produzieren. · Trainingsdaten haben einen Cutoff-Punkt, Wissen über sehr neue Ereignisse ist begrenzt.

---

### Mistral Medium
**Entwickler:** Mistral AI · **Herkunft:** France · **Fokus:** general

Mistral Medium ist ein proprietäres Modell von Mistral AI aus Frankreich. Es wurde als leistungsstarke und kosteneffiziente Alternative zu führenden Modellen entwickelt. Seine Stärken liegen in komplexem Reasoning, mehrsprachiger Textverarbeitung und Code-Generierung, was es zu einem vielseitigen Allrounder für anspruchsvolle Aufgaben macht.

**Stärken:** Hohe Leistung bei komplexen logischen Schlussfolgerungen (Reasoning) · Starke mehrsprachige Fähigkeiten, insbesondere in europäischen Sprachen · Effiziente und qualitativ hochwertige Code-Generierung
**Einschränkungen:** Neigt wie alle LLMs zu Halluzinationen und kann faktisch falsche Informationen generieren. · Als proprietäres Modell mangelt es an Transparenz bezüglich der Trainingsdaten und Architektur.

---

### Kimi K2 Instruct
**Entwickler:** Moonshot AI · **Herkunft:** China · **Fokus:** instruction-following

Das von Moonshot AI in China entwickelte Kimi K2 Instruct ist auf das Befolgen von Anweisungen über extrem lange Kontexte spezialisiert. Seine Stärken liegen in der Analyse und Zusammenfassung umfangreicher Dokumente, dem Code-Verständnis und der allgemeinen Konversation. Es wurde geschaffen, um komplexe Aufgaben zu lösen, die ein tiefes Verständnis großer Informationsmengen erfordern.

**Stärken:** Verarbeitung von extrem langen Kontexten (bis zu 200k Token) · Analyse und Zusammenfassung langer Dokumente, Berichte und Bücher · Präzise Befolgung komplexer, mehrstufiger Anweisungen
**Einschränkungen:** Leistung bei Sprachen außerhalb von Chinesisch und Englisch ist geringer · Neigung zu Halluzinationen oder zur Generierung sachlich falscher Informationen

---

### Qwen 2.5 Coder 7B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** coding

Qwen2.5-Coder-7B ist ein von Alibaba Cloud in China entwickeltes Sprachmodell, das speziell für Aufgaben der Softwareentwicklung trainiert wurde. Es zeichnet sich durch starke Fähigkeiten in der Codegenerierung, Fehlerbehebung und Erklärung von Code in diversen Programmiersprachen aus und wurde als leistungsstarkes Open-Source-Werkzeug für Entwickler konzipiert.

**Stärken:** Code-Generierung und -Vervollständigung in über 300 Programmiersprachen · Fähigkeit zur Fehlerbehebung (Debugging) und Erklärung von Code-Abschnitten · Unterstützung von Tool-Nutzung und Agent-Fähigkeiten für komplexe Entwicklungsaufgaben
**Einschränkungen:** Kann bei sehr komplexen, neuartigen Algorithmen oder Systemarchitekturen an Grenzen stoßen. · Generierter Code erfordert trotz hoher Qualität stets eine Überprüfung durch einen menschlichen Entwickler.

---

### Qwen 3 14B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 14B ist ein von Alibaba Cloud in China entwickeltes, vielseitiges Sprachmodell. Es wurde als leistungsstarke Open-Source-Alternative konzipiert und zeichnet sich durch exzellente mehrsprachige Fähigkeiten, starkes logisches Denken und fortgeschrittene Programmierkompetenzen aus, um eine breite Palette von Aufgaben zu bewältigen.

**Stärken:** Exzellente Mehrsprachigkeit über Englisch und Chinesisch hinaus · Starke Leistungen in den Bereichen Coding, Mathematik und logisches Denken · Unterstützung für lange Kontextfenster zur Verarbeitung umfangreicher Dokumente
**Einschränkungen:** Kann wie alle LLMs faktisch inkorrekte Informationen (Halluzinationen) generieren · Potenzielle kulturelle Voreingenommenheit, die die Trainingsdaten widerspiegelt

---

### Qwen 3 32B
**Entwickler:** Alibaba Cloud · **Herkunft:** China · **Fokus:** general

Qwen 3 32B ist ein von Alibaba Cloud in China entwickeltes, vielseitiges Sprachmodell. Es wurde auf einem breiten Datensatz trainiert, mit einem Fokus auf logisches Schließen, Programmierung und Mehrsprachigkeit. Seine Stärken liegen in der Bewältigung komplexer Aufgaben und der Unterstützung von 96 Sprachen. Ziel war die Schaffung eines leistungsstarken Open-Source-Modells.

**Stärken:** Hervorragende mehrsprachige Fähigkeiten (unterstützt 96 Sprachen) · Starke Leistung bei logischem Schließen, Mathematik und Codierungsaufgaben · Großes Kontextfenster (bis zu 128k Tokens) für die Verarbeitung langer Dokumente
**Einschränkungen:** Kann wie alle LLMs Fakten halluzinieren oder veraltete Informationen wiedergeben · Mögliche Voreingenommenheit (Bias) durch die Trainingsdaten, insbesondere bei sensiblen Themen

---
