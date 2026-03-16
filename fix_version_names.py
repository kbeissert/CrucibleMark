import os
import glob
import json
import csv

def update_files():
    # we want to target benchmark_scores/*.csv and outputs/runs/**/*.json or outputs/**/*.csv
    files_to_check = glob.glob('benchmark_scores/**/*.csv', recursive=True)
    files_to_check += glob.glob('outputs/**/*.csv', recursive=True)
    files_to_check += glob.glob('outputs/**/*.json', recursive=True)

    replacements = {
        'claude-sonnet-4-6': 'claude-3-7-sonnet-20250219',
        'claude-opus-4-6': 'claude-3-5-opus-latest',  # Or whatever they should be? Wait. The user says "diese neue Versionskennung zu aktualisieren, sodass sie wieder zusammengeführt werden können".
        # What was the new versioning?
    }
    
    print("Files to check:", len(files_to_check))

update_files()
