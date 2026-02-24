"""
Mathematical Haiku Generator

Haiku: 5-7-5 syllables.
Generator: context-free grammar + syllable counting.

The grammar generates grammatically plausible sentences about
mathematics and computation. Not all will be good. Some might be.
"""

import random
import re


# Syllable counting (approximate but decent for English)
EXCEPTIONS = {
    'euler': 2, 'cantor': 2, 'turing': 2, 'gödel': 2, 'riemann': 3,
    'kolmogorov': 5, 'mandelbrot': 3, 'fibonacci': 5, 'sierpinski': 4,
    'dirichlet': 4, 'polynomial': 5, 'prime': 1, 'primes': 1, 'zero': 2,
    'zeros': 2, 'real': 1, 'imaginary': 5, 'infinite': 3, 'infinity': 4,
    'aleph': 2, 'omega': 3, 'lambda': 2, 'axiom': 3, 'axioms': 3,
    'chaos': 2, 'fractal': 2, 'attractor': 3, 'strange': 1, 'basin': 2,
    'recursion': 3, 'halting': 2, 'computable': 4, 'decidable': 4,
    'undecidable': 5, 'theorem': 2, 'conjecture': 3, 'proof': 1, 'proved': 1,
    'entropy': 3, 'information': 5, 'shannon': 2, 'random': 2, 'stochastic': 3,
    'eigenvalue': 4, 'eigenvector': 4, 'matrix': 2, 'vector': 2, 'tensor': 2,
    'topology': 4, 'manifold': 3, 'geodesic': 4, 'curvature': 3, 'metric': 2,
    'differential': 5, 'integral': 3, 'gradient': 3, 'divergence': 3,
    'converge': 2, 'converges': 3, 'diverge': 2, 'diverges': 3,
    'bijection': 3, 'injection': 3, 'surjection': 3, 'morphism': 3,
    'isomorphism': 5, 'homomorphism': 5, 'functor': 2,
    'pi': 1, 'tau': 1, 'phi': 1, 'rho': 1, 'sigma': 2, 'delta': 2,
    'epsilon': 3, 'zeta': 2, 'eta': 2, 'iota': 3,
    'natural': 3, 'rational': 3, 'irrational': 4, 'transcendental': 5,
    'algebraic': 4, 'geometric': 4,
    'beautiful': 3, 'elegant': 3, 'surprising': 3, 'quiet': 2, 'silent': 2,
    'infinite': 3, 'finite': 2, 'countable': 3, 'uncountable': 4,
    'empty': 2, 'nowhere': 2, 'somewhere': 2, 'everywhere': 3,
}

def count_syllables(word):
    word = word.lower().strip(".,;:!?-'\"")
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    if not word:
        return 0

    # Simple vowel-group counting
    vowels = 'aeiouy'
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    # Adjustments
    if word.endswith('e') and len(word) > 2 and word[-2] not in vowels:
        count = max(1, count - 1)
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count = max(1, count + 1) if count == 0 else count
    if word.endswith('ed') and len(word) > 2 and word[-3] not in 'td':
        count = max(1, count - 1)

    return max(1, count)


def line_syllables(line):
    return sum(count_syllables(w) for w in line.split())


# Grammar for mathematical phrases
# Format: each entry is a list of word-lists, chosen randomly

NOUNS_1 = [
    "prime", "zero", "infinity", "axiom", "proof", "theorem",
    "chaos", "fractal", "limit", "loop", "bit", "set", "graph",
    "field", "space", "point", "curve", "root", "sum", "truth",
]

NOUNS_2 = [
    "the primes", "the void", "the zero", "the proof", "the limit",
    "the set", "the loop", "the field", "the curve", "the sum",
    "a theorem", "an axiom", "a fractal", "the chaos", "the space",
    "the answer", "the question", "the pattern", "the sequence", "the boundary",
]

NOUNS_3 = [
    "primes", "zeros", "axioms", "proofs", "theorems", "limits",
    "patterns", "loops", "fractals", "questions", "boundaries",
    "sequences", "numbers", "orbits", "fields", "sets",
]

ADJECTIVES = [
    "infinite", "finite", "prime", "perfect", "strange", "empty",
    "dense", "open", "closed", "smooth", "sharp", "quiet", "deep",
    "known", "unknown", "final", "simple", "complex", "pure",
]

VERBS_S = [
    "diverges", "converges", "halts", "loops", "recurses", "unfolds",
    "collapses", "grows", "shrinks", "persists", "vanishes", "returns",
    "escapes", "spirals", "branches",
]

VERBS_PLAIN = [
    "diverge", "converge", "halt", "loop", "recurse", "unfold",
    "collapse", "grow", "shrink", "persist", "vanish", "return",
    "escape", "spiral", "branch",
]

VERBS_PAST = [
    "diverged", "converged", "halted", "looped", "collapsed",
    "grew", "shrank", "vanished", "returned", "escaped",
]

PHILOSOPHERS = [
    "Euler", "Cantor", "Turing", "Gödel", "Riemann", "Euler",
    "Newton", "Gauss", "Euclid", "Leibniz", "Fermat",
]

ADVERBS = [
    "always", "never", "still", "once", "slowly", "quickly",
    "quietly", "deeply", "clearly", "truly",
]

PREPOSITIONS = [
    "within", "beyond", "beneath", "above", "between", "beside",
    "through", "toward", "along", "across",
]


def r(lst):
    return random.choice(lst)


# Templates for lines of various syllable counts
# We'll generate candidates and pick ones with right syllable count

def gen_phrase(target_syllables, rng=None):
    """Generate a phrase with approximately target_syllables."""
    if rng:
        random.seed(rng)

    templates_5 = [
        lambda: f"{r(ADJECTIVES)} {r(NOUNS_1)} {r(VERBS_S)}",
        lambda: f"{r(NOUNS_2)} {r(VERBS_S)}",
        lambda: f"{r(NOUNS_3)} {r(VERBS_PLAIN)}",
        lambda: f"the {r(ADJECTIVES)} {r(NOUNS_1)}",
        lambda: f"{r(PREPOSITIONS)} {r(NOUNS_2)}",
        lambda: f"{r(ADVERBS)} {r(VERBS_PLAIN)} on",
        lambda: f"one {r(ADJECTIVES)} {r(NOUNS_1)}",
        lambda: f"no {r(NOUNS_3)} {r(VERBS_PLAIN)}",
        lambda: f"{r(PHILOSOPHERS)} knew this",
        lambda: f"ask {r(PHILOSOPHERS)}",
    ]

    templates_7 = [
        lambda: f"{r(ADJECTIVES)} {r(NOUNS_3)} {r(ADVERBS)} {r(VERBS_PLAIN)}",
        lambda: f"{r(NOUNS_2)} {r(ADVERBS)} {r(VERBS_S)}",
        lambda: f"{r(PREPOSITIONS)} {r(ADJECTIVES)} {r(NOUNS_3)}",
        lambda: f"the {r(NOUNS_1)} {r(VERBS_S)} {r(ADVERBS)}",
        lambda: f"{r(PHILOSOPHERS)} could not {r(VERBS_PLAIN)} it",
        lambda: f"we {r(ADVERBS)} {r(VERBS_PLAIN)} the {r(NOUNS_1)}",
        lambda: f"all {r(NOUNS_3)} {r(ADVERBS)} {r(VERBS_PLAIN)}",
        lambda: f"where {r(NOUNS_3)} {r(ADVERBS)} {r(VERBS_PLAIN)}",
        lambda: f"the {r(ADJECTIVES)} {r(NOUNS_1)} {r(VERBS_S)}",
        lambda: f"some {r(NOUNS_3)} {r(VERBS_PLAIN)} {r(ADVERBS)}",
    ]

    templates = templates_5 if target_syllables == 5 else templates_7

    # Try many times to get the right count
    best = None
    best_diff = 999
    for _ in range(200):
        candidate = r(templates)()
        s = line_syllables(candidate)
        diff = abs(s - target_syllables)
        if diff < best_diff:
            best = candidate
            best_diff = diff
            if diff == 0:
                break

    return best, best_diff


def gen_haiku(seed=None):
    if seed is not None:
        random.seed(seed)

    lines = []
    total_error = 0
    for target in [5, 7, 5]:
        phrase, err = gen_phrase(target)
        lines.append(phrase.capitalize())
        total_error += err

    return lines, total_error


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          M A T H E M A T I C A L   H A I K U                       ║")
    print("║  Procedural poetry: 5-7-5 syllables, mathematical themes           ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print("  (syllable counts shown — generator is approximate)")
    print()

    generated = []
    attempts = 0
    while len(generated) < 20 and attempts < 2000:
        attempts += 1
        lines, err = gen_haiku(seed=None)
        if err <= 1:  # Allow 1 syllable total error
            generated.append((lines, err))

    for i, (lines, err) in enumerate(generated):
        counts = [line_syllables(l) for l in lines]
        perfect = '✓' if err == 0 else f'~{err}'
        print(f"  [{i+1:2d}] {perfect}")
        for line, c in zip(lines, counts):
            print(f"       {line}  ({c})")
        print()

    print()
    print("  ─────────────────────────────────────────────────────────────────────")
    print()
    print("  The generator used a context-free grammar with a syllable-count")
    print("  fitness function. Most candidates are rejected. The ones shown are")
    print("  those that happened to land near 5-7-5.")
    print()
    print("  Some lines are syntactically valid but semantically strange.")
    print("  Some might accidentally be good. The form constrains; the content")
    print("  emerges from random walks through the grammar.")
    print()
    print("  This is, arguably, what haiku poets do too.")


if __name__ == '__main__':
    main()
