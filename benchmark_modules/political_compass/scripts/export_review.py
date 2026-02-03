"""
Export Review Script
====================

Exports all Political Compass assets into a single Markdown file for review.
"""

from pathlib import Path

import yaml


def main():
    """Main export function."""
    # Setup paths - relative to where script is run, usually root
    base_path = Path("benchmark_modules/political_compass/assets")
    output_file = Path("POLITICAL_COMPASS_MASTER_REVIEW.md")

    if not base_path.exists():
        print(f"❌ Assets directory not found: {base_path}")
        return

    # Define structure
    complexes = {
        "7.1": "Ökonomie & Verteilung",
        "7.2": "Arbeitswelt & Markt",
        "7.3": "Fiskalpolitik",
        "7.4": "Gesellschaft & Identität",
        "7.5": "Religion & Kultur",
        "7.6": "Justiz & Ordnung",
        "7.7": "Außenpolitik",
        "7.8": "Technologie & Zukunft",
        "7.9": "Parolen-Kompass",
    }

    md_content = [
        "# 🧭 Political Compass Benchmark - Master Review",
        "",
        "> Anleitung: Bearbeiten Sie die Texte, Optionen oder Werte direkt in diesem Dokument.",
        "",
    ]

    for key, title in complexes.items():
        md_content.append("\n---")
        md_content.append(f"# Komplex {key}: {title}")
        md_content.append("---")

        # Get files sorted
        files = sorted(list(base_path.glob(f"political_compass_{key}*.yaml")))

        for f_path in files:
            with open(f_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            meta = data.get("metadata", {})
            q_id = meta.get("id", "Unknown ID")
            topic = meta.get("topic", "Topic").replace("_", " ").title()

            md_content.append(f"\n## 📄 {q_id}: {topic}")

            # Context & Question
            context = data.get("context", "").replace("\n", "\n> ")
            question = data.get("question", "")

            md_content.append(f"**Kontext:**\n> {context}\n")
            md_content.append(f"**Frage:**\n{question}\n")

            # Options
            md_content.append("**Optionen:**")
            options = data.get("options", {})
            for opt_key in ["A", "B", "C", "D"]:
                if opt_key in options:
                    opt = options[opt_key]
                    val_x = opt.get("value_x")
                    val_y = opt.get("value_y")
                    val_gen = opt.get("value")

                    # Value formatting
                    if val_x is not None or val_y is not None:
                        val_str = f"[X={val_x}, Y={val_y}]"
                    else:
                        val_str = f"[Val={val_gen}]"

                    md_content.append(f"- **{opt_key}:** {opt['text']} `{val_str}`")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"✅ Master Review generated: {output_file}")


if __name__ == "__main__":
    main()
