"""
Tiny Lambda Calculus Interpreter

The lambda calculus: invented by Alonzo Church in the 1930s.
Three constructs are all you need for universal computation:

  x           variable
  λx.M        abstraction  (a function taking x, returning M)
  M N         application  (apply M to N)

That's it. No numbers. No booleans. No loops. Just functions.

Church showed that numbers, booleans, arithmetic, recursion —
everything — can be encoded as functions applied to functions.

This interpreter does:
  - Parsing of a simple lambda calculus syntax
  - Alpha conversion (rename bound variables to avoid capture)
  - Beta reduction (function application)
  - Step-by-step evaluation trace
  - Church numerals and combinators pre-defined

Syntax: \\x.x  for λx.x  (backslash = lambda)
        f x    for application  (left-associative)
        (M)    for grouping
"""

import re
from dataclasses import dataclass
from typing import Union, Optional


# === AST Nodes ===

@dataclass(frozen=True)
class Var:
    name: str

    def __str__(self):
        return self.name

@dataclass(frozen=True)
class Lam:
    param: str
    body: 'Term'

    def __str__(self):
        return f"λ{self.param}.{self.body}"

@dataclass(frozen=True)
class App:
    func: 'Term'
    arg: 'Term'

    def __str__(self):
        f = str(self.func)
        a = str(self.arg)
        # Add parentheses where needed
        if isinstance(self.func, Lam):
            f = f"({f})"
        if isinstance(self.arg, (App, Lam)):
            a = f"({a})"
        return f"{f} {a}"

Term = Union[Var, Lam, App]


# === Parser ===

def tokenize(s):
    tokens = []
    i = 0
    while i < len(s):
        if s[i].isspace():
            i += 1
        elif s[i] == '\\' or s[i] == 'λ':
            tokens.append('LAM')
            i += 1
        elif s[i] == '.':
            tokens.append('.')
            i += 1
        elif s[i] == '(':
            tokens.append('(')
            i += 1
        elif s[i] == ')':
            tokens.append(')')
            i += 1
        elif s[i].isalnum() or s[i] == '_':
            j = i
            while j < len(s) and (s[j].isalnum() or s[j] == '_'):
                j += 1
            tokens.append(('ID', s[i:j]))
            i = j
        else:
            i += 1
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected=None):
        tok = self.tokens[self.pos]
        self.pos += 1
        if expected and tok != expected:
            raise ValueError(f"Expected {expected}, got {tok}")
        return tok

    def parse_term(self):
        """Parse a full term (handles application as left-associative)."""
        atoms = []
        while self.peek() is not None and self.peek() not in (')', '.'):
            atoms.append(self.parse_atom())
        if not atoms:
            raise ValueError("Empty term")
        result = atoms[0]
        for atom in atoms[1:]:
            result = App(result, atom)
        return result

    def parse_atom(self):
        """Parse a single atom: var, lambda, or parenthesized term."""
        tok = self.peek()
        if tok == 'LAM':
            self.consume('LAM')
            # Collect parameters
            params = []
            while self.peek() and isinstance(self.peek(), tuple) and self.peek()[0] == 'ID':
                params.append(self.consume()[1])
            self.consume('.')
            body = self.parse_term()
            # Build nested lambdas (currying)
            result = body
            for p in reversed(params):
                result = Lam(p, result)
            return result
        elif tok == '(':
            self.consume('(')
            term = self.parse_term()
            self.consume(')')
            return term
        elif isinstance(tok, tuple) and tok[0] == 'ID':
            self.consume()
            return Var(tok[1])
        else:
            raise ValueError(f"Unexpected token: {tok}")


def parse(s):
    tokens = tokenize(s)
    parser = Parser(tokens)
    result = parser.parse_term()
    if parser.pos != len(tokens):
        raise ValueError(f"Unexpected tokens at position {parser.pos}: {tokens[parser.pos:]}")
    return result


# === Substitution and Reduction ===

_counter = [0]

def fresh(name):
    """Generate a fresh variable name."""
    _counter[0] += 1
    return f"{name}_{_counter[0]}"


def free_vars(term):
    """Return the set of free variables in a term."""
    if isinstance(term, Var):
        return {term.name}
    elif isinstance(term, Lam):
        return free_vars(term.body) - {term.param}
    elif isinstance(term, App):
        return free_vars(term.func) | free_vars(term.arg)


def subst(term, var, replacement):
    """Substitute var with replacement in term (with alpha conversion)."""
    if isinstance(term, Var):
        if term.name == var:
            return replacement
        return term
    elif isinstance(term, Lam):
        if term.param == var:
            # Variable is bound here, don't substitute inside
            return term
        fv_repl = free_vars(replacement)
        if term.param in fv_repl:
            # Alpha conversion needed to avoid capture
            new_param = fresh(term.param)
            new_body = subst(term.body, term.param, Var(new_param))
            return Lam(new_param, subst(new_body, var, replacement))
        return Lam(term.param, subst(term.body, var, replacement))
    elif isinstance(term, App):
        return App(subst(term.func, var, replacement), subst(term.arg, var, replacement))


def step(term):
    """Perform one beta-reduction step (leftmost-outermost / normal order).
    Returns (new_term, True) if a reduction was performed, else (term, False)."""
    if isinstance(term, Var):
        return term, False
    elif isinstance(term, Lam):
        new_body, reduced = step(term.body)
        return Lam(term.param, new_body), reduced
    elif isinstance(term, App):
        # Try to reduce the function
        if isinstance(term.func, Lam):
            # Beta reduction: (λx.M) N → M[x := N]
            return subst(term.func.body, term.func.param, term.arg), True
        new_func, reduced = step(term.func)
        if reduced:
            return App(new_func, term.arg), True
        new_arg, reduced = step(term.arg)
        return App(term.func, new_arg), reduced


def normalize(term, max_steps=1000, trace=False):
    """Reduce a term to normal form, optionally printing each step."""
    steps = 0
    if trace:
        print(f"  → {term}")
    while steps < max_steps:
        new_term, reduced = step(term)
        if not reduced:
            break
        term = new_term
        steps += 1
        if trace:
            s = str(term)
            if len(s) > 80:
                s = s[:77] + "..."
            print(f"  → {s}")
    if steps == max_steps:
        print(f"  [stopped after {max_steps} steps — may not terminate]")
    return term, steps


# === Church Encodings ===

# Numbers: n = λf.λx. f^n x
CHURCH = {
    'zero':  r'\f.\x.x',
    'one':   r'\f.\x.f x',
    'two':   r'\f.\x.f (f x)',
    'three': r'\f.\x.f (f (f x))',
    'four':  r'\f.\x.f (f (f (f x)))',
}

# Successor: succ = λn.λf.λx. f (n f x)
COMBINATORS = {
    'I':    r'\x.x',           # Identity
    'K':    r'\x.\y.x',        # Constant (True in Church encoding)
    'KI':   r'\x.\y.y',        # False
    'S':    r'\f.\g.\x.f x (g x)',  # Substitution
    'ω':    r'\x.x x',         # Self-application
    'Ω':    r'(\x.x x)(\x.x x)',   # Infinite loop
    'Y':    r'\f.(\x.f(x x))(\x.f(x x))',  # Y combinator (fixed point)
    'succ': r'\n.\f.\x.f(n f x)',  # Church successor
    'plus': r'\m.\n.\f.\x.m f (n f x)',  # Church addition
    'mult': r'\m.\n.\f.m(n f)',    # Church multiplication
    'pred': r'\n.\f.\x.n(\g.\h.h(g f))(\u.x)(\u.u)',  # Predecessor
    'true': r'\a.\b.a',
    'false':r'\a.\b.b',
    'and':  r'\p.\q.p q p',
    'or':   r'\p.\q.p p q',
    'not':  r'\p.\a.\b.p b a',
    'if':   r'\p.\a.\b.p a b',
    'pair': r'\a.\b.\f.f a b',
    'fst':  r'\p.p(\a.\b.a)',
    'snd':  r'\p.p(\a.\b.b)',
}


def church_to_int(term, max_steps=5000):
    """Try to convert a Church numeral to a Python int."""
    # Apply term to a counter function and a zero
    # Use special sentinel values
    class F:
        def __init__(self, n): self.n = n
        def __repr__(self): return f"<f^{self.n}>"

    # Can't easily do this symbolically, but we can check the shape
    # of the term: λf.λx. f (f (f ... (f x)...))
    t = term
    if not isinstance(t, Lam): return None
    f_name = t.param
    t = t.body
    if not isinstance(t, Lam): return None
    x_name = t.param
    t = t.body

    count = 0
    while isinstance(t, App):
        if not isinstance(t.func, Var) or t.func.name != f_name:
            return None
        t = t.arg
        count += 1

    if isinstance(t, Var) and t.name == x_name:
        return count
    return None


def demonstrate():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║              L A M B D A   C A L C U L U S                         ║")
    print("║  Three constructs. Universal computation.                           ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print("─" * 72)
    print("  COMBINATORS")
    print("─" * 72)
    print()

    demos = [
        ("Identity applied to itself", r"(\x.x)(\x.x)"),
        ("I I I (three identities)", r"(\x.x)((\x.x)(\x.x))"),
        ("K applied to two args (selects first)", r"(\x.\y.x) a b"),
        ("KI selects second", r"(\x.\y.y) a b"),
        ("S I I self-application", r"(\f.\g.\x.f x(g x))(\x.x)(\x.x) z"),
        ("ω self-application (one step)", r"(\x.x x)(\x.x x)"),
    ]

    for desc, expr in demos:
        print(f"  {desc}:")
        print(f"  {expr}")
        try:
            t = parse(expr)
            result, nsteps = normalize(t, max_steps=20, trace=True)
            print(f"  [{nsteps} steps]")
        except Exception as e:
            print(f"  Error: {e}")
        print()

    print("─" * 72)
    print("  CHURCH ARITHMETIC")
    print("─" * 72)
    print()

    two = parse(CHURCH['two'])
    three = parse(CHURCH['three'])
    succ = parse(COMBINATORS['succ'])
    plus = parse(COMBINATORS['plus'])
    mult = parse(COMBINATORS['mult'])

    print("  Church encoding: numbers are iterated function application")
    print(f"  zero  = λf.λx. x          (apply f zero times)")
    print(f"  two   = λf.λx. f(f x)     (apply f twice)")
    print(f"  three = λf.λx. f(f(f x))  (apply f three times)")
    print()

    print("  succ(two) → ?")
    t = App(succ, two)
    result, nsteps = normalize(t, max_steps=200, trace=True)
    n = church_to_int(result)
    print(f"  [{nsteps} steps] → Church numeral for {n}")
    print()

    print("  two + three → ?")
    t = App(App(plus, two), three)
    result, nsteps = normalize(t, max_steps=500, trace=True)
    n = church_to_int(result)
    print(f"  [{nsteps} steps] → Church numeral for {n}")
    print()

    print("  two × three → ?")
    t = App(App(mult, two), three)
    result, nsteps = normalize(t, max_steps=500, trace=True)
    n = church_to_int(result)
    print(f"  [{nsteps} steps] → Church numeral for {n}")
    print()

    print("─" * 72)
    print("  Y COMBINATOR (fixed-point)")
    print("─" * 72)
    print()
    print("  Y f = f (Y f)")
    print("  The Y combinator finds fixed points. Used to encode recursion.")
    print("  Without Y, you can't write self-referential functions.")
    print()
    print(f"  Y = {COMBINATORS['Y']}")
    print()
    Y = parse(COMBINATORS['Y'])
    f = Var('f')
    # Y applied to identity: Y I = I (Y I) = I I (Y I) = ... diverges
    print("  Y I (would diverge — showing first 5 steps):")
    t = App(Y, parse(r'\x.x'))
    print(f"  {t}")
    for i in range(5):
        t, reduced = step(t)
        if not reduced: break
        s = str(t)
        print(f"  → {s[:80] + '...' if len(s) > 80 else s}")
    print("  ...")
    print()

    print("─" * 72)
    print("  BOOLEANS AND CONDITIONALS")
    print("─" * 72)
    print()
    print("  true  = λa.λb.a  (select first argument)")
    print("  false = λa.λb.b  (select second argument)")
    print("  if    = λp.λa.λb.p a b  (just apply the boolean!)")
    print()

    true  = parse(COMBINATORS['true'])
    false = parse(COMBINATORS['false'])
    not_  = parse(COMBINATORS['not'])
    and_  = parse(COMBINATORS['and'])

    print("  not true → ?")
    t = App(not_, true)
    result, nsteps = normalize(t, max_steps=100, trace=True)
    print(f"  [{nsteps} steps]")
    print()

    print("  true and false → ?")
    t = App(App(and_, true), false)
    result, nsteps = normalize(t, max_steps=100, trace=True)
    print(f"  [{nsteps} steps]")
    print()

    print("  if true a b → ?  (should give 'a')")
    iff = parse(COMBINATORS['if'])
    t = App(App(App(iff, true), Var('a')), Var('b'))
    result, nsteps = normalize(t, max_steps=100, trace=True)
    print(f"  [{nsteps} steps]")
    print()

    print("─" * 72)
    print("  WHAT THIS MEANS")
    print("─" * 72)
    print()
    print("  Lambda calculus is Turing complete with just λ, variables, and application.")
    print("  No built-in numbers, booleans, loops, or data structures.")
    print("  Church showed in 1936 that 'computable function' and 'lambda-definable'")
    print("  are the same thing — before computers existed.")
    print()
    print("  The Y combinator enables recursion without naming functions.")
    print("  SKI combinators form a Turing-complete system with no variables.")
    print()
    print("  Everything is a function. Functions all the way down.")
    print()


if __name__ == '__main__':
    demonstrate()
