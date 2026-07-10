import glob

def update_files():
    # we want to target benchmark_scores/*.csv and outputs/runs/**/*.json or outputs/**/*.csv
    files_to_check = glob.glob('benchmark_scores/**/*.csv', recursive=True)
    files_to_check += glob.glob('outputs/**/*.csv', recursive=True)
    files_to_check += glob.glob('outputs/**/*.json', recursive=True)

    print("Files to check:", len(files_to_check))

update_files()
