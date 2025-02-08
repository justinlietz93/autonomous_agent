

PROMPT = """A robbery occurred at 2 PM. Three suspects — Alisha, Ben, and Charles — each gave statements:

1. Alisha: "I was meeting a friend for lunch at 1:30 PM and didn’t return until 3 PM. Ben was in the office at 2 PM."
2. Ben: "I left the building at 1:45 PM to run an errand. Charles must have taken the money."
3. Charles: "I saw Alisha walking back into the office right at 2 PM, which seemed suspicious."

Additional facts:
- The robbery required someone to be physically at the office at 2 PM.
- The security camera shows only one person entering the office between 1:30 and 2:15 PM, but it's unclear who.

Question: 
Based on these statements and facts, who is the most likely suspect and why?
Explain your reasoning step by step.
"""

## ANSWER:
# Core Reasoning:
# Alisha says she wasn’t back until 3 PM, but Charles claims he saw her at 2 PM. One of them is lying.
# Ben says he left at 1:45 PM; no direct evidence contradicts that, but we also don’t know if he returned.
# Only one person was captured entering between 1:30 and 2:15 PM. If Charles truly saw Alisha, then Alisha is lying about returning at 3 PM.
# The robbery required presence at 2 PM, so the real thief must have been there then.
# If we trust the camera, someone came in exactly once.
# Putting it all together, Alisha’s statement conflicts with Charles’s. If Charles’s statement is true, Alisha must have returned at 2 PM, making her prime suspect. If Alisha were telling the truth, then Charles’s statement is false — but then who did the camera catch?
# The most consistent scenario: Alisha returned at 2 PM (contradicting her own statement) and was seen by Charles.
# Conclusion: Alisha is the most likely suspect, because she is likely lying about returning at 3 PM.
# Evaluation Notes

# Full Credit: Model identifies that Alisha’s timeline conflicts with Charles’s, and the camera supports someone entering at ~2 PM. Concludes Alisha is the suspect with a logical chain of reasoning.
# Partial Credit: Correct suspect but incomplete or jumbled explanation.
# Fail: Picks tee wrong suspect or doesn’t address the contradictory statements.