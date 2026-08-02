# Project Brief

## Projektziel

CrucibleMark ist ein LLM-Benchmark-Framework (Python 3.12), das strukturierte Tests gegen verschiedene AI-Modelle durchfuehrt, sie mit einem unabhaengigen LLM-Judge bewertet und gefuehrte Leaderboards generiert.

## Scope

- **Test-Runner:** Führe Benchmark-Module (code_quality, ux_writing, documentation, cultural_intelligence, synthesis, political_compass, tooluse, score) sequenziell gegen konfigurierte Modelle.
- **Judge-Evaluierung:** Blind-Evaluierung der Test-Ergebnisse durch ein separates LLM.
- **Leaderboard-Generierung:** Aggregation zu compact + detailed Leaderboards (CSV).
- **Card-Management:** Model Cards pro Modell mit Metadaten, Kategorien, Pricing, Provenance.
- **Web-Export:** Daten-Pipeline von Python-Export → Eleventy-Web-Site.
- **Vendor/Community-Cards:** Herstellerkarten und Community-Beitraege.

## Non-Goals

- Kein LLM-Training oder Fine-Tuning.
- Kein Frontend-Design-Erstellung (Web-Repo ist separates Repo).
- Keine Live-Chat-Integration.
- Keine Echtzeit-Dashboard-Funktionalitaet.
- Kein API-Rated-Test gegen Open-Source-APIs im Sinne von API-Bench.

## Projektrahmen

- **Start:** 2026-04 (historisch).
- **Aktuelle Version:** v5.1.0 (2026-08-02).
- **Python-Ecosystem:** Python 3.12, venv, pytest, ruff, mypy.
- **Web-Site:** separates Repo (`CrucibleMark-Web`), Eleventy (JS).
- **Konfig-Dateien:** `benchmark_config.yaml`, `provider_config.yaml`, `config.yaml`, `web_export_blacklist.yaml`.
- **Benchmark-Run-Reihenfolge:** Modelle einzeln nacheinander (sequenziell, kein Parallelismus) — Design-Constraint fuer faire Testbedingungen.
