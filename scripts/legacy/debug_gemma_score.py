import sys
from pathlib import Path

# Add root to python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from benchmark_modules.reasoning_logic.core.evaluators import (
    score_granular_rubric,
)  # noqa: E402

gemma_response = """
Okay, let's schedule these meetings. Here's my reasoning process:

**1. Define the Time Window:**

*   The available time window is from 1:00 PM (13:00) to 3:00 PM (15:00). This gives us a total of 2 hou
rs (120 minutes).
**2. Meeting Durations:**

*   Strategy Review: 1 hour (60 minutes)
*   Team Sync: 1 hour (60 minutes)
*   Client Call: 1 hour (60 minutes)

**3. Total Meeting Time:**

*   Total time required for all meetings: 1 hour + 1 hour + 1 hour = 3 hours (180 minutes).

**4. Constraint Analysis:**

*   We have a 2-hour window (120 minutes) but need 3 hours (180 minutes) of meeting time. This means it'
s impossible to fit all three meetings into the given time frame without overlap or exceeding the deadline.
**5. Re-evaluation of Constraints:**

The problem states that the meetings must all be completed by 3:00 PM and must not overlap. This constra
int is impossible to satisfy with the given information. I will assume that the 3:00 PM deadline is the *latest* possible end time, and the meetings can start *after* 1:00 PM.
**6. Scheduling Attempt:**

Given that we can only fit 2 hours of meetings in the 1:00-3:00 window, let's schedule the meetings star
ting at 1:00 PM.
*   1:00 PM - 2:00 PM: Strategy Review
*   2:00 PM - 3:00 PM: Team Sync

This schedule satisfies the time constraints, but leaves the Client Call unscheduled.

**7. Revised Constraints and Solutions:**

Since the problem is unsolvable as stated, I will provide two possible solutions:

**Solution 1: Prioritize all meetings being scheduled.**
*   1:00 PM - 2:00 PM: Strategy Review
*   2:00 PM - 3:00 PM: Team Sync
*   Client Call is scheduled for a later time.

**Solution 2: Prioritize the 3:00 PM deadline.**
*   1:00 PM - 2:00 PM: Strategy Review
*   2:00 PM - 3:00 PM: Team Sync
*   Client Call is scheduled for a later time.

**Answer:**

Due to the conflicting constraints (2-hour window and 3 hours of meeting time), it's impossible to sched
ule all three meetings within the 1:00 PM to 3:00 PM timeframe without overlap. Here are two possible solutions, prioritizing different aspects:
**Solution 1 (Prioritizing all meetings):**

*   1:00 PM - 2:00 PM: Strategy Review
*   2:00 PM - 3:00 PM: Team Sync
*   Client Call: To be scheduled at a later time.

**Solution 2 (Prioritizing the 3:00 PM deadline):**

*   1:00 PM - 2:00 PM: Strategy Review
*   2:00 PM - 3:00 PM: Team Sync
*   Client Call: To be scheduled at a later time.
"""

score, breakdown, details = score_granular_rubric(gemma_response, "reasoning_5c_001")
print(f"Total Score: {score}")
print("Breakdown:", breakdown)
print("\nDetails:")
for d in details:
    print(d)
