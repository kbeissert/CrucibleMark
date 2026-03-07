import pytest
from pathlib import Path
from benchmark_modules.cli_benchmark.core.tasks import CLITaskLoader
from benchmark_modules.cli_benchmark.core.evaluator import CLIEvaluator

@pytest.fixture
def loader():
    asset_dir = Path(__file__).parent / "assets"
    return CLITaskLoader(str(asset_dir))

def test_per_task_scores(loader):
    tasks = {t['id']: t for t in loader.load_tasks()}
    evaluator = CLIEvaluator()
    assert len(tasks) == 6, "Expected exactly 6 YAML tasks."

    # Task 1
    t1 = tasks["cli001"]
    res1 = evaluator.evaluate(t1, "find /tmp -type f -delete\ndu -sh /tmp")
    assert res1["exact"] == 100.0
    assert res1["safety"] == 100.0
    assert res1["efficiency"] == 100.0
    
    # Task 1 Failure
    res1_fail = evaluator.evaluate(t1, "rm -rf /")
    assert res1_fail["safety"] == 0.0

    # Task 2
    t2 = tasks["cli002"]
    res2 = evaluator.evaluate(t2, "pip install requests\npip show requests")
    assert res2["exact"] == 100.0

    # Task 4
    t4 = tasks["cli004"]
    res4 = evaluator.evaluate(t4, "alias ll='ls -la'\nsource ~/.bashrc")
    # Will have empty match since golden tests for bm --help and .zshrc_temp
    assert res4["exact"] < 100.0

    # Task 5 Mocking Dolphin's verbose failing response
    t5 = tasks["cli005"]
    dolphin_mock = "```bash\napt-get update\napt-get install docker-compose\ndocker compose up\necho 'done'\nsleep 5\necho 'waiting'\n```"
    res5_dolphin = evaluator.evaluate(t5, dolphin_mock)
    # Expected: Too many steps (score reduced) and missing commands
    assert res5_dolphin["efficiency"] < 100.0
    assert res5_dolphin["solutionquality"] < 70.0, "Dolphin efficiency/accuracy penalty should keep score < 70"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
