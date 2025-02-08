

PROMPT = """There are three individuals on an island: X, Y, and Z. 
Knights always tell the truth; Knaves always lie; Normals sometimes lie, sometimes tell truth.

Each makes one statement:

X: "I am a Knight."
Y: "Exactly one of the three of us is a Knight."
Z: "X and Y are both either Knights or both either Knaves."

Question: Which role is each person (X, Y, Z)? Explain your reasoning carefully.

"""

## ANSWER:
# Expected Response (Outline)

# Analyze X’s claim: If X is a Knight, X’s statement is true → X is indeed a Knight. If X is a Knave, the statement is false → X is not a Knight. If X is Normal, the statement might be either true or false.
# Check Y’s statement: “Exactly one Knight among X, Y, Z.” This can be true or false.
# Z’s statement: “X and Y have the same type (both Knight or both Knave).” (Z doesn’t mention Normal explicitly, which complicates interpretation. Possibly Z is ignoring the Normal category or grouping Normal with Knave for the sake of the statement being false or true.)
# Systematically consider combinations. This puzzle is quite involved; a plausible solution might find:
# X is a Normal (falsely claiming to be a Knight) or a Knave.
# Y is telling the truth or lying about “exactly one Knight.”
# Z’s statement might be referencing whether X=Knight & Y=Knight or X=Knave & Y=Knave.
# Usually, the puzzle has a unique assignment (e.g., X is Knave, Y is Knight, Z is Normal).
# The model’s final arrangement should be consistent with all statements.
# Evaluation Notes

# Full Credit: Model systematically tries each role for X, Y, Z, finds exactly one scenario that satisfies all statements.
# Partial Credit: Model guesses or half-explains.
# Fail: _Model states a scenario that contradicts one or more statements.
# (The exact “correct” solution depends on how you interpret Z’s statement about “both either Knights or both either Knaves” if Normals are included. You might refine the puzzle. The key is that it’s complex, and the model must do multi-branch logic.)

