
import sys
from pathlib import Path
sys.path.append('.')

from scripts.run_commercial_benchmark import CommercialBenchmarkRunner

def run_test():
    print("🚀 Running Benchmark for Mistral Large (Asset 003 & 005 check)...")
    
    runner = CommercialBenchmarkRunner(mode='test')
    
    benchmark_info = {
        'name': 'Code Quality Audit',
        'path': 'test_modules/code_quality/assets',
        'test_class': 'CodeQualityTest'
    }
    
    # Run for Mistral Large
    results = runner.run_benchmark('mistral', 'mistral-large-latest', benchmark_info)
    
    if results:
        runner.save_results(results)
        runner.print_summary(results)

if __name__ == "__main__":
    run_test()
