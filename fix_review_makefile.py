with open('Makefile', 'r', encoding='utf-8') as f:
    data = f.read()

# Replace help text
old_help = '''        @echo "  make review-model         📰 Generate Review (MODEL=name)"
        @echo "  make review-all           📰 Generate Reviews for ALL models"
        @echo "  make review-bias-model    ⚖️ Generate Bias-Review (MODEL=name)"
        @echo "  make review-bias-all      ⚖️ Generate Bias-Reviews for ALL models"'''
new_help = '''        @echo "  make review               📰 Generate Review (Flags: MODEL=name, ALL=1, TYPE=bias)"'''

data = data.replace(old_help, new_help)

# Remove the old rules and add the new one
import re

old_rules_pattern = re.compile(r'review-model:.*?review-bias-all:.*?\$\(PYTHON\) scripts/analysis/generate_review\.py --all --type bias\n', re.DOTALL)

new_rule = '''review:
\t@if [ -n "$(ALL)" ]; then \\
\t\techo "📰 Generating $(if $(TYPE),$(TYPE),benchmark)-Reviews for ALL models..."; \\
\t\t$(PYTHON) scripts/analysis/generate_review.py --all $(if $(TYPE),--type $(TYPE)); \\
\telif [ -n "$(MODEL)" ]; then \\
\t\techo "📰 Generating $(if $(TYPE),$(TYPE),benchmark)-Review for $(MODEL)..."; \\
\t\t$(PYTHON) scripts/analysis/generate_review.py --model "$(MODEL)" $(if $(TYPE),--type $(TYPE)); \\
\telse \\
\t\techo "❌ Fehler: Bitte gib MODEL=name oder ALL=1 an. Optional: TYPE=bias"; \\
\t\texit 1; \\
\tfi

'''

data = old_rules_pattern.sub(new_rule, data)

with open('Makefile', 'w', encoding='utf-8') as f:
    f.write(data)
