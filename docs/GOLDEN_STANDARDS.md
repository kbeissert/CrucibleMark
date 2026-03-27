# Golden Standards: Design by Intention

CrucibleMark evaluiert LLM-Ausgaben gegen **statische Golden Standards**, die direkt in den `asset.yaml`-Dateien der Benchmark-Assets gepflegt werden.

## Prinzip

Die Methode "Design by Intention" vergleicht Ausgaben nicht pauschal mit der Ausgabe eines Referenzmodells (z. B. Mistral oder GPT-4). Stattdessen prüft sie jede Antwort gegen ein zuvor präzise definiertes Lösungsgerüst. Dieses Gerüst enthält strukturelle, semantische oder qualitative Kernanforderungen – als Checkliste in Textform oder via LLM-Judge.

- **Definition:** Der `golden_standard` ist in jeder `asset.yaml` unterhalb von `prompts` konfiguriert.
- **Validierung:** Der `LLM_Judge` prüft in Phase 3 die Ausgabe des Probanden gegen genau diese Vorgaben.

Das vorherige Konzept eines dynamischen "Reference Model Runs" entfiel mit Version 2.5. Die feste Dokumentation von Absicht und Sollzustand liefert exaktere und konsistentere Beurteilungen.
