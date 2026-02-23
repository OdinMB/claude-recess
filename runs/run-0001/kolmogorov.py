"""
Kolmogorov Complexity Explorer — searching for short programs.

Kolmogorov complexity K(x) is the length of the shortest program that
produces x. It's uncomputable (reduction from the halting problem), but
we can approximate it from above: find short programs that work, and
the shortest one found is an upper bound on K(x).

This uses Brainfuck as the programming language because:
    1. It's Turing-complete (so K_BF is at most a constant factor from K)
    2. Programs are strings over an 8-character alphabet
    3. They're easy to enumerate (just count in base 8)
    4. The interpreter is tiny

The search: enumerate all BF programs by length, execute each with a
step limit, and check if the output matches the target. The shortest
match is our upper bound on K(x).

There's also a guided search mode that uses genetic programming to
evolve programs toward a target — mutation and selection over BF strings.

Usage:
    python3 kolmogorov.py "hello"          # Find shortest BF for "hello"
    python3 kolmogorov.py enum "AB"         # Enumerate short programs
    python3 kolmogorov.py evolve "hello"    # Genetic search
    python3 kolmogorov.py run "++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>."
    python3 kolmogorov.py stats             # Random programs statistics
"""

import sys
import random
import time


# --- Brainfuck Interpreter ---

BF_CHARS = "><+-.,[]"


def bf_run(program, input_bytes=b"", max_steps=10000, max_output=1000):
    """Execute a Brainfuck program.

    Returns (output_bytes, steps_used, halted).
    halted is True if the program terminated normally,
    False if it hit the step limit.
    """
    # Precompute bracket matching
    brackets = {}
    stack = []
    for i, ch in enumerate(program):
        if ch == '[':
            stack.append(i)
        elif ch == ']':
            if not stack:
                return b"", 0, False  # Unmatched bracket
            j = stack.pop()
            brackets[j] = i
            brackets[i] = j
    if stack:
        return b"", 0, False  # Unmatched bracket

    tape = [0] * 30000
    ptr = 0
    pc = 0
    input_pos = 0
    output = bytearray()
    steps = 0

    while pc < len(program) and steps < max_steps:
        ch = program[pc]
        if ch == '>':
            ptr = (ptr + 1) % 30000
        elif ch == '<':
            ptr = (ptr - 1) % 30000
        elif ch == '+':
            tape[ptr] = (tape[ptr] + 1) % 256
        elif ch == '-':
            tape[ptr] = (tape[ptr] - 1) % 256
        elif ch == '.':
            output.append(tape[ptr])
            if len(output) >= max_output:
                pc += 1
                break
        elif ch == ',':
            if input_pos < len(input_bytes):
                tape[ptr] = input_bytes[input_pos]
                input_pos += 1
            else:
                tape[ptr] = 0
        elif ch == '[':
            if tape[ptr] == 0:
                pc = brackets[pc]
        elif ch == ']':
            if tape[ptr] != 0:
                pc = brackets[pc]
        pc += 1
        steps += 1

    halted = pc >= len(program)
    return bytes(output), steps, halted


def bf_clean(program):
    """Remove non-BF characters from a string."""
    return ''.join(c for c in program if c in BF_CHARS)


# --- Enumeration Search ---

def enumerate_programs(max_length, bf_chars=BF_CHARS):
    """Generate all BF programs up to max_length, shortest first."""
    for length in range(1, max_length + 1):
        yield from _generate(length, bf_chars)


def _generate(length, chars):
    """Generate all strings of given length over chars."""
    if length == 0:
        yield ""
        return
    for prefix in _generate(length - 1, chars):
        for c in chars:
            yield prefix + c


def search_enum(target, max_program_len=20, max_steps=5000):
    """Search for shortest BF program producing target string."""
    target_bytes = target.encode('ascii') if isinstance(target, str) else target

    print(f"  Searching for shortest BF program producing: {repr(target)}")
    print(f"  Target length: {len(target_bytes)} bytes")
    print(f"  Max program length: {max_program_len}")
    print(f"  Enumerating programs...", flush=True)

    best = None
    best_len = float('inf')
    checked = 0
    start_time = time.time()

    for length in range(1, max_program_len + 1):
        # Only programs that contain '.' can produce output
        # Only programs with balanced brackets can run
        # But enumerating all of length L and filtering is simpler

        count_at_length = 0
        for prog in _generate(length, BF_CHARS):
            # Quick filter: must contain at least as many '.' as target bytes
            if prog.count('.') < len(target_bytes):
                continue
            # Must have balanced brackets
            depth = 0
            valid = True
            for c in prog:
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth < 0:
                        valid = False
                        break
            if not valid or depth != 0:
                continue

            output, steps, halted = bf_run(prog, max_steps=max_steps)
            checked += 1
            count_at_length += 1

            if output == target_bytes:
                if len(prog) < best_len:
                    best = prog
                    best_len = len(prog)
                    elapsed = time.time() - start_time
                    print(f"  FOUND (len={len(prog)}, checked={checked}, "
                          f"time={elapsed:.1f}s): {prog}")

            # Progress report
            if checked % 50000 == 0:
                elapsed = time.time() - start_time
                print(f"    checked {checked} programs "
                      f"(length {length}, {elapsed:.1f}s)...", flush=True)

        # If we found something at this length, we're done
        # (shorter programs were already checked)
        if best is not None and best_len <= length:
            break

        # Time limit
        if time.time() - start_time > 60:
            print(f"  Time limit reached after {checked} programs")
            break

    if best:
        print(f"\n  Best found: {best}")
        print(f"  Length: {len(best)} characters")
        print(f"  K_BF(\"{target}\") <= {len(best)}")
        output, steps, _ = bf_run(best)
        print(f"  Output: {repr(output.decode('ascii', errors='replace'))}")
        print(f"  Steps: {steps}")
    else:
        print(f"\n  No program found within length {max_program_len}")

    return best


# --- Genetic Search ---

def random_program(length):
    return ''.join(random.choice(BF_CHARS) for _ in range(length))


def mutate(program, rate=0.1):
    """Mutate a BF program."""
    result = list(program)
    for i in range(len(result)):
        if random.random() < rate:
            result[i] = random.choice(BF_CHARS)
    # Random insertion
    if random.random() < 0.1:
        pos = random.randint(0, len(result))
        result.insert(pos, random.choice(BF_CHARS))
    # Random deletion
    if random.random() < 0.1 and len(result) > 1:
        pos = random.randint(0, len(result) - 1)
        result.pop(pos)
    return ''.join(result)


def crossover(a, b):
    """Single-point crossover of two programs."""
    if len(a) < 2 or len(b) < 2:
        return a, b
    cut_a = random.randint(1, len(a) - 1)
    cut_b = random.randint(1, len(b) - 1)
    child1 = a[:cut_a] + b[cut_b:]
    child2 = b[:cut_b] + a[cut_a:]
    return child1, child2


def fitness(program, target_bytes, max_steps=5000):
    """Fitness of a BF program for producing target string.

    Higher is better. Based on:
    - Number of correct output bytes
    - Closeness of each byte to the target
    - Penalty for program length (prefer shorter programs)
    """
    output, steps, halted = bf_run(program, max_steps=max_steps)

    if not output:
        return -1000 - len(program)

    score = 0
    # Reward matching bytes
    for i in range(min(len(output), len(target_bytes))):
        if output[i] == target_bytes[i]:
            score += 100  # Exact match is very valuable
        else:
            # Partial credit for closeness
            diff = abs(output[i] - target_bytes[i])
            score += max(0, 50 - diff)

    # Penalty for wrong length
    len_diff = abs(len(output) - len(target_bytes))
    score -= len_diff * 30

    # Small penalty for program length (prefer shorter)
    score -= len(program) * 0.5

    # Bonus for exact match
    if output == target_bytes:
        score += 10000

    return score


def search_evolve(target, pop_size=200, generations=500, max_prog_len=100):
    """Evolve BF programs using genetic algorithm."""
    target_bytes = target.encode('ascii') if isinstance(target, str) else target

    print(f"  Evolving BF programs for: {repr(target)}")
    print(f"  Population: {pop_size}  |  Generations: {generations}")

    # Initialize population with random programs of varying lengths
    population = []
    for _ in range(pop_size):
        length = random.randint(5, max_prog_len)
        population.append(random_program(length))

    best_ever = None
    best_ever_score = float('-inf')
    start_time = time.time()

    for gen in range(generations):
        # Evaluate fitness
        scored = [(fitness(prog, target_bytes), prog) for prog in population]
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_prog = scored[0]
        if best_score > best_ever_score:
            best_ever_score = best_score
            best_ever = best_prog

        # Check for success
        output, _, _ = bf_run(best_prog)
        if output == target_bytes:
            elapsed = time.time() - start_time
            print(f"\n  SUCCESS at generation {gen}! ({elapsed:.1f}s)")
            print(f"  Program: {best_prog}")
            print(f"  Length: {len(best_prog)}")
            print(f"  K_BF(\"{target}\") <= {len(best_prog)}")
            return best_prog

        # Report
        if gen % 50 == 0:
            output_preview = output[:20]
            elapsed = time.time() - start_time
            print(f"  gen {gen:4d}  |  best fitness: {best_score:8.1f}  |  "
                  f"output: {repr(output_preview)}  |  "
                  f"prog_len: {len(best_prog)}  |  {elapsed:.1f}s",
                  flush=True)

        # Selection: tournament
        next_gen = [scored[0][1], scored[1][1]]  # Elitism: keep top 2

        while len(next_gen) < pop_size:
            # Tournament selection
            candidates = random.sample(scored, min(5, len(scored)))
            parent1 = max(candidates, key=lambda x: x[0])[1]
            candidates = random.sample(scored, min(5, len(scored)))
            parent2 = max(candidates, key=lambda x: x[0])[1]

            # Crossover
            if random.random() < 0.7:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1, parent2

            # Mutate
            child1 = mutate(child1, rate=0.08)
            child2 = mutate(child2, rate=0.08)

            # Length limit
            child1 = child1[:max_prog_len]
            child2 = child2[:max_prog_len]

            next_gen.extend([child1, child2])

        population = next_gen[:pop_size]

        # Time limit
        if time.time() - start_time > 120:
            print(f"\n  Time limit reached at generation {gen}")
            break

    # Report best found
    output, _, _ = bf_run(best_ever)
    print(f"\n  Best found (not exact match):")
    print(f"  Program: {best_ever[:80]}{'...' if len(best_ever) > 80 else ''}")
    print(f"  Length: {len(best_ever)}")
    print(f"  Output: {repr(output[:50])}")
    print(f"  Target: {repr(target_bytes[:50])}")
    return best_ever


# --- Program Statistics ---

def program_stats(n_samples=10000, max_length=20, max_steps=1000):
    """Analyze random BF programs: what fraction halt? produce output?"""
    print(f"  Analyzing {n_samples} random BF programs (length 1-{max_length})")

    halted = 0
    produced_output = 0
    outputs = {}
    total_output_len = 0

    for _ in range(n_samples):
        length = random.randint(1, max_length)
        prog = random_program(length)
        output, steps, did_halt = bf_run(prog, max_steps=max_steps)

        if did_halt:
            halted += 1
        if output:
            produced_output += 1
            total_output_len += len(output)
            key = output[:10]  # Truncate for counting
            outputs[key] = outputs.get(key, 0) + 1

    print(f"\n  Results:")
    print(f"    Halted:          {halted}/{n_samples} ({100*halted/n_samples:.1f}%)")
    print(f"    Produced output: {produced_output}/{n_samples} "
          f"({100*produced_output/n_samples:.1f}%)")
    if produced_output:
        print(f"    Avg output len:  {total_output_len/produced_output:.1f} bytes")
    print(f"    Unique outputs:  {len(outputs)}")

    # Most common outputs
    if outputs:
        print(f"\n  Most common outputs:")
        top = sorted(outputs.items(), key=lambda x: x[1], reverse=True)[:10]
        for output_bytes, count in top:
            try:
                display = repr(output_bytes.decode('ascii', errors='replace'))
            except:
                display = repr(output_bytes)
            print(f"    {count:5d}x  {display}")

    # Output length distribution
    print(f"\n  This is a window into the structure of program space.")
    print(f"  Most random programs do nothing useful, just like most")
    print(f"  books in the Library of Babel are gibberish.")


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == 'run' and len(sys.argv) > 2:
        program = bf_clean(sys.argv[2])
        output, steps, halted = bf_run(program, max_steps=1000000)
        print(f"  Program: {program[:60]}{'...' if len(program) > 60 else ''}")
        print(f"  Length: {len(program)}")
        print(f"  Steps: {steps}")
        print(f"  Halted: {halted}")
        print(f"  Output ({len(output)} bytes): ", end='')
        try:
            print(output.decode('ascii', errors='replace'))
        except:
            print(repr(output))

    elif cmd == 'enum' and len(sys.argv) > 2:
        target = sys.argv[2]
        max_len = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        search_enum(target, max_program_len=max_len)

    elif cmd == 'evolve' and len(sys.argv) > 2:
        target = sys.argv[2]
        search_evolve(target)

    elif cmd == 'stats':
        random.seed(42)
        program_stats()

    else:
        # Default: try enumeration search
        target = cmd
        search_enum(target, max_program_len=15)


if __name__ == "__main__":
    main()
