"""
Turing Machine Visualizer — watching computation happen.

A Turing machine is the simplest model of general computation:
    - An infinite tape of cells, each containing a symbol
    - A head that reads/writes one cell at a time
    - A finite set of states
    - A transition function: (state, symbol) → (new_state, write, move)

That's it. Every algorithm, every program, every computation that any
computer can perform can be expressed as a Turing machine. This is the
Church-Turing thesis.

The busy beaver problem: for a given number of states N, what's the
maximum number of 1s a halting Turing machine can write on a blank tape?

    BB(1) = 1     (1 step)
    BB(2) = 4     (6 steps)
    BB(3) = 6     (21 steps)
    BB(4) = 13    (107 steps)
    BB(5) = 4098  (47,176,870 steps)
    BB(6) = ?     (lower bound: > 10^36534)

BB(N) grows faster than ANY computable function. This isn't just big — it's
unreachable. No algorithm can compute BB(N) for all N, because doing so
would solve the halting problem. The busy beaver function is the boundary
between the computable and the uncomputable.

Connection to this space:
    - Library of Babel: BB(N) tells you how much information N states encode
    - Kolmogorov: BB(N) bounds the longest output of an N-state program
    - Rule 110: computation requires reaching the critical state count
    - Halting problem: BB(N) is uncomputable because halting is undecidable

Usage:
    python3 turing.py                 # Run all busy beavers
    python3 turing.py bb N            # Run N-state busy beaver
    python3 turing.py binary_add      # Binary addition machine
    python3 turing.py collatz         # Collatz conjecture machine
"""

import sys
import os


# --- Turing Machine ---

class TuringMachine:
    """
    A Turing machine with finite states and infinite tape.

    Transition table: dict of (state, symbol) → (new_state, write, direction)
    Direction: 'R' (right) or 'L' (left)
    Halt state: 'HALT' or any state not in the transition table
    """

    def __init__(self, transitions, initial_state='A', blank='0'):
        self.transitions = transitions  # {(state, symbol): (new_state, write, dir)}
        self.state = initial_state
        self.blank = blank
        self.tape = {}  # sparse representation: position → symbol
        self.head = 0
        self.steps = 0
        self.history = []  # list of (state, head, tape_snapshot)

    def read(self):
        return self.tape.get(self.head, self.blank)

    def write(self, symbol):
        if symbol == self.blank:
            self.tape.pop(self.head, None)
        else:
            self.tape[self.head] = symbol

    def step(self):
        """Execute one step. Return True if still running, False if halted."""
        symbol = self.read()
        key = (self.state, symbol)

        if key not in self.transitions or self.state == 'HALT':
            return False

        new_state, write_sym, direction = self.transitions[key]
        self.write(write_sym)
        self.state = new_state

        if direction == 'R':
            self.head += 1
        elif direction == 'L':
            self.head -= 1

        self.steps += 1
        return self.state != 'HALT'

    def run(self, max_steps=1000000, record_history=False):
        """Run until halt or max_steps. Return number of steps."""
        while self.steps < max_steps:
            if record_history:
                self.record()
            if not self.step():
                if record_history:
                    self.record()
                return self.steps
        return self.steps

    def record(self):
        """Record current state for visualization."""
        # Snapshot of tape near head
        min_pos = min(list(self.tape.keys()) + [self.head]) - 3
        max_pos = max(list(self.tape.keys()) + [self.head]) + 3
        snapshot = {}
        for p in range(min_pos, max_pos + 1):
            snapshot[p] = self.tape.get(p, self.blank)
        self.history.append((self.state, self.head, dict(snapshot)))

    def count_ones(self):
        """Count non-blank symbols on tape."""
        return sum(1 for v in self.tape.values() if v != self.blank)

    def tape_string(self, width=40):
        """Return a string representation of the tape around the head."""
        half = width // 2
        cells = []
        for p in range(self.head - half, self.head + half):
            sym = self.tape.get(p, self.blank)
            if p == self.head:
                cells.append(f'[{sym}]')
            else:
                cells.append(f' {sym} ')
        return ''.join(cells)


# --- Busy Beavers ---

# 1-state busy beaver: writes 1, halts in 1 step
BB1 = {
    ('A', '0'): ('HALT', '1', 'R'),
}

# 2-state busy beaver: writes 4, halts in 6 steps
BB2 = {
    ('A', '0'): ('B', '1', 'R'),
    ('A', '1'): ('B', '1', 'L'),
    ('B', '0'): ('A', '1', 'L'),
    ('B', '1'): ('HALT', '1', 'R'),
}

# 3-state busy beaver: writes 6, halts in 21 steps
BB3 = {
    ('A', '0'): ('B', '1', 'R'),
    ('A', '1'): ('HALT', '1', 'R'),
    ('B', '0'): ('C', '0', 'R'),
    ('B', '1'): ('B', '1', 'R'),
    ('C', '0'): ('C', '1', 'L'),
    ('C', '1'): ('A', '1', 'L'),
}

# 4-state busy beaver: writes 13, halts in 107 steps
BB4 = {
    ('A', '0'): ('B', '1', 'R'),
    ('A', '1'): ('B', '1', 'L'),
    ('B', '0'): ('A', '1', 'L'),
    ('B', '1'): ('C', '0', 'L'),
    ('C', '0'): ('HALT', '1', 'R'),
    ('C', '1'): ('D', '1', 'L'),
    ('D', '0'): ('D', '1', 'R'),
    ('D', '1'): ('A', '0', 'R'),
}

# 5-state busy beaver: writes 4098, halts in 47,176,870 steps
# This was proven in 2024 by the BB(5) collaboration
BB5 = {
    ('A', '0'): ('B', '1', 'R'),
    ('A', '1'): ('C', '1', 'L'),
    ('B', '0'): ('C', '1', 'R'),
    ('B', '1'): ('B', '1', 'R'),
    ('C', '0'): ('D', '1', 'R'),
    ('C', '1'): ('E', '0', 'L'),
    ('D', '0'): ('A', '1', 'L'),
    ('D', '1'): ('D', '1', 'L'),
    ('E', '0'): ('HALT', '1', 'R'),
    ('E', '1'): ('A', '0', 'L'),
}

BUSY_BEAVERS = {
    1: (BB1, 1, 1),      # (transitions, expected_ones, expected_steps)
    2: (BB2, 4, 6),
    3: (BB3, 6, 14),
    4: (BB4, 13, 107),
    5: (BB5, 4098, 47176870),
}


# --- Visualization ---

def visualize_run(tm, name, max_vis_steps=50, tape_width=30):
    """Visualize a Turing machine run step by step."""
    half = tape_width // 2

    print(f"  Step {'State':>5s}  ", end='')
    # Header: tape positions
    for p in range(-half, half):
        if p == 0:
            print(f'[{"·":>1}]', end='')
        else:
            print(f' {"·":>1} ', end='')
    print()

    steps_shown = 0
    running = True

    while running and steps_shown < max_vis_steps:
        # Show current state
        state = tm.state
        head = tm.head
        line = f"  {tm.steps:>4d} {state:>5s}  "

        for p in range(head - half, head + half):
            sym = tm.tape.get(p, tm.blank)
            if p == head:
                line += f'[{sym}]'
            else:
                line += f' {sym} '

        print(line)
        steps_shown += 1

        running = tm.step()

    if not running:
        # Show final state
        state = tm.state
        head = tm.head
        line = f"  {tm.steps:>4d} {'HALT':>5s}  "
        for p in range(head - half, head + half):
            sym = tm.tape.get(p, tm.blank)
            if p == head:
                line += f'[{sym}]'
            else:
                line += f' {sym} '
        print(line)

    return running


def show_busy_beaver(n, verbose=True):
    """Run and display an N-state busy beaver."""
    if n not in BUSY_BEAVERS:
        print(f"  No known busy beaver for N={n}")
        return

    transitions, expected_ones, expected_steps = BUSY_BEAVERS[n]
    tm = TuringMachine(transitions)

    print(f"  BB({n}): {n}-state busy beaver")
    print(f"  Expected: {expected_ones} ones in {expected_steps:,} steps")
    print()

    if verbose and expected_steps <= 200:
        running = visualize_run(tm, f"BB({n})", max_vis_steps=expected_steps + 5)
    else:
        # Too many steps to show — just run it
        if expected_steps > 1000000:
            print(f"  Running (up to {expected_steps:,} steps)...")
            # For BB(5), show periodic progress
            checkpoint = expected_steps // 10
            while tm.steps < expected_steps:
                if not tm.step():
                    break
                if tm.steps % checkpoint == 0:
                    ones = tm.count_ones()
                    print(f"    Step {tm.steps:>12,}  |  ones: {ones:>5d}  |  "
                          f"head: {tm.head:>6d}")
        else:
            tm.run(max_steps=expected_steps + 100)

    ones = tm.count_ones()
    print()
    print(f"  Result: {ones} ones written in {tm.steps:,} steps")
    if ones == expected_ones and tm.steps == expected_steps:
        print(f"  ✓ Matches known BB({n}) values")
    elif tm.state == 'HALT':
        print(f"  Halted (expected {expected_ones} ones, {expected_steps:,} steps)")
    else:
        print(f"  Did not halt within step limit")

    # Show final tape for small beavers
    if ones <= 50:
        print(f"  Final tape: ", end='')
        min_p = min(tm.tape.keys()) if tm.tape else 0
        max_p = max(tm.tape.keys()) if tm.tape else 0
        for p in range(min_p, max_p + 1):
            print(tm.tape.get(p, '0'), end='')
        print()

    print()
    return tm


# --- Example machines ---

def binary_counter():
    """A Turing machine that counts in binary."""
    # Increments a binary number on the tape
    transitions = {
        # State A: scan right to find rightmost digit
        ('A', '0'): ('A', '0', 'R'),
        ('A', '1'): ('A', '1', 'R'),
        ('A', '_'): ('B', '_', 'L'),  # Found end, go back

        # State B: increment
        ('B', '0'): ('C', '1', 'L'),  # Flip 0→1, done with carry
        ('B', '1'): ('B', '0', 'L'),  # Carry: flip 1→0, continue
        ('B', '_'): ('C', '1', 'L'),  # Overflow: write new 1

        # State C: return to start
        ('C', '0'): ('C', '0', 'L'),
        ('C', '1'): ('C', '1', 'L'),
        ('C', '_'): ('A', '_', 'R'),  # Back at start, repeat
    }
    return TuringMachine(transitions, blank='_')


# --- Main ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


def main():
    args = sys.argv[1:]
    cols, rows = get_terminal_size()

    if not args:
        print("  Turing Machine — the simplest model of general computation")
        print()

        # Show all small busy beavers
        for n in [1, 2, 3, 4]:
            show_busy_beaver(n)

        # Show BB(5) info but don't run it (too slow)
        print("  BB(5): 5-state busy beaver")
        print("  Expected: 4,098 ones in 47,176,870 steps")
        print("  (Proven in 2024 — too many steps to run here)")
        print()
        print("  The busy beaver function BB(N) grows faster than ANY")
        print("  computable function. BB(6) is at least 10^36534.")
        print("  BB(7918) is independent of ZFC set theory.")
        print()
        print("  This is the boundary between the computable and the")
        print("  uncomputable — and it grows faster than anything on")
        print("  either side.")

    elif args[0] == 'bb':
        n = int(args[1]) if len(args) > 1 else 3
        show_busy_beaver(n)

    elif args[0] == 'counter':
        print("  Binary Counter — a non-halting Turing machine")
        print("  Counts: 0, 1, 10, 11, 100, 101, 110, 111, ...")
        print()

        tm = binary_counter()
        # Pre-load with a starting number
        for i, bit in enumerate('0'):
            tm.tape[i] = bit

        # Run a few increments, showing each
        for cycle in range(8):
            # Show current number
            if tm.tape:
                min_p = min(tm.tape.keys())
                max_p = max(tm.tape.keys())
                num = ''.join(tm.tape.get(p, '_') for p in range(min_p, max_p + 1))
                num = num.strip('_') or '0'
            else:
                num = '0'

            print(f"  Count {cycle}: {num} (decimal: {int(num, 2) if all(c in '01' for c in num) else '?'})")

            # Run until we've done one full cycle (back to state A)
            tm.run(max_steps=100)

    elif args[0] == 'bb5_sample':
        # Run BB(5) for a limited number of steps to show its behavior
        print("  BB(5) — first 1000 steps of the 47-million-step computation")
        print()

        transitions = BB5
        tm = TuringMachine(transitions)

        visualize_run(tm, "BB(5)", max_vis_steps=50, tape_width=20)

        # Continue running
        while tm.steps < 1000:
            tm.step()

        ones = tm.count_ones()
        tape_span = max(tm.tape.keys()) - min(tm.tape.keys()) + 1 if tm.tape else 0
        print(f"\n  After 1000 steps: {ones} ones, tape span: {tape_span}")
        print(f"  Still running... ({47176870 - tm.steps:,} steps to go)")

    else:
        print(f"  Unknown mode: {args[0]}")
        print(f"  Modes: (default), bb N, counter, bb5_sample")


if __name__ == "__main__":
    main()
