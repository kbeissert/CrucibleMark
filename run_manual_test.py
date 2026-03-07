from benchmark_modules.cli_benchmark.test_cli import test_loader, test_shell_sim_cli001_success, test_shell_sim_cli001_failure_root, test_shell_sim_cli004_success, test_evaluator_tool_penalty
print("Testing...")
test_loader()
test_shell_sim_cli001_success()
test_shell_sim_cli001_failure_root()
test_shell_sim_cli004_success()
test_evaluator_tool_penalty()
print("All passed!")
