import re
pat = re.compile(
    r"(?:##\s*)?"
    r"\*?\*?SCORE\*?\*?"
    r"\s*[:\-]?\s*"
    r"(?:\*?\*?)?"
    r"[\[\(\"']?"
    r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"[\]\)\"']?",
    re.IGNORECASE | re.MULTILINE
)
for s in ["SCORE: 3", "**SCORE:** 3", "**SCORE:** **4**", "## SCORE
3", "SCORE:
3", "SCORE - [4]", "SCORE: **4**", "## SCORE 
**4**"]:
    m = pat.search(s)
    print(f"{repr(s):25s} -> {m.group(1) if m else None}")

