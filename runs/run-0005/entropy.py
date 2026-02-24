"""
Information Entropy

Claude Shannon (1948): the amount of information in a message can be
quantified. The entropy of a probability distribution is:

    H = -Σ p_i × log₂(p_i)   (measured in bits)

This is the minimum average number of bits needed to encode one symbol
from the distribution. It's also Boltzmann's formula from thermodynamics
(with log_e instead of log₂ and a physical constant k):

    S = -k × Σ p_i × ln(p_i)   (Boltzmann 1877)

The same formula appears in:
  - Information theory (Shannon 1948)
  - Statistical mechanics (Boltzmann 1877, Gibbs 1878)
  - Quantum information (von Neumann entropy)
  - Machine learning (cross-entropy loss)
  - Decision trees (information gain)
"""

import math
import heapq
from collections import Counter, defaultdict


def entropy(distribution):
    """Shannon entropy in bits. distribution is a list/dict of probabilities."""
    if isinstance(distribution, dict):
        probs = list(distribution.values())
    else:
        probs = distribution

    total = sum(probs)
    probs = [p / total for p in probs if p > 0]

    return -sum(p * math.log2(p) for p in probs)


def entropy_of_string(s):
    """Entropy of the character distribution of a string."""
    if not s:
        return 0.0
    freq = Counter(s)
    n = len(s)
    return entropy({c: f/n for c, f in freq.items()})


# ── Huffman Coding ────────────────────────────────────────────────────────────

def huffman_code(frequencies):
    """Build Huffman code. Returns dict: symbol → binary string."""
    heap = [(freq, i, symbol, None, None) for i, (symbol, freq) in enumerate(frequencies.items())]
    heapq.heapify(heap)
    counter = len(heap)

    while len(heap) > 1:
        f1, _, s1, l1, r1 = heapq.heappop(heap)
        f2, _, s2, l2, r2 = heapq.heappop(heap)
        merged = (f1 + f2, counter, None, (f1, s1, l1, r1), (f2, s2, l2, r2))
        counter += 1
        heapq.heappush(heap, merged)

    if not heap:
        return {}

    _, _, _, root_l, root_r = heap[0]

    codes = {}
    def walk(node, prefix):
        f, _, sym, left, right = node
        if sym is not None:  # Leaf
            codes[sym] = prefix or '0'
            return
        if left:
            walk(left, prefix + '0')
        if right:
            walk(right, prefix + '1')

    # Rebuild the tree structure
    def huffman_tree(node, prefix=''):
        if node is None:
            return
        freq, _, sym, left, right = node
        if sym is not None:
            codes[sym] = prefix or '0'
        else:
            if left:
                huffman_tree(left, prefix + '0')
            if right:
                huffman_tree(right, prefix + '1')

    if root_l or root_r:
        # Reconstruct from heap
        pass

    # Simpler approach: recursive Huffman
    return build_huffman(frequencies)


def build_huffman(frequencies):
    """Build Huffman code using a cleaner recursive approach."""
    if not frequencies:
        return {}
    if len(frequencies) == 1:
        return {list(frequencies.keys())[0]: '0'}

    # Build priority queue with (freq, symbol_or_None, subtree)
    items = sorted(frequencies.items(), key=lambda x: x[1])

    class Node:
        def __init__(self, freq, symbol=None, left=None, right=None):
            self.freq = freq
            self.symbol = symbol
            self.left = left
            self.right = right
        def __lt__(self, other):
            return self.freq < other.freq

    heap = [Node(freq, sym) for sym, freq in items]
    heapq.heapify(heap)

    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        heapq.heappush(heap, Node(a.freq + b.freq, None, a, b))

    codes = {}
    def traverse(node, prefix=''):
        if node.symbol is not None:
            codes[node.symbol] = prefix or '0'
            return
        traverse(node.left, prefix + '0')
        traverse(node.right, prefix + '1')

    traverse(heap[0])
    return codes


def average_code_length(frequencies, codes):
    """Average code length given a frequency distribution and codes."""
    total = sum(frequencies.values())
    return sum(freq/total * len(codes[sym]) for sym, freq in frequencies.items())


# ── Demonstrations ────────────────────────────────────────────────────────────

def section_entropy_of_distributions():
    print("┌─ Entropy of Different Distributions ───────────────────────────────┐")
    print("│  H = -Σ p × log₂(p)  bits per symbol")
    print("│")

    examples = [
        ("Certain outcome",      {1: 1.0}),
        ("Fair coin",            {H: 0.5, T: 0.5}),
        ("Biased coin p=0.9",    {H: 0.9, T: 0.1}),
        ("Fair die (6 sides)",   {i: 1/6 for i in range(1, 7)}),
        ("Loaded die",           {1: 0.5, 2: 0.2, 3: 0.1, 4: 0.1, 5: 0.05, 6: 0.05}),
        ("Fair 4-sided die",     {i: 0.25 for i in range(4)}),
        ("26 equal letters",     {chr(65+i): 1/26 for i in range(26)}),
        ("English letter freq",  {
            'e': 0.127, 't': 0.091, 'a': 0.082, 'o': 0.075, 'i': 0.070,
            'n': 0.067, 's': 0.063, 'h': 0.061, 'r': 0.060, 'd': 0.043,
            # (simplified — remaining ~22% spread over other letters)
            '_': 0.220
        }),
    ]

    for name, dist in examples:
        h = entropy(dist)
        max_h = math.log2(len(dist)) if len(dist) > 1 else 0
        efficiency = h / max_h if max_h > 0 else 1.0
        bar_len = int(h * 6)
        bar = '█' * bar_len
        print(f"│  {name:<30s}  H = {h:.4f} bits  {bar}")

    print("│")
    print("│  Maximum entropy: log₂(n) for n equally-likely outcomes")
    print("│  A uniform distribution is maximally uncertain (maximally informative)")
    print("└" + "─" * 73)
    print()

H, T = 'H', 'T'


def section_entropy_of_text():
    print("┌─ Entropy of Text ───────────────────────────────────────────────────┐")
    print("│  Character-level entropy measures text 'randomness'")
    print("│  (Lower = more structured/compressible, Higher = more random/dense)")
    print("│")

    texts = {
        "All same letter: 'aaaa...'": "a" * 100,
        "Alternating: 'ababab...'": "ab" * 50,
        "π digits (0-9)": "31415926535897932384626433832795028841971693993751",
        "English prose":
            "the quick brown fox jumps over the lazy dog while the mathematician "
            "pondered the infinite series and its beautiful convergence properties",
        "Random-looking (primes mod 10)":
            "".join(str(n % 10) for n in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,
                                           53,59,61,67,71,73,79,83,89,97,101,103,107,
                                           109,113,127,131,137,139,149,151,157,163,167]),
        "DNA sequence (ACGT)":
            "ATCGATCGATCGATCGATCGATCGAATTCGAATTCGAATTCGATCGATCGATCG",
        "Random DNA":
            "ACGTTAGCGTATCGAATCGATCGATCGATCGTAGCTGATCGATCGATCGATCGA",
        "Binary counter":
            "".join(format(i, '04b') for i in range(16)),
        "Pure random (simulated)":
            "aeBkzQpXmLwRdTsYjNcVoUhFgIiKnOpqrstuvwxyz0123456789!@#$%^",
    }

    for name, text in texts.items():
        h = entropy_of_string(text)
        unique = len(set(text))
        max_h = math.log2(unique) if unique > 1 else 0
        eff = h / max_h if max_h > 0 else 1.0
        bar = '█' * int(h * 4)
        print(f"│  {name[:40]:<40s}")
        print(f"│    H={h:.3f}  symbols={unique}  efficiency={eff:.2%}  {bar}")
        print("│")

    print("└" + "─" * 73)
    print()


def section_huffman(text=None):
    if text is None:
        text = "the quick brown fox jumps over the lazy dog"

    print("┌─ Huffman Coding ────────────────────────────────────────────────────┐")
    print(f"│  Optimal prefix-free code for: \"{text[:50]}\"")
    print("│")

    freq = Counter(text)
    total = len(text)
    codes = build_huffman(freq)

    h = entropy_of_string(text)
    avg_len = average_code_length(freq, codes)

    print(f"│  Symbol  Freq   Prob    Code           Bits")
    print(f"│  ──────  ─────  ──────  ─────────────  ────")

    # Sort by frequency descending
    for sym, count in sorted(freq.items(), key=lambda x: -x[1]):
        prob = count / total
        code = codes[sym]
        display_sym = repr(sym) if sym == ' ' else sym
        bar = '█' * count
        print(f"│  '{display_sym}'    {count:4d}   {prob:.3f}   {code:<14s}  {len(code)}")

    print("│")
    print(f"│  Entropy H = {h:.4f} bits/symbol")
    print(f"│  Huffman avg = {avg_len:.4f} bits/symbol")
    print(f"│  Overhead = {avg_len - h:.4f} bits/symbol (Huffman is within 1 bit of optimal)")
    print(f"│  Total message: {total} chars × {avg_len:.2f} bits = {int(total*avg_len)} bits")
    print(f"│  vs naive 8 bits/char: {total*8} bits  (compression: {total*avg_len/(total*8):.2%})")
    print("└" + "─" * 73)
    print()


def section_entropy_bounds():
    print("┌─ Entropy and Compression ───────────────────────────────────────────┐")
    print("│")
    print("│  Shannon's source coding theorem:")
    print("│  No lossless compression can go below the entropy H.")
    print("│  Huffman coding achieves H ≤ avg_length < H+1.")
    print("│  Arithmetic coding can get arbitrarily close to H.")
    print("│")
    print("│  Information content of one symbol (self-information):")
    print("│  I(p) = -log₂(p) bits")
    print("│")
    print("│  Rare events carry more information:")

    events = [
        ("Fair coin lands heads",           0.5),
        ("Die shows 6",                     1/6),
        ("Card drawn is ace of spades",     1/52),
        ("Random byte is exactly 42",       1/256),
        ("Lottery jackpot (1 in 10M)",      1e-7),
        ("Lightning strikes here today",    1e-6),
    ]

    for name, p in events:
        info = -math.log2(p)
        print(f"│    {name:<40s}  {p:.2e}  I={info:.1f} bits")

    print("│")
    print("│  H = E[I(X)] — entropy is the expected information content")
    print("│")
    print("│  Connection to thermodynamics:")
    print("│  S = k_B × H × ln(2)  — Boltzmann entropy equals Shannon entropy!")
    print("│  (up to a physical constant and logarithm base)")
    print("│  Maxwell's demon: to erase one bit requires k_B T ln(2) joules (Landauer)")
    print("└" + "─" * 73)
    print()


def section_conditional_entropy():
    print("┌─ Redundancy in English ─────────────────────────────────────────────┐")
    print("│  English has ~4.5 bits/char (character level)")
    print("│  But humans can read text with 50% of letters removed.")
    print("│  Shannon estimated true entropy ≈ 1 bit/character (word level).")
    print("│")

    # Show how letter frequencies in English deviate from uniform
    english_freq = {
        'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0, 'n': 6.7,
        's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3, 'l': 4.0, 'c': 2.8,
        'u': 2.8, 'm': 2.4, 'w': 2.4, 'f': 2.2, 'g': 2.0, 'y': 2.0,
        'p': 1.9, 'b': 1.5, 'v': 1.0, 'k': 0.8, 'j': 0.2, 'x': 0.2,
        'q': 0.1, 'z': 0.1
    }

    h_english = entropy(english_freq)
    h_uniform = math.log2(26)

    print(f"│  English letter frequency entropy: {h_english:.3f} bits/char")
    print(f"│  Uniform 26-letter distribution:   {h_uniform:.3f} bits/char")
    print(f"│  Redundancy: {(1 - h_english/h_uniform)*100:.1f}%  (English is this much more predictable)")
    print("│")
    print("│  Frequency visualization (top 10 letters):")
    top = sorted(english_freq.items(), key=lambda x: -x[1])[:10]
    for letter, pct in top:
        bar = '█' * int(pct * 2)
        print(f"│    {letter}: {bar} {pct:.1f}%")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         I N F O R M A T I O N   E N T R O P Y                      ║")
    print("║  H = -Σ p log₂ p  — Shannon 1948 = Boltzmann 1877                 ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    section_entropy_of_distributions()
    section_entropy_of_text()
    section_huffman()
    section_entropy_bounds()
    section_conditional_entropy()

    print("  Shannon's 1948 paper 'A Mathematical Theory of Communication'")
    print("  introduced entropy, mutual information, channel capacity,")
    print("  error-correcting codes, and the noisy channel coding theorem —")
    print("  essentially founding the field of information theory in one paper.")
    print()


if __name__ == '__main__':
    main()
