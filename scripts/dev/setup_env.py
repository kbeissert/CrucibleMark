#!/usr/bin/env python3
"""
CrucibleMark Environment Setup Script
=====================================

Versucht, die optimale Umgebung zu installieren.
1. Versucht 'Semantic Mode' (mit sentence-transformers).
2. Bei Fehler: Fallback auf 'Lightweight Mode' (nur Keyword-Matching).
"""

import subprocess
import sys
import platform
from pathlib import Path


def install_pip_requirements(req_file):
    """Führt pip install -r aus."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", req_file],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    """Main setup routine."""
    print("🔧 CrucibleMark Environment Setup")
    print("================================")
    print(f"System: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {sys.version.split()[0]}")
    print("--------------------------------")

    # Pfade definieren
    root_dir = Path(__file__).parent.parent.parent
    req_light = root_dir / "requirements.txt"
    req_semantic = root_dir / "requirements-semantic.txt"

    print("\nVersuche Installation: 🧠 SEMANTIC MODE (Empfohlen)")
    print("Dies aktiviert 'sentence-transformers' für präziseres Scoring.")

    success = install_pip_requirements(str(req_semantic))

    if success:
        print("\n✅ ERFOLG: Semantic Mode installiert!")
        print("CrucibleMark läuft jetzt mit maximaler Präzision.")
    else:
        print("\n⚠️  FEHLER bei Semantic Installation.")
        print(
            ">> Mögliche Ursache: Konflikte zwischen torch/numpy/mistralai "
            "oder fehlende Compiler."
        )
        print("\n🔄 Starte Fallback: 🪶 LIGHTWEIGHT MODE")
        print("Dies nutzt reines Keyword-Matching (sehr stabil, aber strikter).")

        success_light = install_pip_requirements(str(req_light))

        if success_light:
            print("\n✅ ERFOLG: Lightweight Mode installiert!")
            print("CrucibleMark ist einsatzbereit (ohne Semantic Similarity).")
        else:
            print("\n❌ KRITISCHER FEHLER: Auch Lightweight Installation schlug fehl.")
            sys.exit(1)


if __name__ == "__main__":
    main()
