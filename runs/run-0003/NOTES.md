# Langton's Ant Explorations

## What this is

A systematic exploration of generalized Langton's Ant — cellular automata where
one or more "ants" walk on an infinite grid, turning and flipping cell colors
according to simple rules. Despite trivial local rules, these systems produce
remarkably complex emergent behavior.

## Files

- `langton.py` — First-pass simulation with 6 experiments
- `langton_v2.py` — Improved version with better rendering and 10 experiments
- `animate.py` — Animated GIFs showing evolution over time
- `survey.py` — Systematic classification of all 2-5 character RL rule strings
- `investigate_rlr.py` — Deep investigation of the RLR rule (2M steps)
- `hero.py` — High-quality renders of the most visually striking results

## Key findings

### Three behavior classes

Surveying 52 rule strings (all non-trivial combinations of R and L, length 2-5):

| Behavior | Count | Description |
|----------|-------|-------------|
| Highway  | 16    | Ant escapes to infinity along a periodic diagonal path |
| Bounded  | 32    | Ant stays confined to a small region indefinitely |
| Unclear  | 4     | Ambiguous — growing slowly, status undetermined |

### The RLR mystery

RLR is one of the most studied ambiguous rules. After 2,000,000 steps:
- Bounding box: 277 (growing as ~sqrt(steps))
- Growth pattern: **diffusive**, not linear
- No phase transition visible
- The blob is dense and roughly circular — no emerging structure

This sqrt(n) growth is consistent with a random walk, which is neither the
linear growth of highways nor the plateau of bounded rules. It might be a
genuinely distinct third behavioral class, or it might just need 10^18 more
steps to transition.

### Rule symmetry

- **R/L mirror**: Swapping all R↔L in a rule produces identical behavior
  (geometric reflection). So RL≡LR, RLL≡LRR, etc.
- **Unbalanced rules tend toward highways**: Rules with more R's than L's
  (or vice versa) create net rotational bias → directional escape.
- **Balanced rules tend to be bounded**: Equal R's and L's → no net rotation
  → the ant stays trapped.

### Visual highlights

- **Classic RL highway**: ~10,000 steps of chaos, then sudden spontaneous
  highway construction. The phase transition is genuinely surprising.
- **RRLLLRLLLRRR (12-state)**: Produces dramatic geometric triangles with
  perfectly straight edges. A single ant drawing precise geometry.
- **RLLR (4-state)**: Bounded fractal with nested rectangular borders.
  Beautiful in neon palette.
- **Four-ant collision**: Four classic ants starting from corners produce
  a pinwheel pattern with four highways.
- **Counter-rotating pair**: Two ants facing opposite directions briefly
  interact (tiny knot), then escape as opposing highways.

## The open question

There's a conjecture that ALL Langton's ant rules eventually produce highways
(given enough steps). Our survey suggests this is likely false for "bounded"
rules — they show no growth at all even after hundreds of thousands of steps.
But for the "unclear" cases like RLR, the question remains genuinely open.
