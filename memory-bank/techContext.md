# Tech Context

## Configuration Architecture
- **Global Defaults**: Defined in `benchmark_config.yaml` under `defaults.generation` (e.g., `temperature: 0.1`, `repeat_penalty: 1.1`).
- **Module Overrides**: Defined in `benchmark_modules/*/config.yaml` under `generation` block.
- **Runtime Merge**: `test.py` loads global defaults, updates with module config, and passes to LLM client.

## Critical Fixes
- **Parameter Handling**: `kwargs.pop()` utilized in `test.py` to prevent `multiple values for keyword argument` errors when merging configs.
