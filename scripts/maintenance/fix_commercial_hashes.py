import csv
import shutil
import os
from pathlib import Path

# Unify strict logic for hash correction
CONTAMINATED_HASH = "812e63c4"

# Models allowed to have this hash
# Based on usage in unify_o3_mini_hashes.py and grep results
SAFE_MODELS = {"o3-mini", "gpt-5", "gpt-5-mini"}

# Known correct versions to force
FORCED_VERSIONS = {
    "claude-opus-4-5-20251101": "20251101",
    "claude-sonnet-4-5-20250929": "8717af19",
}


def fix_csv_file(file_path):
    path = Path(file_path)
    if not path.exists():
        return

    print(f"Processing {path}...")

    # Read all rows into memory to avoid read/write conflicts
    rows = []
    fieldnames = []
    has_changes = False

    try:
        with open(path, "r", newline="", encoding="utf-8", errors="replace") as f:
            # Check for header
            try:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                if (
                    not fieldnames
                    or "model" not in fieldnames
                    or "model_version" not in fieldnames
                ):
                    print(f"  Skipping {path.name}: Missing required columns")
                    return

                for row in reader:
                    model = row.get("model", "")
                    version = row.get("model_version", "")
                    original_version = version

                    # Correction Logic
                    if model in FORCED_VERSIONS:
                        if version != FORCED_VERSIONS[model]:
                            version = FORCED_VERSIONS[model]

                    elif CONTAMINATED_HASH in version:
                        if model not in SAFE_MODELS:
                            # It's contaminated.
                            # If it was concatenated (e.g., "2312-812e63c4"), try to salvage.
                            # Otherwise, clear it.
                            if version == CONTAMINATED_HASH:
                                version = ""  # Clear strictly wrong hash
                            else:
                                # Start clean approach: remove the hash string
                                version = version.replace(f"-{CONTAMINATED_HASH}", "")
                                version = version.replace(
                                    CONTAMINATED_HASH, ""
                                )  # Fallback

                    if version != original_version:
                        row["model_version"] = version
                        has_changes = True

                    rows.append(row)
            except csv.Error:
                print(f"  Skipping {path.name}: CSV Error")
                return

        if has_changes:
            # Backup original
            backup_file = path.with_suffix(path.suffix + ".bak_hash_fix")
            shutil.copy2(path, backup_file)

            # Write back
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"  Fixed {path.name} (Original backed up to {backup_file.name})")
        else:
            print(f"  No changes needed for {path.name}")

    except Exception as e:
        print(f"  Error processing {path.name}: {e}")


def main():
    base_dir = Path.cwd()

    # Target directories
    target_dirs = [base_dir / "benchmark_scores", base_dir / "backups"]

    for d in target_dirs:
        if d.exists():
            # Walk through directory to find CSVs
            for root, dirs, files in os.walk(d):
                for file in files:
                    if "csv" in file:  # matches .csv, .csv.bak, etc.
                        fix_csv_file(Path(root) / file)


if __name__ == "__main__":
    main()
