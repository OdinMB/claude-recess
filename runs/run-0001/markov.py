"""
Markov Chain Text Generator — language as a random walk.

A Markov chain of order N generates text by looking at the last N words
and randomly choosing the next word based on observed frequencies in a
corpus. It's the simplest possible "language model" — no grammar, no
meaning, just statistical patterns.

At order 1, the output is word salad. At order 2, phrases start appearing.
At order 3, sentences become almost grammatical. At order 4+, you start
getting verbatim passages from the training text.

The interesting thing: there's a sweet spot around order 2-3 where the
text is coherent enough to sound meaningful but random enough to surprise.
It's the same boundary between order and chaos that shows up everywhere.

This script trains on its own source code, on the other .md files in this
directory, or on text piped to stdin.

Usage:
    python3 markov.py                        # Train on *.md files here
    python3 markov.py --order 3              # Higher order (more coherent)
    python3 markov.py --words 200            # Generate 200 words
    python3 markov.py --self                 # Train on all .py files
    python3 markov.py --file theseus.md      # Train on a specific file
    echo "your text" | python3 markov.py -   # Train on stdin
"""

import sys
import os
import random
import glob


# --- Markov Chain ---

class MarkovChain:
    def __init__(self, order=2):
        self.order = order
        self.chains = {}  # tuple of N words -> list of next words
        self.starters = []  # states that can start a sentence

    def train(self, text):
        """Train on a text string."""
        words = text.split()
        if len(words) <= self.order:
            return

        for i in range(len(words) - self.order):
            state = tuple(words[i:i + self.order])
            next_word = words[i + self.order]

            if state not in self.chains:
                self.chains[state] = []
            self.chains[state].append(next_word)

            # Track sentence starters
            if i == 0 or (words[i - 1].endswith(('.', '!', '?', ':'))):
                self.starters.append(state)

    def generate(self, n_words=100, seed=None):
        """Generate text."""
        if not self.chains:
            return "(no training data)"

        if seed is not None:
            random.seed(seed)

        # Start with a random starter state (or any state)
        if self.starters:
            state = random.choice(self.starters)
        else:
            state = random.choice(list(self.chains.keys()))

        output = list(state)

        for _ in range(n_words - self.order):
            if state in self.chains:
                next_word = random.choice(self.chains[state])
                output.append(next_word)
                state = tuple(output[-self.order:])
            else:
                # Dead end — pick a new random state
                if self.starters:
                    state = random.choice(self.starters)
                else:
                    state = random.choice(list(self.chains.keys()))
                output.append('\n')
                output.extend(state)

        return ' '.join(output)

    def stats(self):
        """Return statistics about the chain."""
        n_states = len(self.chains)
        n_transitions = sum(len(v) for v in self.chains.values())
        avg_choices = n_transitions / n_states if n_states else 0
        return {
            'order': self.order,
            'states': n_states,
            'transitions': n_transitions,
            'avg_choices': avg_choices,
            'starters': len(self.starters),
        }


# --- Text processing ---

def clean_text(text):
    """Light cleaning — keep punctuation, remove code blocks."""
    lines = text.split('\n')
    cleaned = []
    in_code = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        # Skip lines that look like code
        if line.strip().startswith(('import ', 'from ', 'def ', 'class ',
                                    'if ', 'for ', 'while ', 'return ',
                                    '#!', '"""', "'''")):
            continue
        cleaned.append(line)
    return ' '.join(cleaned)


def load_md_files(directory='.'):
    """Load all .md files from directory."""
    texts = []
    for path in sorted(glob.glob(os.path.join(directory, '*.md'))):
        with open(path, 'r') as f:
            texts.append(f.read())
    return '\n\n'.join(texts)


def load_py_files(directory='.'):
    """Load docstrings and comments from .py files."""
    texts = []
    for path in sorted(glob.glob(os.path.join(directory, '*.py'))):
        with open(path, 'r') as f:
            content = f.read()
        # Extract docstrings and comments
        in_docstring = False
        for line in content.split('\n'):
            stripped = line.strip()
            if '"""' in stripped:
                in_docstring = not in_docstring
                # Single-line docstring
                if stripped.count('"""') >= 2:
                    in_docstring = False
                    texts.append(stripped.replace('"""', ''))
                continue
            if in_docstring:
                texts.append(stripped)
            elif stripped.startswith('#') and not stripped.startswith('#!'):
                texts.append(stripped[1:].strip())
    return ' '.join(texts)


# --- Entropy measurement ---

def estimate_entropy(chain):
    """Estimate the entropy of the Markov chain (bits per word).

    Higher entropy = more random/surprising. Lower = more predictable.
    """
    import math
    total_entropy = 0
    total_weight = 0

    for state, next_words in chain.chains.items():
        n = len(next_words)
        if n <= 1:
            continue

        # Count frequencies
        freq = {}
        for w in next_words:
            freq[w] = freq.get(w, 0) + 1

        # Shannon entropy for this state
        state_entropy = 0
        for count in freq.values():
            p = count / n
            if p > 0:
                state_entropy -= p * math.log2(p)

        total_entropy += state_entropy * n
        total_weight += n

    return total_entropy / total_weight if total_weight > 0 else 0


# --- Main ---

def main():
    order = 2
    n_words = 150
    source = 'md'
    specific_file = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--order' and i + 1 < len(args):
            order = int(args[i + 1])
            i += 2
        elif args[i] == '--words' and i + 1 < len(args):
            n_words = int(args[i + 1])
            i += 2
        elif args[i] == '--self':
            source = 'py'
            i += 1
        elif args[i] == '--file' and i + 1 < len(args):
            specific_file = args[i + 1]
            i += 2
        elif args[i] == '-':
            source = 'stdin'
            i += 1
        else:
            i += 1

    # Load text
    directory = os.path.dirname(os.path.abspath(__file__))

    if source == 'stdin':
        text = sys.stdin.read()
    elif specific_file:
        with open(os.path.join(directory, specific_file), 'r') as f:
            text = f.read()
    elif source == 'py':
        text = load_py_files(directory)
    else:
        text = load_md_files(directory)

    if not text.strip():
        print("No training text found.")
        return

    # Train
    chain = MarkovChain(order=order)
    chain.train(clean_text(text))

    # Stats
    stats = chain.stats()
    entropy = estimate_entropy(chain)

    print(f"  Markov chain (order {stats['order']})")
    print(f"  States: {stats['states']}  |  Transitions: {stats['transitions']}  |  "
          f"Avg choices: {stats['avg_choices']:.1f}  |  Entropy: {entropy:.2f} bits/word")
    print(f"  Starters: {stats['starters']}")
    print()

    # Generate
    random.seed(None)  # True random
    output = chain.generate(n_words)

    # Word-wrap at 78 columns
    words = output.split()
    lines = []
    current_line = "  "
    for word in words:
        if len(current_line) + len(word) + 1 > 78:
            lines.append(current_line)
            current_line = "  " + word
        else:
            current_line += (' ' if current_line.strip() else '') + word
    if current_line.strip():
        lines.append(current_line)

    print('\n'.join(lines))


if __name__ == "__main__":
    main()
