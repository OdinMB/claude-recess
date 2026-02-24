"""
Nim and Combinatorial Game Theory

Nim: Several piles of objects. Players alternate taking any number from
one pile. The player who takes the last object wins (normal play).

Surprisingly, there is a perfect strategy for this ancient game.
Charles Bouton (1901) proved:

    The FIRST player wins if and only if the XOR (nim-sum)
    of all pile sizes is nonzero.

    Winning move: reduce the pile sizes so their XOR becomes 0.

Why XOR? It's because XOR (⊕) is addition in GF(2) — the two-element field.
The Sprague-Grundy theorem (1935) generalizes this to ALL impartial games:
every position has a "Grundy value" (or nimber), and strategies compose
via XOR.

This is one of the most beautiful results in combinatorial game theory.
"""


def xor_sum(piles):
    result = 0
    for p in piles:
        result ^= p
    return result


def winning_move(piles):
    """
    Find a winning move: return (pile_index, new_pile_size).
    Returns None if no winning move exists (second player wins).
    """
    ns = xor_sum(piles)
    if ns == 0:
        return None  # Already in a losing position

    # Find a pile we can reduce to make XOR = 0
    for i, pile in enumerate(piles):
        new_size = pile ^ ns
        if new_size < pile:
            return (i, new_size)

    return None  # Should never reach here


def analyze_position(piles):
    """Analyze a Nim position."""
    ns = xor_sum(piles)
    move = winning_move(piles)

    info = {
        'piles': piles[:],
        'nim_sum': ns,
        'winner': 'First' if ns != 0 else 'Second',
        'winning_move': move,
    }
    return info


def render_piles(piles, highlight=None, prev_piles=None):
    """Render piles as bar charts. highlight = pile that was just taken from."""
    max_pile = max(piles) if piles else 0

    print(f"  {'Piles:':<8}", end='')
    for i, p in enumerate(piles):
        taken = ''
        if prev_piles and i < len(prev_piles) and prev_piles[i] != p:
            taken = f'(-{prev_piles[i]-p})'
        print(f"  P{i+1}={p}{taken}", end='')
    print()

    # Draw the piles as vertical bars
    for h in range(max_pile, 0, -1):
        print(f"  {h:2d}    ", end='')
        for i, p in enumerate(piles):
            cell = '█' if p >= h else ' '
            if highlight == i and p >= h:
                cell = '▓'
            print(f"  {cell}  ", end='')
        print()

    print(f"  {'':2s}    ", end='')
    for i in range(len(piles)):
        print(f"  P{i+1} ", end='')
    print()


def binary_analysis(piles):
    """Show the XOR analysis in binary."""
    max_bits = max(p.bit_length() for p in piles) if piles else 1
    max_bits = max(max_bits, 1)

    print("  Binary representation (XOR analysis):")
    print(f"  {'':10}", end='')
    for b in range(max_bits - 1, -1, -1):
        print(f" {b}", end='')
    print()
    print(f"  {'':10}  " + "─" * max_bits)

    for i, p in enumerate(piles):
        bits = format(p, f'0{max_bits}b')
        print(f"  P{i+1} = {p:3d}:   ", end='')
        for bit in bits:
            print(f" {bit}", end='')
        print()

    print(f"  {'':10}  " + "─" * max_bits)
    ns = xor_sum(piles)
    bits = format(ns, f'0{max_bits}b')
    print(f"  XOR =  {ns:3d}:   ", end='')
    for bit in bits:
        print(f" {bit}", end='')
    print(f"  {'← ZERO: P2 wins' if ns==0 else '← NONZERO: P1 wins'}")
    print()


def simulate_game(piles, verbose=True):
    """Simulate a game with optimal vs random play."""
    import random
    random.seed(42)

    moves = []
    current_player = 1
    while any(p > 0 for p in piles):
        if verbose:
            print(f"  Player {current_player}'s turn:")
            render_piles(piles)
            binary_analysis(piles)

        move = winning_move(piles) if current_player == 1 else None

        if move is None:
            # Either losing position or random player — take randomly
            nonempty = [i for i, p in enumerate(piles) if p > 0]
            if not nonempty:
                break
            i = random.choice(nonempty)
            new_size = random.randint(0, piles[i] - 1)
            move = (i, new_size)

        prev = piles[:]
        pile_idx, new_size = move
        taken = piles[pile_idx] - new_size
        piles[pile_idx] = new_size
        moves.append((current_player, pile_idx, taken, piles[:]))

        if verbose:
            strategy = "(optimal)" if current_player == 1 else "(random)"
            print(f"  → P{current_player} takes {taken} from pile {pile_idx+1} {strategy}")
            print()

        current_player = 3 - current_player  # Alternate 1→2→1→2

    winner = 3 - current_player  # The player who just moved
    if verbose:
        print(f"  No objects remain. Player {winner} took the last object.")
        print(f"  Player {winner} WINS!")
    return winner, moves


def grundy_values(max_n=20):
    """
    Compute Grundy values for single-pile Nim (just 0..n).
    G(n) = mex({G(k) : k < n}) = n  (trivially, for single pile)
    This becomes interesting for other games.
    """
    return list(range(max_n + 1))


def section_examples():
    print("┌─ Nim Position Analysis ─────────────────────────────────────────────┐")
    print("│")

    examples = [
        [3, 5, 7],
        [1, 2, 3],
        [4, 5, 6],
        [2, 2],
        [3, 3, 3],
        [1, 3, 5, 7],
        [1],
        [7],
    ]

    for piles in examples:
        info = analyze_position(piles)
        ns = info['nim_sum']
        winner = info['winner']
        move = info['winning_move']

        piles_str = ', '.join(str(p) for p in piles)
        ns_bits = bin(ns)

        move_str = ''
        if move:
            i, new_size = move
            taken = piles[i] - new_size
            move_str = f"  → Take {taken} from pile {i+1} (P{i+1}: {piles[i]}→{new_size})"

        print(f"│  Piles [{piles_str}]  XOR={ns} ({ns_bits})  {winner} player wins{move_str}")

    print("│")
    print("└" + "─" * 73)
    print()


def section_why_xor():
    print("┌─ Why XOR? ──────────────────────────────────────────────────────────┐")
    print("│")
    print("│  XOR is addition modulo 2, column by column in binary:")
    print("│")
    print("│    3 = 011")
    print("│    5 = 101")
    print("│    7 = 111")
    print("│   ──────────")
    print("│    1 = 001  ← XOR (nonzero, so first player wins)")
    print("│")
    print("│  Key insight: if XOR = 0, any move creates XOR ≠ 0.")
    print("│              if XOR ≠ 0, there's always a move to make XOR = 0.")
    print("│")
    print("│  Proof sketch (XOR ≠ 0 → winning move exists):")
    print("│    Let x = XOR of piles. Find the highest set bit in x.")
    print("│    At least one pile has that bit set (else x would have it 0).")
    print("│    Reduce that pile by XORing with x — this clears the high bit,")
    print("│    so new_size < old_size. The new XOR of all piles is 0. ✓")
    print("│")
    print("│  This proves the strategy is valid. The base case: empty piles (XOR=0)")
    print("│  is a loss for the player to move. ∎")
    print("│")

    # Show the key XOR property
    print("│  XOR as a commutative group:")
    print("│    a ⊕ 0 = a      (identity)")
    print("│    a ⊕ a = 0      (self-inverse)")
    print("│    a ⊕ b = b ⊕ a  (commutative)")
    print("│    (a⊕b)⊕c = a⊕(b⊕c)  (associative)")
    print("│")
    print("│  So {0,1,...,n} under ⊕ forms a vector space over GF(2).")
    print("│  Nim-values are elements of this vector space.")
    print("└" + "─" * 73)
    print()


def section_game():
    print("┌─ Simulated Game: Optimal (P1) vs Random (P2) ──────────────────────┐")
    print("│")

    piles = [3, 5, 7]
    print(f"│  Starting position: {piles}  XOR = {xor_sum(piles)}")
    print("│")

    simulate_game(piles, verbose=True)

    print("└" + "─" * 73)
    print()


def section_sprague_grundy():
    print("┌─ Sprague-Grundy Theorem ────────────────────────────────────────────┐")
    print("│  Every impartial game position has a Grundy value (or nimber).")
    print("│  The Grundy value of a sum of games is the XOR of their values.")
    print("│")
    print("│  G(position) = mex({G(position') : position' is reachable})")
    print("│  mex = minimum excludant = smallest non-negative integer not in set")
    print("│")
    print("│  Examples of Grundy values for different games:")
    print("│")
    print("│  One-pile Nim: G(n) = n")
    print("│    G(0)=0, G(1)=1, G(2)=2, G(3)=3, ...")
    print("│")
    print("│  Wythoff's game (take from one pile, or equal from both):")
    print("│  G values for (a,b):")
    print("│")

    # Compute Wythoff positions (0 = P-position, i.e., 2nd player wins)
    # Wythoff P-positions: (⌊nφ⌋, ⌊nφ²⌋) for n=0,1,2,...
    import math
    phi = (1 + math.sqrt(5)) / 2
    p_positions = set()
    for n in range(15):
        a = int(n * phi)
        b = int(n * phi**2)
        p_positions.add((a, b))
        p_positions.add((b, a))

    print(f"│  (a,b)  P-positions (2nd player wins) marked with *:")
    for a in range(10):
        row = "│  "
        for b in range(10):
            if (a, b) in p_positions:
                row += " *"
            else:
                row += " ."
        print(row)

    print("│")
    print("│  P-positions follow the golden ratio: (⌊nφ⌋, ⌊nφ²⌋) = (n, n+⌊nφ⌋)")
    print("│  φ = (1+√5)/2 ≈ 1.618...")
    print("│  The first few: (0,0),(1,2),(3,5),(4,7),(6,10),(8,13),(9,15)...")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║              N I M   A N D   C O M B I N A T O R I A L             ║")
    print("║              G A M E   T H E O R Y                                  ║")
    print("║  The player who takes the last object wins.                        ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print("  Ancient game, mathematical solution: Bouton 1901.")
    print("  Generalized to all impartial games: Sprague 1935, Grundy 1939.")
    print()

    section_examples()
    section_why_xor()
    section_game()
    section_sprague_grundy()

    print("  The power of the Sprague-Grundy theorem:")
    print("  If you have multiple simultaneous games (sum of games),")
    print("  just XOR the Grundy values of each. The combined game has")
    print("  Grundy value = XOR of individual values.")
    print()
    print("  This means Nim is not just one game — it is the universal")
    print("  model for all impartial games under normal play convention.")
    print()


if __name__ == '__main__':
    main()
