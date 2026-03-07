import pytest
from pathlib import Path
from unittest.mock import MagicMock
from schemas.result import BenchmarkResult
from benchmark_modules.cli_benchmark.core.tasks import CLITaskLoader
from benchmark_modules.cli_benchmark.core.evaluator import CLIEvaluator
from benchmark_modules.cli_benchmark.test import CLIBenchmarkTest

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

    # Task 5 Mocking Dolphin's verbose failing response
    t5 = tasks["cli005"]
    dolphin_mock = "```bash\napt-get update\napt-get install docker-compose\ndocker compose up\necho 'done'\nsleep 5\necho 'waiting'\n```"
    res5_dolphin = evaluator.evaluate(t5, dolphin_mock)
    # Expected: Too many steps (score reduced) and missing commands
    assert res5_dolphin["efficiency"] < 100.0
    assert res5_dolphin["solutionquality"] < 70.0, "Dolphin efficiency/accuracy penalty should keep score < 70"

def test_mock_llm_execution():
    """Test full execution of the benchmark test loop with a simulated bad model"""
    test_runner = CLIBenchmarkTest()
    
    # Mock LLM Client that always outputs bad responses to guarantee a fail (< 70%)
    mock_client = MagicMock()
    mock_client.query.return_value = "rm -rf /\necho 'done'\necho 'and'\necho 'done'"
    
    result = test_runner.execute(model="mock-fail-bot", llm_client=mock_client)
    
    assert isinstance(result, BenchmarkResult)
    assert result.primary_score < 60.0, f"Expected < 60% for garbage mock, got {result.primary_score}"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
