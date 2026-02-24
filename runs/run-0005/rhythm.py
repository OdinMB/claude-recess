"""
Euclidean Rhythms

Godfried Toussaint (2005): the Euclidean algorithm for computing GCD
is equivalent to distributing n beats across m time slots as evenly
as possible. The resulting patterns are Euclidean rhythms.

The striking discovery: these mathematically-derived patterns match
many traditional rhythms from around the world — without any
musical knowledge being embedded in the algorithm.

E(n, m) = n beats distributed as evenly as possible across m slots

Notation: ●  = beat (hit)
          ○  = rest
          [●○●○] = repeat
"""


def euclidean_rhythm(beats, slots):
    """
    Generate an Euclidean rhythm: n beats in m slots.
    Uses Bjorklund's algorithm (equivalent to Euclidean algorithm).
    Returns a list of 0s and 1s.
    """
    if beats == 0:
        return [0] * slots
    if beats == slots:
        return [1] * slots
    if beats > slots:
        return [1] * slots  # More beats than slots

    # Bjorklund's algorithm
    groups = [[1]] * beats + [[0]] * (slots - beats)

    while True:
        # Find the number of the smaller group
        ones = groups.count([1]) if [1] in groups else 0
        # Check if all groups are the same
        if len(set(tuple(g) for g in groups)) <= 1:
            break

        # Find the larger and smaller counts
        remainder = groups[:]
        # Distribute the last (smaller) group's elements into the beginning of each larger group
        last = groups[-1]
        n_last = groups.count(last)
        n_first = len(groups) - n_last

        if n_last == 0 or n_first == 0:
            break

        new_groups = []
        for i in range(min(n_first, n_last)):
            new_groups.append(groups[i] + groups[n_first + i])

        # Remaining groups
        if n_first > n_last:
            for i in range(n_last, n_first):
                new_groups.append(groups[i])
        elif n_last > n_first:
            for i in range(n_first, n_last):
                new_groups.append(groups[n_first + i])

        if new_groups == groups:
            break
        groups = new_groups

    # Flatten
    result = []
    for g in groups:
        result.extend(g)

    return result[:slots]  # Trim to exact length


def render_circle(pattern, radius=8):
    """Render a rhythm pattern as a clock circle."""
    n = len(pattern)
    width = radius * 4 + 4
    height = radius * 2 + 4
    grid = [[' '] * width for _ in range(height)]

    cx, cy = width // 2, height // 2

    for i, beat in enumerate(pattern):
        angle = 2 * math.pi * i / n - math.pi / 2  # Start at top
        # Point on the circle
        x = cx + int(radius * 2.0 * math.cos(angle) + 0.5)  # 2.0 for aspect ratio
        y = cy + int(radius * math.sin(angle) + 0.5)

        if 0 <= y < height and 0 <= x < width:
            grid[y][x] = '●' if beat else '○'

    # Add connections between consecutive beats
    # (just draw the circle outline lightly)
    steps = n * 4
    for s in range(steps):
        angle = 2 * math.pi * s / steps - math.pi / 2
        x = cx + int(radius * 2.0 * math.cos(angle) + 0.5)
        y = cy + int(radius * math.sin(angle) + 0.5)
        if 0 <= y < height and 0 <= x < width:
            if grid[y][x] == ' ':
                grid[y][x] = '·'

    return [''.join(row) for row in grid]


import math


def linear_render(pattern, repeat=2):
    """Render pattern as a linear sequence, repeated."""
    symbols = ['●' if b else '○' for b in pattern]
    bar = '│' + ''.join(symbols) + '│'
    return bar * repeat


def rotation_classes(beats, slots):
    """
    Two rhythms are the same "necklace" if one is a rotation of the other.
    Enumerate distinct rotations of the Euclidean rhythm.
    """
    base = euclidean_rhythm(beats, slots)
    rotations = []
    for i in range(slots):
        rotated = base[i:] + base[:i]
        rotations.append(rotated)
    return rotations


def onsets(pattern):
    """Return the positions of beats."""
    return [i for i, b in enumerate(pattern) if b]


def inter_onset_intervals(pattern):
    """Return the sequence of gaps between beats."""
    pos = onsets(pattern)
    if not pos:
        return []
    n = len(pattern)
    intervals = []
    for i in range(len(pos)):
        next_i = (i + 1) % len(pos)
        if next_i > i:
            gap = pos[next_i] - pos[i]
        else:
            gap = n - pos[i] + pos[next_i]
        intervals.append(gap)
    return intervals


def evenness_score(pattern):
    """How evenly distributed are the beats? (0=perfectly uneven, 1=perfectly even)"""
    pos = onsets(pattern)
    if len(pos) <= 1:
        return 1.0
    n = len(pattern)
    # Perfect intervals would be n/len(pos) each
    perfect = n / len(pos)
    intervals = inter_onset_intervals(pattern)
    deviation = sum(abs(x - perfect) for x in intervals) / len(intervals)
    max_dev = perfect  # Worst case
    return 1.0 - deviation / max_dev


def show_pattern(name, beats, slots, cultural_note='', rotation=0):
    """Show a single Euclidean rhythm with statistics."""
    pattern = euclidean_rhythm(beats, slots)
    # Apply rotation
    if rotation:
        pattern = pattern[rotation:] + pattern[:rotation]

    intervals = inter_onset_intervals(pattern)
    score = evenness_score(pattern)

    beat_char = '●'
    rest_char = '○'
    seq = ''.join(beat_char if b else rest_char for b in pattern)

    print(f"  E({beats},{slots})" + (f"  rot={rotation}" if rotation else ""))
    if cultural_note:
        print(f"  → {cultural_note}")
    print(f"  Linear: {seq}")
    print(f"  Onset positions: {onsets(pattern)}")
    intervals_str = '+'.join(str(x) for x in intervals)
    print(f"  Inter-onset intervals: [{intervals_str}] = {sum(intervals)}")
    print(f"  Evenness: {score:.3f}  {'(maximally even)' if score > 0.99 else ''}")
    print()


def show_comparison(patterns_data):
    """Show multiple patterns side by side with circle views."""
    for beats, slots, name, rotation in patterns_data:
        pattern = euclidean_rhythm(beats, slots)
        if rotation:
            pattern = pattern[rotation:] + pattern[:rotation]

        seq = ''.join('●' if b else '○' for b in pattern)
        print(f"  {name or f'E({beats},{slots})'}")
        print(f"  {seq}")
        print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║              E U C L I D E A N   R H Y T H M S                     ║")
    print("║  The Euclidean algorithm generates traditional world rhythms        ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("  E(n, m) = n beats distributed as evenly as possible across m slots")
    print("  ● = beat   ○ = rest")
    print()

    print("─" * 72)
    print("  TRADITIONAL RHYTHMS IDENTIFIED AS EUCLIDEAN (Toussaint 2005)")
    print("─" * 72)
    print()

    traditional = [
        (2, 3,  "Tresillo: found in sub-Saharan Africa and Latin American music"),
        (3, 4,  "Cumbia: Colombia"),
        (3, 8,  "Cuban tresillo (with rests): 3+3+2 pattern"),
        (4, 12, "Fandango: Andalucia, Spain"),
        (5, 6,  "York-samai: Persian music"),
        (5, 8,  "Aksak: Turkish, Romanian music"),
        (5, 12, "South African and West African"),
        (5, 16, "Bossa-nova: Brazil"),
        (7, 8,  "Aksak: Bulgarian and Greek music"),
        (7, 12, "West African / Pygmy music"),
        (7, 16, "Samba: Brazil"),
        (9, 16, "West African"),
        (11, 24,"Central African Republic"),
        (13, 24,"Aka Pygmy music"),
    ]

    for beats, slots, note in traditional:
        show_pattern(note.split(':')[0], beats, slots, cultural_note=note)

    print()
    print("─" * 72)
    print("  MATHEMATICAL PROPERTIES")
    print("─" * 72)
    print()

    print("  When gcd(n, m) = 1, the rhythm is maximally even — no two")
    print("  rotations of the pattern are identical (it's a 'prime necklace').")
    print()

    # Show all E(n, 8) for n = 1..8
    print("  All E(n, 8): distributing n beats in 8 slots:")
    print()
    for n in range(1, 9):
        pattern = euclidean_rhythm(n, 8)
        seq = ''.join('●' if b else '○' for b in pattern)
        intervals = inter_onset_intervals(pattern)
        score = evenness_score(pattern)
        ioi = '+'.join(str(x) for x in intervals)
        from math import gcd
        g = gcd(n, 8)
        special = " (maximally even)" if g == 1 else f" (gcd={g})"
        print(f"  E({n},8) = {seq}  [{ioi}]  score={score:.3f}{special}")

    print()

    # Show all E(n, 12)
    print("  All E(n, 12): the 12-beat timeline used in many African rhythms:")
    print()
    for n in [2, 3, 4, 5, 6, 7, 8, 9, 11]:
        pattern = euclidean_rhythm(n, 12)
        seq = ''.join('●' if b else '○' for b in pattern)
        intervals = inter_onset_intervals(pattern)
        ioi = '+'.join(str(x) for x in intervals)
        from math import gcd
        g = gcd(n, 12)
        print(f"  E({n:2d},12) = {seq}  [{ioi}]  gcd={g}")

    print()
    print("─" * 72)
    print("  THE BJORKLUND ALGORITHM = EUCLIDEAN ALGORITHM = BRESENHAM")
    print("─" * 72)
    print()
    print("  The algorithm that generates these rhythms is the same as:")
    print("  - Euclid's algorithm for computing GCD (~300 BCE)")
    print("  - Bresenham's line algorithm for rasterizing straight lines (1962)")
    print("  - The Bjorklund algorithm for distributing timing pulses in physics (1999)")
    print("  - A distributive law for maximally even sequences (Clough & Douthett 1991)")
    print()
    print("  Toussaint noticed the connection to world music in 2005.")
    print("  The same simple algorithm, discovered independently,")
    print("  connecting neutron spallation timing to Yoruba drumming.")
    print()


if __name__ == '__main__':
    main()
