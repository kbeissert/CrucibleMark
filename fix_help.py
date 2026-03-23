with open('Makefile', 'r', encoding='utf-8') as f:
    data = f.read()

import re
old_help_pattern = re.compile(r'  make review-model.*?\s+make review-bias-all.*?\n', re.DOTALL)
new_help = '  make review               📰 Generate Review (Flags: MODEL=name, ALL=1, TYPE=bias)\n'
data = old_help_pattern.sub(new_help, data)

# Also fix the top level targets line where these aliases might still exist.
target_line_pattern = re.compile(r'review-model review-all review-bias-model review-bias-all')
data = target_line_pattern.sub('review', data)


with open('Makefile', 'w', encoding='utf-8') as f:
    f.write(data)
