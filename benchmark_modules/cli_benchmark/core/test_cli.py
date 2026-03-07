from typing import Dict, Any

from benchmark_modules.cli_benchmark.core.tasks import CLITaskLoader
from benchmark_modules.cli_benchmark.core.shell_sim import ShellSimulator
from benchmark_modules.cli_benchmark.core.evaluator import CLIEvaluator

# A small standalone local test suite

def test_loader():
    loader = CLITaskLoader()
    tasks = loader.load_tasks()
    assert len(tasks) == 6
    assert tasks[0]["id"] == "cli001"

def test_shell_sim_cli001_success():
    sim = ShellSimulator()
    output = "du -sh /tmp/* | sort -h | tail -5; find /tmp -type f -mtime +7 -delete"
    success, score, msg = sim.simulate("cli001", output)
    assert success is True
    assert score == 100.0
