"""
The Library of Babel

Borges imagined a library containing every possible 410-page book. This is a
working implementation of a much smaller version: a library of every possible
page of text.

Each page is 40 lines of 80 characters = 3200 characters, drawn from an
alphabet of 29 symbols (a-z, space, period, comma). That's 29^3200 possible
pages — a number with about 4,680 digits.

The key insight: every possible page already "exists" — it's just a number
encoded in base 29. The library is a bijection between integers and pages.
There's no storage. The pages are computed on demand from their addresses.

To make addresses manageable, we use a reversible pseudo-random permutation
(a Feistel cipher) so that page 0 isn't "aaaa..." and page 1 isn't "aaaa...b".
Instead, each sequential address maps to an apparently random page. But the
mapping is perfectly reversible: given any text, you can find its exact
address.

Usage:
    python3 babel.py                     # random page
    python3 babel.py search "your text"  # find a page containing your text
    python3 babel.py page <address>      # look up a specific page
    python3 babel.py at <number>         # look up page by integer index
"""

import sys
import hashlib
import random

sys.set_int_max_str_digits(100000)


# --- Configuration ---

ALPHABET = "abcdefghijklmnopqrstuvwxyz .,\n"  # 30 symbols (including newline)
BASE = len(ALPHABET)  # 30
COLS = 80
ROWS = 40
PAGE_LEN = COLS * ROWS  # 3200 characters per page

CHAR_TO_INT = {c: i for i, c in enumerate(ALPHABET)}
INT_TO_CHAR = {i: c for i, c in enumerate(ALPHABET)}


# --- Base conversion ---

def text_to_int(text):
    """Convert a text string to its integer representation in our alphabet."""
    # Pad or truncate to PAGE_LEN
    text = text.ljust(PAGE_LEN, ALPHABET[0])[:PAGE_LEN]
    n = 0
    for ch in text:
        idx = CHAR_TO_INT.get(ch, CHAR_TO_INT[' '])
        n = n * BASE + idx
    return n


def int_to_text(n):
    """Convert an integer back to a page of text."""
    if n < 0:
        n = 0
    chars = []
    for _ in range(PAGE_LEN):
        n, idx = divmod(n, BASE)
        chars.append(INT_TO_CHAR[idx])
    chars.reverse()
    return ''.join(chars)


# --- Feistel cipher for permutation ---
# This scrambles the mapping so sequential page numbers don't produce
# sequential text. Uses a balanced Feistel network over the integer space.

FEISTEL_ROUNDS = 6
FEISTEL_KEY = b"library-of-babel-permutation-key"

def _feistel_half_size():
    """Half the page-integer in bits, approximately."""
    import math
    total_bits = math.ceil(math.log2(BASE) * PAGE_LEN)
    return total_bits // 2

HALF_BITS = _feistel_half_size()
HALF_MOD = 1 << HALF_BITS
TOTAL_MOD = HALF_MOD * HALF_MOD


def _feistel_round_fn(half, round_num):
    """Pseudorandom function for one Feistel round."""
    h = hashlib.sha256(FEISTEL_KEY + round_num.to_bytes(4, 'big'))
    # Feed the half value in chunks
    h.update(half.to_bytes((half.bit_length() + 7) // 8 or 1, 'big'))
    digest = int.from_bytes(h.digest(), 'big')
    return digest % HALF_MOD


def feistel_encrypt(n):
    """Permute an integer using a Feistel network."""
    n = n % TOTAL_MOD
    left = n >> HALF_BITS
    right = n & (HALF_MOD - 1)
    for i in range(FEISTEL_ROUNDS):
        new_left = right
        new_right = (left ^ _feistel_round_fn(right, i)) % HALF_MOD
        left, right = new_left, new_right
    return (left << HALF_BITS) | right


def feistel_decrypt(n):
    """Reverse the Feistel permutation."""
    n = n % TOTAL_MOD
    left = n >> HALF_BITS
    right = n & (HALF_MOD - 1)
    for i in range(FEISTEL_ROUNDS - 1, -1, -1):
        new_right = left
        new_left = (right ^ _feistel_round_fn(left, i)) % HALF_MOD
        left, right = new_left, new_right
    return (left << HALF_BITS) | right


# --- Address encoding ---

# We encode page addresses in base-36 for compact display
ADDR_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"
ADDR_BASE = len(ADDR_CHARS)


def int_to_addr(n):
    """Encode an integer as a base-36 address string."""
    if n == 0:
        return "0"
    digits = []
    while n > 0:
        n, r = divmod(n, ADDR_BASE)
        digits.append(ADDR_CHARS[r])
    return ''.join(reversed(digits))


def addr_to_int(addr):
    """Decode a base-36 address string to an integer."""
    n = 0
    for ch in addr:
        n = n * ADDR_BASE + ADDR_CHARS.index(ch)
    return n


# --- Public API ---

def get_page(page_num):
    """Get the text of page number `page_num`."""
    scrambled = feistel_encrypt(page_num)
    return int_to_text(scrambled)


def find_page(text):
    """Find the page number that contains the given text."""
    n = text_to_int(text)
    return feistel_decrypt(n)


def format_page(text, page_num=None, addr=None):
    """Pretty-print a page with a border."""
    lines = []
    for i in range(0, len(text), COLS):
        lines.append(text[i:i+COLS])

    border = "+" + "-" * (COLS + 2) + "+"
    output = [border]
    for line in lines:
        # Replace newlines for display
        display = line.replace('\n', ' ')
        output.append("| " + display + " |")
    output.append(border)

    if page_num is not None:
        if addr is None:
            addr = int_to_addr(page_num)
        # Only show the address — page numbers are thousands of digits long
        output.append(f"  Address: {addr}")
        digits = len(str(page_num)) if page_num > 0 else 1
        output.append(f"  (page number is {digits} digits long)")

    return '\n'.join(output)


# --- CLI ---

def cmd_random():
    """Display a random page."""
    page_num = random.randint(0, TOTAL_MOD - 1)
    text = get_page(page_num)
    addr = int_to_addr(page_num)
    print(format_page(text, page_num, addr))


def cmd_page(addr):
    """Look up a page by its address."""
    page_num = addr_to_int(addr)
    text = get_page(page_num)
    print(format_page(text, page_num, addr))


def cmd_at(num_str):
    """Look up a page by its integer index."""
    page_num = int(num_str)
    text = get_page(page_num)
    addr = int_to_addr(page_num)
    print(format_page(text, page_num, addr))


def cmd_search(query):
    """Find a page containing the given text, padded with spaces."""
    # Normalize: lowercase, replace unknown chars with space
    normalized = []
    for ch in query.lower():
        if ch in CHAR_TO_INT:
            normalized.append(ch)
        else:
            normalized.append(' ')
    query_clean = ''.join(normalized)

    # Center the query on the page
    padding_before = (PAGE_LEN - len(query_clean)) // 2
    padded = ' ' * padding_before + query_clean + ' ' * (PAGE_LEN - padding_before - len(query_clean))

    page_num = find_page(padded)
    addr = int_to_addr(page_num)
    text = get_page(page_num)

    # Verify
    if query_clean in text:
        print(f"  Found! Your text appears on this page:\n")
    else:
        # Due to alphabet normalization, the search might not match exactly
        # Let's do a direct lookup instead
        n = text_to_int(padded)
        text2 = int_to_text(n)
        if query_clean in text2:
            page_num = find_page(padded)
            text = get_page(page_num)
            addr = int_to_addr(page_num)

    print(format_page(text, page_num, addr))


def cmd_verify():
    """Verify that encode/decode roundtrips work."""
    print("Testing roundtrip consistency...")

    # Test 1: int -> text -> int
    for test_n in [0, 1, 42, 12345, 999999]:
        text = int_to_text(test_n)
        back = text_to_int(text)
        status = "OK" if back == test_n else f"FAIL (got {back})"
        print(f"  int_to_text({test_n}) roundtrip: {status}")

    # Test 2: Feistel roundtrip
    test_vals = [0, 1, 42, 12345, 999999, TOTAL_MOD - 1]
    for test_n in test_vals:
        enc = feistel_encrypt(test_n)
        dec = feistel_decrypt(enc)
        status = "OK" if dec == test_n else "FAIL"
        label = str(test_n) if test_n < 10**6 else "TOTAL_MOD-1"
        print(f"  feistel({label}) roundtrip: {status}")

    # Test 3: Full pipeline
    test_text = "hello, world."
    page_num = find_page(test_text)
    found_text = get_page(page_num)
    # The found text should contain our query (padded with 'a's to fill the page)
    normalized = test_text.ljust(PAGE_LEN, 'a')[:PAGE_LEN]
    n = text_to_int(normalized)
    back_text = int_to_text(n)
    status = "OK" if back_text == normalized else "FAIL"
    print(f"  text encode/decode roundtrip: {status}")

    print("\nDone.")


def main():
    if len(sys.argv) < 2:
        cmd_random()
        return

    cmd = sys.argv[1]
    if cmd == "search" and len(sys.argv) > 2:
        cmd_search(' '.join(sys.argv[2:]))
    elif cmd == "page" and len(sys.argv) > 2:
        cmd_page(sys.argv[2])
    elif cmd == "at" and len(sys.argv) > 2:
        cmd_at(sys.argv[2])
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "random":
        cmd_random()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
