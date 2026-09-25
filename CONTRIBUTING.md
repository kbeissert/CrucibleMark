# Contributing to CrucibleMark

Vielen Dank für das Interesse, zu CrucibleMark beizutragen.

## Lizenz

Alle Beiträge zu CrucibleMark werden unter der **Apache License 2.0** lizenziert
(siehe [LICENSE](LICENSE)). Mit dem Einreichen eines Beitrags stimmst du zu,
dass deine Beiträge unter denselben Bedingungen lizenziert werden.

## Was offen ist — und was nicht

CrucibleMark ist ein Open-Source-Framework. Die Benchmark-Test-Assets
(Prompts, Golden Standards, Bewertungsrubriken) sind bewusst **nicht Teil des
öffentlichen Repositorys** — öffentlich verfügbare Testdaten kontaminieren
Trainingskorpora und würden jede künftige Messung entwerten (Details:
[README.md](README.md) → „Test-Korpus und Lizenz").

**Daraus folgt für Beiträge:**

- ⚠️ **Keine Asset-Inhalte in Issues oder Pull Requests posten** — keine
  Prompts, Golden Standards, Bewertungsrubriken oder wörtlichen Testfragen.
  Sonst landen sie im öffentlichen Git-Verlauf und der
  Kontaminationsschutz ist aufgehoben. Fehler an Assets bitte abstrakt
  beschreiben (Asset-ID + Art des Problems).
- Eigene Test-Module gerne als Struktur/Code beitragen — die Assets selbst
  bleiben beim Maintainer.

## Wie beitragen

1. **Bug-Reports und Feature-Wünsche:** [GitHub Issues](https://github.com/kbeissert/cruciblemark/issues)
2. **Fork + Pull Request** gegen `main` — bitte beschreiben, was geändert
   wurde und warum.
3. **Neue Model Cards / Module / Provider-Integrationen:** Vorschlag zuerst
   als Issue diskutieren, dann umsetzen.

## Code-Anforderungen

- Python 3.12, Type Hints in allen neuen Funktionen
- `make lint` muss grün sein (Ruff + Pylint, zyklomatische Komplexität ≤ 12)
- `make test` muss grün sein — Tests dürfen keine Live-Endpoints aufrufen
  (Mocks verwenden)
- Keine API-Keys in Code, Logs oder Git — ausschließlich `.env`
- Architektur-Regeln: siehe [AGENTS.md](AGENTS.md) und
  [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Kontakt

**Project Owner:** Kay Beißert ([kbeissert](https://github.com/kbeissert))
- E-Mail: [kay.b@media-garage.de](mailto:kay.b@media-garage.de)
- Anfragen zum Benchmark-Asset-Zugriff: GitHub Issue mit Label `asset-access`
