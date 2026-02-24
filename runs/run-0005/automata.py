"""
Wolfram's Elementary Cellular Automata

A 1D row of cells, each black (1) or white (0).
Each generation: a cell's next state depends only on
  its current state and its two neighbors — 3 bits total.

With 3 bits there are 8 patterns. Each can map to 0 or 1.
That's 2^8 = 256 possible rules.

Wolfram numbered them by reading the output bits as binary:
  pattern: 111 110 101 100 011 010 001 000
  Rule 30:   0   0   0   1   1   1   1   0  → binary 00011110 = 30

What Wolfram found (and built a career on):
  - Some rules are static (dead)
  - Some oscillate (boring)
  - Some are fractal (beautiful)
  - Some are chaotic (Rule 30 — used as a random number generator)
  - Some are Turing complete (Rule 110)

A whole "computational universe" in 8 bits.
"""


def apply_rule(cells, rule_num):
    """Apply a Wolfram rule to a row of cells."""
    n = len(cells)
    new_cells = [0] * n
    rule_bits = [(rule_num >> i) & 1 for i in range(8)]

    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        pattern = (left << 2) | (center << 1) | right
        new_cells[i] = rule_bits[pattern]

    return new_cells


def evolve(rule_num, width=72, generations=36, seed='single'):
    """Run a cellular automaton for N generations."""
    cells = [0] * width

    if seed == 'single':
        cells[width // 2] = 1
    elif seed == 'random':
        import random
        random.seed(rule_num)  # Deterministic per rule
        cells = [random.randint(0, 1) for _ in range(width)]

    history = [cells[:]]
    for _ in range(generations - 1):
        cells = apply_rule(cells, rule_num)
        history.append(cells[:])

    return history


def render(history, on='█', off='·'):
    return [''.join(on if c else off for c in row) for row in history]


FEATURED_RULES = [
    (0,   "Null",         "All cells die immediately", 'single'),
    (30,  "Rule 30",      "Chaotic — Wolfram's randomness source", 'single'),
    (54,  "Rule 54",      "Complex patterns with propagating signals", 'single'),
    (60,  "Rule 60",      "XOR rule — produces Sierpinski triangle", 'single'),
    (90,  "Rule 90",      "Sierpinski triangle (additive, XOR)", 'single'),
    (105, "Rule 105",     "Complementary to Rule 150", 'single'),
    (110, "Rule 110",     "Turing complete — capable of universal computation", 'single'),
    (150, "Rule 150",     "Additive XOR rule with center bit", 'single'),
    (184, "Rule 184",     "Traffic flow model: particles moving right", 'random'),
    (255, "Rule 255",     "Everything lives — all cells instantly alive", 'single'),
]


def print_rule_diagram(rule_num):
    """Print the 8-case lookup table for this rule."""
    rule_bits = [(rule_num >> i) & 1 for i in range(8)]
    patterns = ['111', '110', '101', '100', '011', '010', '001', '000']
    line1 = '  '.join(p for p in patterns)
    line2 = '  '.join('█' if rule_bits[7-i] else '·' for i in range(8))
    return line1, line2


def all_rules_comparison(width=60, generations=20):
    """Show all 256 rules in a compact grid."""
    print("┌─ All 256 rules from a single-cell seed (20 gen, 60 wide) ──────────┐")
    print("│  Each block is one rule. Row by row, rule 0–255.")
    print("│")

    cols_per_row = 4
    rule = 0
    while rule < 256:
        # Render cols_per_row rules side by side
        rule_histories = []
        rule_nums = []
        for i in range(cols_per_row):
            if rule + i < 256:
                h = evolve(rule + i, width=width//cols_per_row - 2, generations=generations)
                rule_histories.append(render(h, on='█', off=' '))
                rule_nums.append(rule + i)

        # Header row
        header = '│ '
        for rn in rule_nums:
            w = width // cols_per_row - 2
            label = f"Rule {rn}"
            header += label + ' ' * max(0, w - len(label)) + '  '
        print(header[:80])

        # Data rows
        for gen in range(generations):
            line = '│ '
            for i, h in enumerate(rule_histories):
                line += h[gen] + '  '
            print(line[:80])

        print("│")
        rule += cols_per_row

    print("└" + "─" * 72)


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          E L E M E N T A R Y   C E L L U L A R   A U T O M A T A   ║")
    print("║  8 bits of rule → entire computational universes                   ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print("  Rule lookup table format:")
    print("  Pattern (left,center,right) → next state of center cell")
    print()

    for rule_num, name, desc, seed in FEATURED_RULES:
        print(f"┌─ {name}: {desc}")
        l1, l2 = print_rule_diagram(rule_num)
        print(f"│  Patterns: {l1}")
        print(f"│  Outputs:  {l2}")
        print(f"│  Seed: {seed} cell{'  (72 wide, 36 generations)' if seed=='single' else ' (random, 72 wide, 36 gen)'}")
        print("│")

        history = evolve(rule_num, width=72, generations=36, seed=seed)
        lines = render(history, on='█', off=' ')
        for line in lines:
            print("│ " + line)

        print("└" + "─" * 74)
        print()

    # Show the rule table
    print("┌─ Rule classification (Wolfram's four classes) ─────────────────────┐")
    print("│")
    print("│  Class 1: Fixed point — all cells die or become uniform")
    print("│           Examples: 0, 8, 32, 40, 128, 136, 160, 168, 255")
    print("│")
    print("│  Class 2: Periodic — stable or oscillating patterns")
    print("│           Examples: 4, 12, 36, 44, 72, 76, 104, 108, 200, 204")
    print("│")
    print("│  Class 3: Chaotic — unpredictable, looks random")
    print("│           Examples: 18, 22, 30, 45, 54, 60, 90, 105, 122, 126")
    print("│")
    print("│  Class 4: Complex — localized structures, potential computation")
    print("│           Examples: 54, 106, 110 (only proven Turing-complete)")
    print("│")
    print("│  Only Rule 110 has been proven Turing complete (Matthew Cook, 1994)")
    print("│  published only in 2004 after legal disputes with Wolfram Research.")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()


if __name__ == '__main__':
    main()
