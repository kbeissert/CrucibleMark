import pytest
import yaml
from pathlib import Path

ASSET_DIR = Path(__file__).parent.parent / "assets"


def get_assets():
    return sorted(list(ASSET_DIR.glob("asset_*.yaml")))


@pytest.mark.parametrize("asset_path", get_assets())
def test_asset_structure(asset_path):
    with open(asset_path) as f:
        data = yaml.safe_load(f)

    required_keys = [
        "metadata",
        "context",
        "prompt",
        "requirements",
        "input_text",
        "scoring",
        "testdata",
    ]
    for key in required_keys:
        assert key in data, f"Missing key {key} in {asset_path.name}"

    assert "error_detection" in data["scoring"]
    assert "solution_quality" in data["scoring"]
    assert "formatting" in data["scoring"]


@pytest.mark.parametrize("asset_path", get_assets())
def test_scoring_weights(asset_path):
    with open(asset_path) as f:
        data = yaml.safe_load(f)

    scoring = data["scoring"]
    ed_weight = scoring["error_detection"]["weight"]
    sq_weight = scoring["solution_quality"]["weight"]
    fmt_weight = scoring["formatting"]["weight"]

    assert ed_weight + sq_weight + fmt_weight == 100, (
        f"Weights do not sum to 100 in {asset_path.name}"
    )


@pytest.mark.parametrize("asset_path", get_assets())
def test_testdata_consistency(asset_path):
    with open(asset_path) as f:
        data = yaml.safe_load(f)

    testdata_issue_names = {i["issue"] for i in data["testdata"]["issues"]}

    scoring_issues = []
    ed = data["scoring"]["error_detection"]
    scoring_issues.extend(ed.get("labeled_issues", []))
    scoring_issues.extend(ed.get("standard_issues", []))
    scoring_issues.extend(ed.get("advanced_issues", []))
    scoring_issues.extend(ed.get("expert_issues", []))

    scoring_issue_names = {i["issue"] for i in scoring_issues}

    # Check if all scoring issues are present in testdata
    missing = scoring_issue_names - testdata_issue_names
    assert not missing, (
        f"Issues in scoring but not in testdata in {asset_path.name}: {missing}"
    )
