# Plan: Card-Research — Lizenz-Recherche & Findings-Qualität verbessern

## Problem-Analyse

### Ist-Zustand (`make card-research MODEL=gemma-4-12b-it-ud-q8_k_xl`)

Das LLM erkennt 9 Findings (6 errors, 3 warnings), aber:
1. **Kein einziges Finding hat einen `suggested`-Wert** → `_apply_research_diff()` kann nichts anwenden
2. **Die Card wird unverändert geschrieben** mit `profile_verified=true`, obwohl 6 Fehler vorliegen
3. **Lizenz-Felder (`license`, `license_url`, `weights_license_tier`) werden gar nicht geprüft**
4. **`community: "UndiX"`** ist nicht in der Taxonomie (`classification_taxonomy.json`), wird aber nicht korrigiert

### Kernursachen

| # | Ursache | Auswirkung |
|---|---------|------------|
| 1 | `_RESEARCH_SYSTEM_INSTRUCTION` ist zu generisch — erwähnt Lizenz, Community, GGUF-Pfad nicht | LLM prüft nur Preise, Context, Summary, Display-Name |
| 2 | LLM wird nicht angewiesen, `suggested`-Werte zu liefern | Findings sind reine Beschreibungen ohne Korrekturvorschläge |
| 3 | `editor_prompt` wird zwar übergeben, aber der System-Prompt leitet nicht daraus ab | GGUF-Recherchepfad, Lizenz-Regeln, Community-Kontrolle bleiben ungenutzt |
| 4 | Keine strukturierte Lizenz-Verifikationslogik im Research-Prompt | Gemma 4 = Apache 2.0 wird nie erkannt |
| 5 | `_commit_card()` setzt `profile_verified=true` unabhängig von error-Findings | Fehlerhafte Cards werden als verifiziert markiert |

### Konkretes Beispiel: `gemma-4-12b-it-ud-q8_k_xl`

| Feld | Aktuell | Korrekt (laut editor_prompt + anderen Gemma-4-Cards) |
|------|---------|------------------------------------------------------|
| `license` | "Google Gemma Terms of Use" | "Apache 2.0" |
| `license_url` | "https://ai.google.dev/gemma/terms" | "https://ai.google.dev/gemma/apache_2" oder SPDX-URL |
| `weights_license_tier` | "restricted-weights" | "open-weights" |
| `commercial_use_allowed` | true | true (korrekt) |
| `community` | "UndiX" | "Unsloth" (oder null — "UndiX" ist nicht in Taxonomie) |
| `developer` | "Google DeepMind" | "Google DeepMind" (korrekt, aber Summary/Distributortrennung fehlt) |
| `deployment_type` | "open-weights" | "localweights" (GGUF) |
| `weights_provenance_risk_rationale` | "...Gemma-Lizenz ist restriktiv..." | Muss Apache 2.0 reflektieren |

---

## Änderungen

### 1. `_RESEARCH_SYSTEM_INSTRUCTION` erweitern (`manage_model_cards.py:328-339`)

**Problem:** Der Prompt ist zu generisch. Er erwähnt keine Lizenz-Recherche, keine Community-Validierung, keinen GGUF-Pfad.

**Lösung:** System-Prompt modular erweitern mit:

```
Du bist ein Card-Researcher. Pruefe die unten angegebene Model Card auf
inhaltliche Korrektheit. Du hast den editor_prompt als Kontext — befolge
dort die Regeln für GGUF-Recherche, Lizenz-Verifikation und Community-Zuordnung.

Pflicht-Pruefungen:
1. Lizenz: Pruefe license, license_url, weights_license_tier, commercial_use_allowed
   auf Konsistenz. Lizenz darf nie aus Modellnamen abgeleitet werden —
   immer aktiv recherchieren. Nutze den editor_prompt fuer bekannte
   Lizenz-Mappings (z.B. Gemma 4 = Apache 2.0).
2. Community: Pruefe ob der community-Wert in der kontrollierten Taxonomie
   liegt (Unsloth, mradermacher, HauhauCS, ARA-APEX). Unbekannte Werte
   sind Fehler.
3. GGUF-Konsistenz: Bei GGUF-Modellen (UD, Q4, Q5, Q6, Q8, GGUF im Namen)
   muss deployment_type=localweights sein, Preise muessen null sein,
   developer darf keinen Distributor enthalten.
4. Preise, Context-Window, Knowledge-Cutoff, Display-Name, Summary.

WICHTIG: Fuer JEDES Finding MUSS ein "suggested"-Wert angegeben werden,
wenn der korrekte Wert bestimmbar ist. Nur wenn der Wert nicht
verifizierbar ist, darf suggested=null sein.

Antworte AUSSCHLIESSLICH mit JSON:
{"findings": [{"field": ..., "severity": "error|warning|info",
"message": ..., "current": ..., "suggested": ...}], "summary": "..."}.
```

### 2. `editor_prompt` konsistent in Research-Prompt einbetten (`manage_model_cards.py:711-730`)

**Problem:** `_build_research_user_prompt()` übergibt den `editor_prompt`, aber der System-Prompt referenziert ihn nicht.

**Lösung:** Im System-Prompt explizit verweisen:
```
Der unten übergebene editor_prompt enthaelt regelwerke fuer:
- GGUF-Recherchepfad (Schritt A-E)
- Lizenz-Mappings pro Modellfamilie
- Community-Kontrollwerte
- Feldspezifikationen
Befolge diese Regeln zwingend.
```

### 3. `_apply_research_diff()` erweitern (`manage_model_cards.py:687-708`)

**Problem:** Die Funktion übernimmt nur `suggested`-Werte, wenn das Zielfeld bereits existiert. Für neue Felder oder Felder, die der LLM als ganzes Objekt vorschlägt (z.B. Lizenz-Block), passiert nichts.

**Lösung:** Erweitern um:
- Auch Felder übernehmen, die in der Card fehlen (neue Felder aus Findings)
- Expliziten Lizenz-Block-Support: Wenn `license` geändert wird, automatisch `license_url`, `weights_license_tier`, `commercial_use_allowed` konsistent mitschleppen

```python
def _apply_research_diff(original: dict, response: dict) -> dict:
    findings = response.get("findings", [])
    if not isinstance(findings, list):
        return original
    merged = dict(original)
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        suggested = finding.get("suggested")
        if suggested is None:
            continue
        field = finding.get("field")
        if not field:
            continue
        merged[field] = suggested  # Auch neue Felder zulassen
    return merged
```

### 4. Lizenz-Konsistenz-Heuristik als Pre-Finding (`manage_model_cards.py`, neue Funktion)

**Problem:** Das LLM wird Lizenz-Fehler möglicherweise trotzdem nicht finden, weil es kein Wissen über Gemma 4 = Apache 2.0 hat (lokales Modell).

**Lösung:** Eine `_check_license_consistency()` Heuristik als Pre-Check (wie `_check_murks()`):

```python
_KNOWN_LICENSE_MAPPINGS: dict[str, dict] = {
    "gemma-4": {
        "license": "Apache 2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "weights_license_tier": "open-weights",
    },
    # Weitere Mappings können ergänzt werden
}

def _check_license_consistency(card: dict) -> list[CardFinding]:
    """Heuristik: Lizenz-Felder gegen bekannte Mappings prüfen."""
    findings = []
    model_id = card.get("model_id", "").lower()
    family = card.get("model_family", "").lower()
    
    for key, mapping in _KNOWN_LICENSE_MAPPINGS.items():
        if key in model_id or key in family:
            license_val = card.get("license", "")
            if license_val and license_val != mapping["license"]:
                findings.append(CardFinding(
                    field="license",
                    severity="error",
                    message=f"Lizenz '{license_val}' widerspricht bekanntem Mapping fuer {key}: '{mapping['license']}'",
                    current=license_val,
                    suggested=mapping["license"],
                ))
            tier = card.get("weights_license_tier", "")
            if tier and tier != mapping["weights_license_tier"]:
                findings.append(CardFinding(
                    field="weights_license_tier",
                    severity="error",
                    message=f"weights_license_tier '{tier}' widerspricht bekanntem Mapping fuer {key}: '{mapping['weights_license_tier']}'",
                    current=tier,
                    suggested=mapping["weights_license_tier"],
                ))
            break
    return findings
```

**Integration:** In `_research_one()` und `_research_tooluse_one()` nach `_check_murks()` aufrufen:
```python
pre_findings = _check_murks(original)
pre_findings.extend(_check_license_consistency(original))
```

### 5. Community-Validierung als Pre-Finding (`manage_model_cards.py`, neue Funktion)

**Problem:** "UndiX" ist nicht in `classification_taxonomy.json#community_groups`, wird aber nicht erkannt.

**Lösung:** `_check_community()` Heuristik:

```python
_KNOWN_COMMUNITY_GROUPS = {"Unsloth", "mradermacher", "HauhauCS", "ARA-APEX"}

def _check_community(card: dict) -> list[CardFinding]:
    findings = []
    community = card.get("community")
    if community and community not in _KNOWN_COMMUNITY_GROUPS:
        findings.append(CardFinding(
            field="community",
            severity="error",
            message=f"Community '{community}' ist nicht in der kontrollierten Taxonomie. Erlaubt: {', '.join(sorted(_KNOWN_COMMUNITY_GROUPS))}",
            current=community,
            suggested=None,  # LLM soll korrigieren
        ))
    return findings
```

### 6. `profile_verified` nicht bei error-Findings setzen (`manage_model_cards.py:863-874`)

**Problem:** `_commit_card()` setzt `profile_verified=true` unabhängig von error-Findings.

**Lösung:** Vor dem Setzen prüfen:

```python
# In _commit_card(), vor Zeile 863:
has_errors = any(f.severity == "error" for f in report.findings)
if has_errors:
    logger.warning("    ⚠️ profile_verified bleibt false — %d error-Findings vorhanden.", 
                   sum(1 for f in report.findings if f.severity == "error"))
    final["profile_verified"] = False
    final["profile_verified_at"] = None
    final["profile_verified_by"] = None
else:
    final["profile_verified"] = True
    final["profile_verified_at"] = date.today().isoformat()
    final["profile_verified_by"] = f"llm:{self.llm_spec.model}"
```

### 7. Lizenz-Mapping für Gemma, Qwen, Llama (`manage_model_cards.py`, neue Konstante)

**Scope:** Drei Familien, die häufig Lizenzwechsel zwischen Generationen haben.

```python
_KNOWN_LICENSE_MAPPINGS: dict[str, dict] = {
    # --- Gemma ---
    "gemma-4": {
        "license": "Apache 2.0",
        "license_url": "https://ai.google.dev/gemma/apache_2",
        "weights_license_tier": "open-weights",
    },
    "gemma-3": {
        "license": "Google Gemma Terms of Use",
        "license_url": "https://ai.google.dev/gemma/terms",
        "weights_license_tier": "restricted-weights",
    },
    "gemma-2": {
        "license": "Google Gemma Terms of Use",
        "license_url": "https://ai.google.dev/gemma/terms",
        "weights_license_tier": "restricted-weights",
    },
    # --- Qwen ---
    "qwen3": {
        "license": "Apache 2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "weights_license_tier": "open-weights",
    },
    "qwen3_5": {
        "license": "Apache 2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "weights_license_tier": "open-weights",
    },
    "qwen2_5": {
        "license": "Apache 2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "weights_license_tier": "open-weights",
    },
    # --- Llama ---
    "llama-4": {
        "license": "Llama 4 Community License",
        "license_url": "https://github.com/meta-llama/llama-models/blob/main/models/llama4/LICENSE",
        "weights_license_tier": "restricted-weights",
    },
    "llama-3": {
        "license": "Llama 3 Community License",
        "license_url": "https://github.com/meta-llama/llama-models/blob/main/models/llama3/LICENSE",
        "weights_license_tier": "restricted-weights",
    },
}
```

**Lizenz-URL-Konvention (Entscheidung):**
- `license`: SPDX-Name oder offizieller Lizenzname (z.B. "Apache 2.0")
- `license_url`: Hersteller-spezifische Lizenzseite (z.B. `https://ai.google.dev/gemma/apache_2`)
- Nicht SPDX-Standard-URL verwenden, sondern die URL, die der Hersteller als canonical angibt

**Matching:** Longest-Prefix-Match auf `model_id` (lowercase). Reihenfolge der Keys ist irrelevant — `gemma-4` wird vor `gemma-3` gematcht, wenn der Prefix passt.

### 8. Community-Recherche im Tool-Use-Modus (`_research_tooluse_one`)

**Problem:** "UndiX" ist möglicherweise ein Distributor oder ein Tippfehler. Das LLM kann das nur mit Web-Zugang klären.

**Lösung:** Im Tool-Use-Modus dem LLM im System-Prompt mitgeben:
```
Wenn der community-Wert nicht in der Taxonomie liegt, recherchiere
auf HuggingFace, ob es eine aktive Org/Gruppe mit diesem Namen gibt.
Beispiel: Suche nach "UndiX" auf HuggingFace.
- Wenn gefunden: community = gefundener Name
- Wenn nicht gefunden: community = null, in known_limitations dokumentieren
```

### 9. `_apply_research_diff()` — Lizenz-Block konsistent mitschleppen

**Problem:** Wenn `license` geändert wird, bleiben `license_url` und `weights_license_tier` inkonsistent.

**Lösung:** Nach `_apply_research_diff()` eine Konsistenz-Korrektur:

```python
def _ensure_license_consistency(card: dict) -> dict:
    """Wenn license geändert wurde, pruefe ob Lizenz-URL und Tier noch passen."""
    license_val = card.get("license", "")
    url = card.get("license_url", "")
    tier = card.get("weights_license_tier", "")
    
    # Apache 2.0 → open-weights
    if "Apache" in license_val and tier == "restricted-weights":
        card["weights_license_tier"] = "open-weights"
    # Proprietary/Custom → restricted-weights oder proprietary
    if "Terms of Use" in license_val and tier == "open-weights":
        card["weights_license_tier"] = "restricted-weights"
    
    return card
```

---

## Dateien

| Datei | Änderung |
|-------|----------|
| `scripts/manage_model_cards.py` | `_RESEARCH_SYSTEM_INSTRUCTION` erweitern, `_check_license_consistency()`, `_check_community()` als Pre-Findings, `_apply_research_diff()` erweitern, `_ensure_license_consistency()`, `_commit_card()` error-aware, Integration in `_research_one()` + `_research_tooluse_one()` |

## Offene Fragen (geklärt)

1. **"UndiX" vs "Unsloth":** → Research-Script soll via HuggingFace-Abfrage klären (Tool-Use-Modus) oder als Pre-Finding markieren (Standard-Modus)
2. **Lizenz-URL:** → `license: "Apache 2.0"` + `license_url: "https://ai.google.dev/gemma/apache_2"` (Hersteller-URL, nicht SPDX)
3. **Mapping-Breite:** → Gemma + Qwen + Llama (drei Familien)

---

## Status: Implementierung abgeschlossen (Runde 1 + 2)

### Runde 1 — Strukturelle Fixes (Plan-Punkte 1–9)

Alle Plan-Punkte implementiert:
- `_KNOWN_LICENSE_MAPPINGS` (Gemma 2/3/4, Qwen 2.5/3/3.5, Llama 3/4)
- `_KNOWN_COMMUNITY_GROUPS` (Unsloth, mradermacher, HauhauCS, ARA-APEX)
- `_match_family()` — Longest-Prefix-Match
- `_check_license_consistency()` + `_check_community()` als Pre-Findings
- `_ensure_license_consistency()` als Post-Apply-Korrektur
- `_commit_card()`: `profile_verified` conditional on `has_errors`
- `_commit_card()`: Apply findings directly from `report.findings` (not `parsed["findings"]`)
- System-Prompt erweitert (regular + tool-use)

### Runde 2 — Bugs aus erstem Live-Run

| Bug | Fix |
|-----|-----|
| Log `(profile_verified=true)` hardcodiert | Dynamisch `profile_verified=%s` |
| Report `profile_verified=true` hardcodiert | Neues `ResearchReport.profile_verified` Feld |
| Pre-finding `suggested`-Werte nicht angewandt | `_commit_card` iteriert `report.findings` statt `parsed["findings"]` |
| Textfelder nach Lizenz-Wechsel nicht erkannt | `_check_license_cascade()` als Post-Merge-Check (Strings + Listen) |

### Runde 3 — Textfelder als Pre-Findings (diese Session)

**Problem:** Der Live-Run zeigte, dass die LLM-Response die strukturellen Lizenz-Felder korrigierte (license, weights_license_tier, deployment_type, community), aber die **Textfelder unverändert blieben**:
- `summary`: "...restriktiver Gemma-Lizenz..."
- `strengths`: "...Gemma-Lizenz (mit Auflagen)..."
- `known_limitations`: "Gemma-Lizenz ist restriktiv..."
- `judge_context_hint`: "...Google Gemma License (restricted-weights)..."
- `weights_provenance_risk_rationale`: "...Gemma-Lizenz ist restriktiv..."

Die Post-Merge-Cascade (`_check_license_cascade`) erkannte alle 5 Felder korrekt, aber mit `suggested=None` — sie konnte nichts auto-korrigieren.

**Fix (2-teilig):**

1. **`_check_license_text_fields()` als Pre-Finding:** Prüft auf der ORIGINAL-Card ob Textfelder die alte Lizenz referenzieren, wenn das Mapping eine Änderung erzwingt. Erzeugt Pre-Findings mit `suggested=None` aber expliziter Meldung "suggested-Wert mit korrigiertem Text ist PFLICHT".

2. **System-Prompt Regel 5:** Explizite Anweisung "TEXTFELDER BEI LIZENZ-WECHSEL: Wenn sich die Lizenz ändert, MÜSSEN ALLE Textfelder aktualisiert werden... Jedes Feld braucht ein Finding mit einem KOMPLETT NEU GESCHRIEBENEN Text als suggested-Wert."

**Integration:** `_check_license_text_fields()` in beiden Research-Pfaden nach `_check_community()` eingefügt. System-Prompt in beiden Modi (regular + tool-use) + dead-code `_build_tooluse_system_instruction()` aktualisiert.

### Runde 4 — GGUF-Konventionen + profile_verified-Fix + MCP Auto-Lifecycle

**Problem:** Bei jedem Run überschrieb das LLM korrekte Werte:
- `deployment_type: localweights` → `open-weights` (falsch — `open-weights` ist ein `weights_license_tier`-Wert)
- `params_active_b: 12` → `null`
- Preise `0.0` → `null`
- `profile_verified` blieb `false` weil die Findings-Historie (inkl. bereits korrigierter Fehler) statt der finalen Karte geprüft wurde

**Fixes:**

1. **`_is_gguf_model(model_id)`** — GGUF-Erkennung via Regex: `q[2-8]_[k0-9]`, `gguf`, `-ud-`/`_ud_`

2. **`_ensure_gguf_conventions(card)`** — Post-Apply-Korrektur in `_commit_card` NACH `_ensure_license_consistency`:
   - `deployment_type` → `localweights`
   - `params_active_b` → `params_total_b` (bei Dense-Architektur)
   - `input_price_per_1m` / `output_price_per_1m` → `0.0`

3. **`profile_verified`-Logik umgestellt** — Validiert FINALE Karte statt Findings-Historie:
   - Re-runs `_check_license_consistency` + `_check_license_text_fields` + `_check_community` auf `merged`
   - Prüft Pflichtfeld-Warnings
   - `profile_verified=true` nur wenn finale Karte fehlerfrei

4. **System-Prompt:** "Preise muessen 0.0 sein" statt "null" (beide Modi)

5. **MCP Auto-Lifecycle:**
   - `_ensure_mcp_running(mcp_url)` — startet MCP automatisch wenn `TOOLUSE=1`
   - `_stop_mcp_server()` — stoppt am Ende (nur wenn gestartet)
   - `_reset_llama_context(base_url)` — KV-Cache-Reset via `POST /slots/{id}?action=reset` nach jeder Karte
   - `_check_health(url)` — Health-Check auf llama.cpp vor jeder Karte

**Ergebnis:** `make card-research MODEL=gemma-4-12b-it-ud-q8_k_xl` → `profile_verified=true`, alle Felder korrekt. GGUF-Erkennung 8/8 Tests bestanden.
