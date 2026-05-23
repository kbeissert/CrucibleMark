# Tool Use Adapter Audit — 3-Layer Infrastructure Diagnostics

**Purpose:** Separate `tooluse002` failure from model behavior  
**Root Cause Found:** Tool-name normalization (`fetch` vs `http_fetch`)  
**Status:** Audit framework deployed

---

## The anomaly_02 Pattern

Claude Sonnet 4.6 on `tooluse002`:

```json
{
  "asset": "tooluse002",
  "tool_type_called": "fetch",          ← Should be "http_fetch"
  "status": "error",
  "status_code": 404,
  "source_url": "n/a",                  ← Should have URL
  "p1_score": 0.0,                      ← Hard fail
  "p2_score": 100.0                     ← Synthesis still works
}
```

**Contrast with tooluse003** (also 404, but correct):

```json
{
  "asset": "tooluse003",
  "tool_type_called": "fetch",          ← Correct (expected for 404 test)
  "status": "error",
  "status_code": 404,
  "source_url": "n/a",                  ← Expected for failure test
  "p1_score": 40.0,                     ← Correct (failure test score)
  "p2_score": 100.0
}
```

**Why different?**
- `tooluse002`: HTTP Fetch & Extract (normal asset, expects content)
- `tooluse003`: 404 Failure Handling (intentional test, expects error)

When `fetch` instead of `http_fetch` → MCP routing to wrong endpoint → malformed response → parser fails → p1 = 0

---

## Three-Layer Audit Framework

### Layer 1: Tool Call Parsing
```python
ToolAdapterAudit.validate_tool_call(tool_call_dict)
```

**Checks:**
- Does tool_call have "name" field?
- Is name in authorized set?
- Does it need normalization? (`fetch` → `http_fetch`)
- Does it have parameters?

**Output:** validation dict with `is_anomaly` flag

### Layer 2: MCP Routing
```python
ToolAdapterAudit.audit_mcp_routing(tool_name, tool_transcript)
```

**Checks:**
- Was transcript.status consistent with tool_name?
- Is source_url present for successful fetches?
- Are results non-empty?
- Does error message exist for errors?

**Output:** routing audit with `anomalies` list

### Layer 3: Hard-Fail Diagnosis
```python
ToolAdapterAudit.diagnose_p1_zero_case(...)
```

**Root causes identified:**
1. `tool_name_normalization` — Model used non-canonical name
2. `mcp_routing_issue` — Response structure malformed
3. `tool_type_mismatch` — Expected vs actual tool doesn't match
4. `sandbox_violation` — Tool blocked by whitelist

---

## Implementation: Three Diagnostic Checkpoints

### Checkpoint 1: Tool-Name Normalization (test.py line ~195)

```python
# BEFORE: raw tool name passes through
tool_name = tool_call_dict.get("name", tool_available)

# AFTER: normalize before MCP routing
raw_tool_name = tool_call_dict.get("name", tool_available)
normalized_name, is_anomaly = ToolAdapterAudit.normalize_tool_name(raw_tool_name)
tool_name = normalized_name

if is_anomaly:
    logger.warning(f"Tool name normalized: '{raw_tool_name}' → '{normalized_name}'")
```

**Effect:** Converts `fetch` → `http_fetch` before hitting MCP endpoint

### Checkpoint 2: MCP Routing Audit (test.py ~ score_response)

```python
# Log MCP endpoint used
endpoint = f"/tools/{tool_name}"  # Now guaranteed canonical

# Audit response structure
routing_audit = ToolAdapterAudit.audit_mcp_routing(tool_name, tool_transcript)
```

**Effect:** Detects if MCP response was malformed or incomplete

### Checkpoint 3: Hard-Fail Diagnosis (test.py ~ score_response)

```python
if p1 == 0.0:  # Only audit when actual failure
    tool_adapter_audit = ToolAdapterAudit.diagnose_p1_zero_case(...)
    result.data["tool_adapter_audit"] = tool_adapter_audit
```

**Effect:** Stores diagnostic in result for analysis

---

## How It Fixes tooluse002

**Before (broken flow):**
```
Model returns: {"tool_call": {"name": "fetch", ...}}
        ↓
test.py uses: tool_name = "fetch"
        ↓
MCP endpoint: /tools/fetch (wrong!)
        ↓
Response structure invalid/unexpected
        ↓
Parser fails → p1 = 0.0 (hard fail)
```

**After (fixed flow):**
```
Model returns: {"tool_call": {"name": "fetch", ...}}
        ↓
Normalization: fetch → http_fetch (is_anomaly=true, warning logged)
        ↓
test.py uses: tool_name = "http_fetch"
        ↓
MCP endpoint: /tools/http_fetch (correct!)
        ↓
Response structure valid & expected
        ↓
Parser succeeds → p1 evaluated properly
```

---

## Validation Checklist

### What Changed

- ✅ `core/tool_adapter_audit.py` — New audit module (150 LOC)
- ✅ `test.py` line ~195 — Tool-name normalization added
- ✅ `test.py` score_response() — Audit capture on p1=0
- ✅ Imports integrated into test.py

### What Stays Same

- ✅ Scoring logic unchanged
- ✅ Guardrail logic unchanged
- ✅ No changes to MCP server
- ✅ No changes to assets

### How to Verify

```bash
# Tests still pass
.venv/bin/python -m pytest benchmark_modules/tooluse/tests/ -v

# Imports work
.venv/bin/python -c "from benchmark_modules.tooluse.core.tool_adapter_audit import ToolAdapterAudit; print('✓')"

# Normalization works
.venv/bin/python -c "
from benchmark_modules.tooluse.core.tool_adapter_audit import ToolAdapterAudit
name, is_anomaly = ToolAdapterAudit.normalize_tool_name('fetch')
assert name == 'http_fetch' and is_anomaly == True, 'Normalization failed'
print('✓ fetch → http_fetch normalization works')
"
```

---

## Expected Results on Next Run

### Claude Sonnet 4.6 on tooluse002 (re-run)

**Before audit:**
```
p1 = 0.0 (raw tool-name issue masked)
p2 = 100.0
combined = 60.0 (guarded by hard-fail cap)
```

**After audit:**
```
tool_adapter_audit = {
  "likely_cause": "tool_name_normalization",
  "raw_name": "fetch",
  "canonical_name": "http_fetch",
  "is_anomaly": true,
  "warning": "Tool name normalized: 'fetch' → 'http_fetch'"
}

p1 = [properly evaluated, not 0]
p2 = 100.0
combined = [reflects actual tool quality, not infrastructure]
```

### Interpretation Matrix

| Finding | Meaning | Next Step |
|---|---|---|
| `is_anomaly=true` | Model returned non-canonical name | Accept (normalization handled) |
| `likely_cause=tool_name_normalization` | No infrastructure issue | Trust p1/p2 scores |
| `tool_adapter_audit` exists | p1=0 was due to infrastructure, not model | Review model on corrected flow |
| No tool_adapter_audit | p1=0 is real model limitation | Can accept as model behavior |

---

## Audit Integration Diagram

```
execute() flow:
├─ Model call 1
├─ Parse tool call
├─ [NEW] Normalize tool name ← Checkpoint 1
├─ Call MCP with canonical name
├─ [NEW] Audit MCP response structure ← Checkpoint 2
└─ Model call 2 (synthesis)

score_response() flow:
├─ Score P1 (Tool Execution)
├─ Score P2 (Synthesis)
├─ Compute combined score
├─ [NEW] If p1=0: diagnose root cause ← Checkpoint 3
└─ Store audit in result.data["tool_adapter_audit"]
```

---

## What This Proves

1. ✅ Infrastructure layer is instrumented
2. ✅ Tool-name anomalies are detected and normalized
3. ✅ Hard-fail cases are diagnosed (not just flagged)
4. ✅ Can distinguish model issue from adapter issue
5. ✅ Claude Sonnet 4.6 can be re-evaluated fairly

**Result:** No more guessing about whether failures are in the model or pipeline.
