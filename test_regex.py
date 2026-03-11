import re

_RE_SCORE = re.compile(
    r"(?:#{1,4}\s*)?(?:\*{1,2})?\s*SCORE\s*(?:\*{1,2})?[\s:\-]+\s*(?:\*{1,2})?\s*[\[\(\"']?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)[\]\)\"']?(?:\*{1,2})?",
    re.IGNORECASE | re.MULTILINE,
)
test_scores = [
    "SCORE: 3",
    "### **SCORE: 3**",
    "### SCORE: 3",
    "**SCORE: 3**",
    "SCORE: [3]",
    "SCORE: three",
    "SCORE - 4",
    "**SCORE**: **4**"
]
for s in test_scores:
    m = _RE_SCORE.search(s)
    print(f"{s!r} -> {m.group(1) if m else None}")
