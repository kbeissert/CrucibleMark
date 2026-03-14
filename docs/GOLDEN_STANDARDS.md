# Golden Standards: Design by Intention

Das CrucibleMark Benchmark-System nutzt **statische Golden Standards**, die direkt innerhalb der als `asset.yaml` definierten Benchmark-Assets gepflegt werden.

## Prinzip
Die Methode "Design by Intention" evaluiert Ausgaben von LLMs **nicht** mehr pauschal durch einen Text-Vergleich mit der Ausgabe eines Referenz-Modells (z.B. Mistral oder GPT-4), sondern gegen ein zuvor präzise definiertes "ideales" Lösungs-Gerüst, welches oft strukturelle, semantische oder qualitative Kern-Anforderungen (Checklisten) in purer Text-Form oder via LLM-Judge vergleicht.

- **Ort der Definition:** Der `golden_standard` wird in jeder `asset.yaml` unterhalb von `prompts` konfiguriert.
- **Validierung:** Der `LLM_Judge` verifiziert in Phase 3 die tatsächliche Ausgabe des Probanden gegen genau diese Vorgaben.

Das vorherige Konzept eines dynamischen "Reference Model Runs" (Golden Standard Model) wurde mit Version 2.1 vollständig migriert und abgelöst, da die feste Dokumentation von Absicht und Soll-Zustand exaktere und konsistentere Beurteilungen zulässt.
