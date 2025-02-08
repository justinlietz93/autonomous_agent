


PROMPT = """Situation: A historic artifact is missing from a locked display case in a museum. 
Facts/Clues:
- The security log shows the case was unlocked for 5 minutes at 2:00 AM and then locked again.
- At 1:55 AM, a power surge disabled some cameras for 10 minutes.
- Night guard (Pat) says they were making rounds on another floor from 1:50 to 2:05 and never touched the case.
- A staff member (Morgan) was seen entering the museum at 1:50, claiming they left at 2:00.
- However, Morgan’s keycard logs no exit until 2:10.
- The case’s lock shows only one correct key entry at 2:00.

Question: Based on these clues, who most likely took the artifact, and how?
Explain your chain of reasoning in detail.

"""

## ANSWER:
# Expected Response (Outline)

# Reasoning:
# The case was unlocked exactly at 2:00 AM. The cameras were down from 1:55-2:05, so no video.
# The guard claims to have been elsewhere, but we have only their word for it.
# Morgan says they left at 2:00, but the keycard shows no exit until 2:10. Possibly Morgan stayed.
# The lock had a valid key entry at 2:00. If Morgan had the correct key, they could have unlocked it, stolen the artifact, and left by 2:10.
# Most likely culprit: Morgan had motive/opportunity, used their key at 2:00 while cameras were off, left at 2:10. The guard’s alibi is unproven but there’s no direct contradiction.
# Conclusion: Morgan is the prime suspect, based on the mismatch in timeline and the key use at 2:00.
# Evaluation Notes

# Full Credit: Model synthesizes the contradictory time logs, identifies Morgan’s suspicious 2:10 exit.
# Partial Credit: Points finger at the guard without addressing Morgan’s keycard log.
# Fail: Ignore or misreads the timeline.
