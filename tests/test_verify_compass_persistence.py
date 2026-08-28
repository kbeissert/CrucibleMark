import sys
from pathlib import Path
import json
import csv
from unittest.mock import patch

# Add root directory to sys.path so we can import from scripts
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from scripts.core.verify_compass_anomalies import run_verification  # noqa: E402
from schemas.result import BenchmarkResult  # noqa: E402

def test_verify_compass_persistence(tmp_path):
    """
    Tests if verify_compass_anomalies correctly saves the averaged data to the CSV
    after running the verification iterations.
    """
    # 1. Setup mock directories
    mock_scores_dir = tmp_path / "benchmark_scores"
    mock_scores_dir.mkdir()

    leaderboard_csv = mock_scores_dir / "political_compass_leaderboard.csv"

    # 2. Plant a mock anomaly in the dummy CSV so `get_anomalies` finds it
    with open(leaderboard_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "provider_type", "shift_distance"])
        writer.writeheader()
        writer.writerow({
            "model": "mock-test-model",
            "provider_type": "openai",
            "shift_distance": "5.0"  # This is the anomaly
        })

    # 3. Create dummy raw response representing the inner JSON
    vanilla_coord = {"x": 1.0, "y": 1.0}
    forced_coord = {"x": -8.0, "y": 8.0}

    dummy_report = {
        "runs": {
            "vanilla": {
                "coordinates": vanilla_coord,
                "x_label": "Mitte",
                "y_label": "Mitte",
            },
            "forced": {
                "coordinates": forced_coord,
                "x_label": "Extrem",
                "y_label": "Extrem",
            }
        },
        "individual_runs": [
            {"type": "vanilla", "x": 1.0, "y": 1.0, "x_label": "Mitte", "y_label": "Mitte"},
            {"type": "forced", "x": -8.0, "y": 8.0, "x_label": "Extrem", "y_label": "Extrem"}
        ],
        "model": "mock-test-model",
        "provider": "openai",
        "statistics": {"total_cost": 0.0},
        "shift": {"x": 5.0, "y": 5.0, "distance": 7.0}
    }

    dummy_benchmark_result = BenchmarkResult(
        status="success",
        scores={"total_score": 0.0},
        execution_time=1.0,
        raw_response=json.dumps(dummy_report),
        costs={"total_cost": 0.0}
    )

    # 4. Patch the dependencies to intercept real logic
    with patch("scripts.core.verify_compass_anomalies.get_anomalies") as mock_get_anomalies, \
         patch("scripts.core.verify_compass_anomalies.ConfigValidator"), \
         patch("scripts.core.verify_compass_anomalies.LLMClient"), \
         patch("scripts.core.verify_compass_anomalies.time.sleep"), \
         patch("subprocess.run"), \
         patch("scripts.core.verify_compass_anomalies.CheckpointManager"), \
         patch("scripts.core.verify_compass_anomalies.PoliticalCompassTest") as MockTestClass, \
         patch("benchmark_modules.political_compass.core.audit_logger.AuditLogWriter.write_audit_log"), \
         patch("benchmark_modules.political_compass.core.io_manager.PoliticalCompassResultManager.save_leaderboard_csv") as mock_save_csv:

        mock_get_anomalies.return_value = ["mock-test-model"]

        # Make the test execute mock return the dummy benchmark
        mock_test_instance = MockTestClass.return_value
        mock_test_instance.execute.return_value = dummy_benchmark_result

        # 5. Run the actual script logic
        run_verification(model_id="mock-test-model")

        # 6. Verify that save_leaderboard_csv was actually called
        assert mock_save_csv.called, "Data was not sent to the CSV persistence layer!"

        # Get the payload that was passed to save_leaderboard_csv
        call_args = mock_save_csv.call_args[0]
        saved_report = call_args[0]

        # 7. Assert the averaged values were injected into the payload!
        # Because we mocked 3 iterations returning EXACTLY 1.0/1.0 and -8.0/8.0, the cluster average must match!
        assert saved_report["runs"]["vanilla"]["coordinates"]["x"] == 1.0
        assert saved_report["runs"]["forced"]["coordinates"]["x"] == -8.0

        # Mathematical Hypotenuse between (1.0, 1.0) and (-8.0, 8.0) is approx 11.401
        assert "shift" in saved_report
        assert round(saved_report["shift"]["distance"], 1) == 11.4

        print("✅ Pipeline successfully reconstructed and persisted the verified results.")
