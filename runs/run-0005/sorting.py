"""
Sorting Algorithms as Visual Fingerprints

When you visualize the state of an array at each step of sorting,
each algorithm creates a distinctive visual pattern.

The view: rows = steps in time, columns = array positions.
The character at each position shows the element's relative value.
(lighter = smaller, darker = larger)

This reveals the algorithm's "structure":
- Bubble sort: diagonal waves pushing large elements to the right
- Insertion sort: sorted region growing from the left
- Selection sort: minimum found and placed, one by one
- Merge sort: recursive halving then merging
- Quick sort: partitioning structure, pivot placement
- Shell sort: large jumps early, refinement later
"""

import random
import math


SHADE = ' ░▒▓█'


def value_to_char(v, min_v, max_v):
    """Map a value to a display character based on its relative rank."""
    if max_v == min_v:
        return SHADE[0]
    frac = (v - min_v) / (max_v - min_v)
    idx = int(frac * (len(SHADE) - 1))
    return SHADE[max(0, min(len(SHADE)-1, idx))]


def snapshot(arr):
    """Take a snapshot of array state as a string of chars."""
    if not arr:
        return ''
    min_v, max_v = min(arr), max(arr)
    return ''.join(value_to_char(v, min_v, max_v) for v in arr)


def render_sort_history(history, width=60, height=40):
    """
    Render sorting history as a 2D fingerprint.
    history = list of array states (each a list of values)
    Shows at most 'height' rows sampled from history.
    """
    n = len(history)
    if n == 0:
        return []

    # Sample rows from history
    indices = [int(i * (n-1) / (height-1)) for i in range(height)]
    indices = sorted(set(indices))

    # Trim each to width
    lines = []
    min_v = min(min(s) for s in history if s)
    max_v = max(max(s) for s in history if s)

    for idx in indices:
        state = history[idx]
        # Sample state to width
        m = len(state)
        chars = []
        for c in range(width):
            arr_idx = int(c * (m-1) / (width-1)) if width > 1 else 0
            chars.append(value_to_char(state[arr_idx], min_v, max_v))
        lines.append(''.join(chars))

    return lines


# ── Sorting Algorithms ────────────────────────────────────────────────────────

def bubble_sort(arr):
    """O(n²) average — exchanges bubble up."""
    history = [arr[:]]
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
            history.append(arr[:])
    return history


def insertion_sort(arr):
    """O(n²) average — builds sorted region from left."""
    history = [arr[:]]
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j+1] = arr[j]
            j -= 1
            history.append(arr[:])
        arr[j+1] = key
        history.append(arr[:])
    return history


def selection_sort(arr):
    """O(n²) — finds minimum and places it."""
    history = [arr[:]]
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
            history.append(arr[:])
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
        history.append(arr[:])
    return history


def merge_sort(arr):
    """O(n log n) — divide and conquer."""
    history = [arr[:]]

    def merge(arr, left, mid, right):
        L = arr[left:mid+1]
        R = arr[mid+1:right+1]
        i = j = 0
        k = left
        while i < len(L) and j < len(R):
            if L[i] <= R[j]:
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            k += 1
            history.append(arr[:])
        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1
            history.append(arr[:])
        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1
            history.append(arr[:])

    def ms(arr, left, right):
        if left < right:
            mid = (left + right) // 2
            ms(arr, left, mid)
            ms(arr, mid+1, right)
            merge(arr, left, mid, right)

    ms(arr, 0, len(arr)-1)
    history.append(arr[:])
    return history


def quick_sort(arr):
    """O(n log n) average — partition around pivot."""
    history = [arr[:]]

    def partition(arr, low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                history.append(arr[:])
        arr[i+1], arr[high] = arr[high], arr[i+1]
        history.append(arr[:])
        return i + 1

    def qs(arr, low, high):
        if low < high:
            pi = partition(arr, low, high)
            qs(arr, low, pi-1)
            qs(arr, pi+1, high)

    qs(arr, 0, len(arr)-1)
    history.append(arr[:])
    return history


def shell_sort(arr):
    """O(n^1.5) average — large gaps first, then insertion sort."""
    history = [arr[:]]
    n = len(arr)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            while j >= gap and arr[j-gap] > temp:
                arr[j] = arr[j-gap]
                j -= gap
                history.append(arr[:])
            arr[j] = temp
            history.append(arr[:])
        gap //= 2
    return history


def counting_sort(arr, max_val=None):
    """O(n+k) — non-comparison sort for integers."""
    history = [arr[:]]
    if max_val is None:
        max_val = max(arr)
    count = [0] * (max_val + 1)
    for x in arr:
        count[x] += 1
    idx = 0
    for v, c in enumerate(count):
        for _ in range(c):
            arr[idx] = v
            idx += 1
            history.append(arr[:])
    return history


def radix_sort(arr):
    """O(nk) — sort by individual digits."""
    history = [arr[:]]
    max_val = max(arr)
    exp = 1
    while max_val // exp > 0:
        # Counting sort on digit at position exp
        n = len(arr)
        output = [0] * n
        count = [0] * 10
        for x in arr:
            count[(x // exp) % 10] += 1
        for i in range(1, 10):
            count[i] += count[i-1]
        for i in range(n-1, -1, -1):
            digit = (arr[i] // exp) % 10
            output[count[digit]-1] = arr[i]
            count[digit] -= 1
        arr[:] = output
        history.append(arr[:])
        exp *= 10
    return history


def heap_sort(arr):
    """O(n log n) — heapify, then extract max."""
    history = [arr[:]]
    n = len(arr)

    def heapify(arr, n, i):
        largest = i
        l, r = 2*i+1, 2*i+2
        if l < n and arr[l] > arr[largest]:
            largest = l
        if r < n and arr[r] > arr[largest]:
            largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            history.append(arr[:])
            heapify(arr, n, largest)

    for i in range(n//2-1, -1, -1):
        heapify(arr, n, i)

    for i in range(n-1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        history.append(arr[:])
        heapify(arr, i, 0)

    history.append(arr[:])
    return history


def show_algorithm(name, desc, complexity, sort_fn, data):
    """Show a sorting algorithm's fingerprint."""
    arr = data[:]
    history = sort_fn(arr)

    print(f"┌─ {name} ─{'─' * max(1, 58-len(name))}┐")
    print(f"│  {desc}")
    print(f"│  Complexity: {complexity}    Steps recorded: {len(history)}")
    print("│")

    lines = render_sort_history(history, width=68, height=28)
    for line in lines:
        print("│" + line)
    print("│")
    print(f"│  First: {' '.join(str(x) for x in history[0][:12])}...")
    print(f"│  Last:  {' '.join(str(x) for x in history[-1][:12])}...")
    print("└" + "─" * 71)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           S O R T I N G   A L G O R I T H M S                      ║")
    print("║  Visualized as time × space fingerprints                           ║")
    print("║  Darker = larger value   Rows = time   Columns = array position    ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    random.seed(42)
    N = 40
    data_random = random.sample(range(1, N+1), N)
    data_reversed = list(range(N, 0, -1))
    data_nearly = list(range(1, N+1))
    # Scramble a few
    for _ in range(N // 5):
        i, j = random.randint(0, N-1), random.randint(0, N-1)
        data_nearly[i], data_nearly[j] = data_nearly[j], data_nearly[i]

    print(f"  Input: {N} elements, random permutation")
    print(f"  {data_random}")
    print()

    algorithms = [
        ("Bubble Sort", "Adjacent pairs compared and swapped if out of order", "O(n²)",
         bubble_sort, data_random[:]),
        ("Insertion Sort", "Grows a sorted prefix, inserting each element in place", "O(n²)",
         insertion_sort, data_random[:]),
        ("Selection Sort", "Finds minimum, places it; repeat for remaining elements", "O(n²)",
         selection_sort, data_random[:]),
        ("Shell Sort", "Insertion sort with shrinking gap sequence (Knuth's sequence)", "O(n^1.5)",
         shell_sort, data_random[:]),
        ("Merge Sort", "Recursive divide-and-conquer: split, sort halves, merge", "O(n log n)",
         merge_sort, data_random[:]),
        ("Quick Sort", "Partition around pivot, recurse on each part", "O(n log n) avg",
         quick_sort, data_random[:]),
        ("Heap Sort", "Build max-heap, extract elements in order", "O(n log n)",
         heap_sort, data_random[:]),
        ("Radix Sort", "Sort by individual digits — no comparisons", "O(nk)",
         radix_sort, data_random[:]),
    ]

    for name, desc, complexity, fn, data in algorithms:
        show_algorithm(name, desc, complexity, fn, data)

    print("  The fingerprints reveal structure invisible in code:")
    print("  - Bubble sort: diagonal 'waves' as large elements float right")
    print("  - Insertion sort: clean sorted region growing from left")
    print("  - Selection sort: filled strip advancing from left, chaotic right")
    print("  - Merge sort: recursive bisection is visible as horizontal bands")
    print("  - Quick sort: pivot placement creates a 'tree' structure")
    print("  - Heap sort: heap phase (top half) then extraction (bottom half)")
    print("  - Radix sort: clean columns — sorts by digit position, not value")
    print()
    print("  All produce the same sorted result. The journeys differ.")
    print()


if __name__ == '__main__':
    main()
