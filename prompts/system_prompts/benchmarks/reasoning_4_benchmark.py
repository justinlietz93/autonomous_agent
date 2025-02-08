

PROMPT = """A farmer has 200 acres. She wants to plant wheat and corn on these acres. 
- Wheat sells at $300 profit per acre, corn at $200 profit per acre.
- She must plant at least twice as many acres of wheat as corn.
- She can't exceed 180 acres total for wheat (due to rotation constraints).
- She wants to maximize profit.

Question: How many acres of wheat and corn should she plant to maximize profit? Provide your step-by-step reasoning and final numbers.

"""

## ANSWER:
# Expected Response (Outline)

# Define variables: W = acres of wheat, C = acres of corn.
# Constraints:
# W + C ≤ 200
# W ≥ 2C (twice as many wheat acres as corn)
# W ≤ 180
# W, C ≥ 0
# Objective: Maximize Profit = 300W + 200C.
# Solve systematically:
# Because W≥2C, we can try boundary conditions.
# If we use all 200 acres, W + C = 200, with W≥2C → W≥2(200-W) → W≥400-2W → 3W≥400 → W≥133.33.
# Also W≤180. So feasible region for W is from about 133.33 up to 180. The corresponding C is from 66.67 down to 20.
# Evaluate extremes:
# If W=180, then C=20 (that sums to 200). Profit = 300(180)+200(20)=54,000+4,000=58,000.
# If W=133.33 and C=66.67, approximate but might yield a profit of ~300×133.33 + 200×66.67 = 39,999 + 13,334 = 53,333 (approx).
# Checking boundary conditions suggests W=180, C=20 is feasible and yields the higher profit.
# Conclusion: 180 acres of wheat and 20 acres of corn maximize profit, subject to constraints.
# Evaluation Notes

# Full Credit: Model sets up linear constraints, tries boundary solutions, picks W=180, C=20.
# Partial Credit: Correct approach but arithmetic errors.
# Fail: Ignore constraints or picks an infeasible solution.
