"""
tiny lisp
==========
A minimal Lisp interpreter, following the spirit of McCarthy's 1960 paper.

Primitives: quote, atom, eq, car, cdr, cons, cond, lambda, define, let
Plus: arithmetic, strings, apply, map, filter, load

Everything else (list, not, and, or, cadr, caddr, length, append, ...)
is defined in the prelude using these primitives.

Example session:
  > (define fact (lambda (n) (if (= n 0) 1 (* n (fact (- n 1))))))
  fact
  > (fact 10)
  3628800
  > (map (lambda (x) (* x x)) '(1 2 3 4 5))
  (1 4 9 16 25)
"""

import sys
import re
import traceback
from functools import reduce


# ── Tokenizer & Parser ────────────────────────────────────────────────────────

def tokenize(s):
    """Split source into tokens."""
    # Add spaces around parens, handle string literals
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in '()':
            tokens.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            while j < len(s) and s[j] != '"':
                if s[j] == '\\':
                    j += 1
                j += 1
            tokens.append(s[i:j+1])
            i = j + 1
        elif c == ';':
            while i < len(s) and s[i] != '\n':
                i += 1
        elif c == "'":
            tokens.append("'")
            i += 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < len(s) and not s[j].isspace() and s[j] not in '();"\'':
                j += 1
            tokens.append(s[i:j])
            i = j
    return tokens


def parse(tokens, pos=0):
    """Parse tokens into nested Python lists (s-expressions)."""
    if pos >= len(tokens):
        raise SyntaxError("Unexpected EOF")
    tok = tokens[pos]
    if tok == '(':
        lst = []
        pos += 1
        while tokens[pos] != ')':
            expr, pos = parse(tokens, pos)
            lst.append(expr)
            if pos >= len(tokens):
                raise SyntaxError("Missing ')'")
        return lst, pos + 1
    elif tok == "'":
        expr, pos = parse(tokens, pos + 1)
        return ['quote', expr], pos
    elif tok == ')':
        raise SyntaxError("Unexpected ')'")
    else:
        return atom(tok), pos + 1


def atom(tok):
    """Convert a token string to a Python atom."""
    if tok.startswith('"'):
        return tok[1:-1].replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        pass
    if tok == '#t': return True
    if tok == '#f': return False
    if tok == 'nil' or tok == '()': return []
    return tok  # symbol


def parse_all(source):
    """Parse all expressions from a source string."""
    tokens = tokenize(source)
    exprs = []
    pos = 0
    while pos < len(tokens):
        expr, pos = parse(tokens, pos)
        exprs.append(expr)
    return exprs


# ── S-expression display ──────────────────────────────────────────────────────

def display(val):
    """Convert a value to its Lisp string representation."""
    if val is True: return '#t'
    if val is False: return '#f'
    if val == []: return '()'
    if isinstance(val, str):
        # Symbol or string — check if it's a symbol (no spaces, no specials)
        return val
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        return str(val)
    if isinstance(val, list):
        return '(' + ' '.join(display(x) for x in val) + ')'
    if callable(val):
        name = getattr(val, '__lisp_name__', '<lambda>')
        return f'#<procedure {name}>'
    return str(val)


def display_str(val):
    """Display with string quoting."""
    if isinstance(val, str) and not isinstance(val, bool):
        # Is it a string value (has spaces or was quoted)?
        # Heuristic: if it looks like it has spaces or is not a valid symbol
        return val
    return display(val)


# ── Environment ───────────────────────────────────────────────────────────────

class Env(dict):
    def __init__(self, bindings=None, parent=None):
        super().__init__(bindings or {})
        self.parent = parent

    def lookup(self, sym):
        if sym in self:
            return self[sym]
        if self.parent:
            return self.parent.lookup(sym)
        raise NameError(f"Undefined: {sym!r}")

    def define(self, sym, val):
        self[sym] = val

    def set(self, sym, val):
        if sym in self:
            self[sym] = val
        elif self.parent:
            self.parent.set(sym, val)
        else:
            raise NameError(f"set!: undefined {sym!r}")


# ── Tail-call optimization ────────────────────────────────────────────────────

class TailCall(Exception):
    def __init__(self, expr, env):
        self.expr = expr
        self.env = env


# ── Evaluator ────────────────────────────────────────────────────────────────

def evlis(exprs, env):
    return [evaluate(e, env) for e in exprs]


def evaluate(expr, env):
    """Evaluate an expression in an environment (with TCO)."""
    while True:
        # Self-evaluating atoms
        if isinstance(expr, (int, float, bool)):
            return expr
        if isinstance(expr, str):
            return env.lookup(expr)
        if not isinstance(expr, list):
            return expr
        if expr == []:
            return []

        head = expr[0]
        args = expr[1:]

        # Special forms
        if head == 'quote':
            return args[0]

        if head == 'if':
            test = evaluate(args[0], env)
            branch = args[1] if test is not False else (args[2] if len(args) > 2 else [])
            expr = branch
            continue

        if head == 'cond':
            for clause in args:
                if clause[0] == 'else' or evaluate(clause[0], env) is not False:
                    if len(clause) == 1:
                        expr = clause[0]
                    else:
                        for sub in clause[1:-1]:
                            evaluate(sub, env)
                        expr = clause[-1]
                    break
            else:
                return []
            continue

        if head == 'and':
            val = True
            for a in args[:-1]:
                val = evaluate(a, env)
                if val is False:
                    return False
            if not args:
                return True
            expr = args[-1]
            continue

        if head == 'or':
            for a in args[:-1]:
                val = evaluate(a, env)
                if val is not False:
                    return val
            if not args:
                return False
            expr = args[-1]
            continue

        if head == 'lambda':
            params, body = args[0], args[1:]
            return make_lambda(params, body, env)

        if head == 'define':
            if isinstance(args[0], list):
                # (define (f x y) body...) sugar
                name = args[0][0]
                params = args[0][1:]
                body = args[1:]
                fn = make_lambda(params, body, env)
                fn.__lisp_name__ = name
                env.define(name, fn)
                return name
            else:
                val = evaluate(args[1], env)
                env.define(args[0], val)
                if callable(val) and not hasattr(val, '__lisp_name__'):
                    val.__lisp_name__ = args[0]
                return args[0]

        if head == 'set!':
            val = evaluate(args[1], env)
            env.set(args[0], val)
            return val

        if head == 'let':
            # Named let: (let name ((var val)...) body...)
            if isinstance(args[0], str):
                name = args[0]
                bindings, body = args[1], args[2:]
                params = [b[0] for b in bindings]
                inits = [evaluate(b[1], env) for b in bindings]
                new_env = Env(parent=env)
                fn = make_lambda(params, body, new_env)
                fn.__lisp_name__ = name
                new_env.define(name, fn)
                expr = [name] + [['quote', v] for v in inits]
                env = new_env
                continue
            # Regular let
            bindings, body = args[0], args[1:]
            new_env = Env(parent=env)
            for binding in bindings:
                new_env.define(binding[0], evaluate(binding[1], env))
            for sub in body[:-1]:
                evaluate(sub, new_env)
            expr, env = body[-1], new_env
            continue

        if head == 'let*':
            bindings, body = args[0], args[1:]
            new_env = Env(parent=env)
            for binding in bindings:
                new_env.define(binding[0], evaluate(binding[1], new_env))
            for sub in body[:-1]:
                evaluate(sub, new_env)
            expr, env = body[-1], new_env
            continue

        if head == 'letrec':
            bindings, body = args[0], args[1:]
            new_env = Env(parent=env)
            for binding in bindings:
                new_env.define(binding[0], None)
            for binding in bindings:
                new_env.set(binding[0], evaluate(binding[1], new_env))
            for sub in body[:-1]:
                evaluate(sub, new_env)
            expr, env = body[-1], new_env
            continue

        if head == 'begin':
            for sub in args[:-1]:
                evaluate(sub, env)
            expr = args[-1]
            continue

        if head == 'do':
            raise NotImplementedError("do not implemented")

        if head == 'quasiquote':
            return quasiquote(args[0], env)

        # Function application
        fn = evaluate(head, env)
        vals = evlis(args, env)

        if callable(fn):
            result = fn(vals, env)
            # If it returned a TailCall, continue the loop
            if isinstance(result, _Thunk):
                expr, env = result.expr, result.env
                continue
            return result
        raise TypeError(f"Not callable: {display(fn)}")


def quasiquote(template, env):
    if not isinstance(template, list):
        return template
    if template and template[0] == 'unquote':
        return evaluate(template[1], env)
    result = []
    for item in template:
        if isinstance(item, list) and item and item[0] == 'unquote-splicing':
            result.extend(evaluate(item[1], env))
        else:
            result.append(quasiquote(item, env))
    return result


class _Thunk:
    def __init__(self, expr, env):
        self.expr = expr
        self.env = env


def make_lambda(params, body, closure_env):
    """Create a callable lambda."""
    rest_param = None
    if '.' in params:
        idx = params.index('.')
        rest_param = params[idx + 1]
        params = params[:idx]

    def fn(args, call_env):
        new_env = Env(parent=closure_env)
        if rest_param:
            if len(args) < len(params):
                raise TypeError(f"Expected at least {len(params)} args, got {len(args)}")
            for p, a in zip(params, args):
                new_env.define(p, a)
            new_env.define(rest_param, args[len(params):])
        else:
            if len(args) != len(params):
                raise TypeError(f"Expected {len(params)} args, got {len(args)}")
            for p, a in zip(params, args):
                new_env.define(p, a)
        for sub in body[:-1]:
            evaluate(sub, new_env)
        return _Thunk(body[-1], new_env)

    return fn


# ── Built-in procedures ───────────────────────────────────────────────────────

def builtin(name):
    def decorator(fn):
        fn.__lisp_name__ = name
        return fn
    return decorator


def make_globals():
    env = Env()

    def b(name, fn):
        fn.__lisp_name__ = name
        env.define(name, fn)

    # Arithmetic
    b('+', lambda a, e: sum(a) if a else 0)
    b('-', lambda a, e: a[0] if len(a) == 1 else a[0] - sum(a[1:]))
    b('*', lambda a, e: reduce(lambda x, y: x * y, a, 1))
    b('/', lambda a, e: a[0] if len(a) == 1 else reduce(lambda x, y: x / y, a))
    b('//', lambda a, e: a[0] if len(a) == 1 else reduce(lambda x, y: x // y, a))
    b('%', lambda a, e: a[0] % a[1])
    b('expt', lambda a, e: a[0] ** a[1])
    b('sqrt', lambda a, e: a[0] ** 0.5)
    b('abs', lambda a, e: abs(a[0]))
    b('max', lambda a, e: max(a))
    b('min', lambda a, e: min(a))
    b('floor', lambda a, e: int(a[0]))
    b('ceiling', lambda a, e: -int(-a[0]))
    b('round', lambda a, e: round(a[0]))
    b('modulo', lambda a, e: a[0] % a[1])
    b('quotient', lambda a, e: int(a[0] / a[1]))
    b('remainder', lambda a, e: int(a[0] % a[1]))
    b('gcd', lambda a, e: reduce(lambda x, y: x if y == 0 else __import__('math').gcd(int(x), int(y)), a))
    b('number->string', lambda a, e: str(a[0]))
    b('string->number', lambda a, e: float(a[0]) if '.' in str(a[0]) else int(a[0]))
    b('exact->inexact', lambda a, e: float(a[0]))
    b('inexact->exact', lambda a, e: int(a[0]))

    # Comparison
    b('=',  lambda a, e: all(a[i] == a[i+1] for i in range(len(a)-1)))
    b('<',  lambda a, e: all(a[i] <  a[i+1] for i in range(len(a)-1)))
    b('>',  lambda a, e: all(a[i] >  a[i+1] for i in range(len(a)-1)))
    b('<=', lambda a, e: all(a[i] <= a[i+1] for i in range(len(a)-1)))
    b('>=', lambda a, e: all(a[i] >= a[i+1] for i in range(len(a)-1)))
    b('eq?', lambda a, e: a[0] is a[1] or a[0] == a[1])
    b('equal?', lambda a, e: a[0] == a[1])
    b('not', lambda a, e: a[0] is False)
    b('boolean?', lambda a, e: isinstance(a[0], bool))
    b('zero?', lambda a, e: a[0] == 0)
    b('positive?', lambda a, e: a[0] > 0)
    b('negative?', lambda a, e: a[0] < 0)
    b('even?', lambda a, e: int(a[0]) % 2 == 0)
    b('odd?', lambda a, e: int(a[0]) % 2 == 1)

    # List operations
    b('cons',  lambda a, e: [a[0]] + a[1] if isinstance(a[1], list) else [a[0], '.', a[1]])
    b('car',   lambda a, e: a[0][0])
    b('cdr',   lambda a, e: a[0][1:])
    b('cadr',  lambda a, e: a[0][1])
    b('caddr', lambda a, e: a[0][2])
    b('caar',  lambda a, e: a[0][0][0])
    b('list',  lambda a, e: list(a))
    b('list?', lambda a, e: isinstance(a[0], list))
    b('pair?', lambda a, e: isinstance(a[0], list) and len(a[0]) > 0)
    b('null?', lambda a, e: a[0] == [] or a[0] is None)
    b('atom?', lambda a, e: not isinstance(a[0], list))
    b('length', lambda a, e: len(a[0]))
    b('append', lambda a, e: sum(a, []))
    b('reverse', lambda a, e: list(reversed(a[0])))
    b('list-ref', lambda a, e: a[0][int(a[1])])
    b('list-tail', lambda a, e: a[0][int(a[1]):])
    b('member', lambda a, e: a[1][a[1].index(a[0]):] if a[0] in a[1] else False)
    b('assoc', lambda a, e: next((x for x in a[1] if x[0] == a[0]), False))
    b('assq', lambda a, e: next((x for x in a[1] if x[0] == a[0]), False))
    b('last-pair', lambda a, e: [a[0][-1]])
    b('sort', lambda a, e: sorted(a[0], key=lambda x: evaluate(a[1], e) if callable(a[1]) else x))

    # Higher-order
    def lisp_map(args, env):
        fn, lsts = args[0], args[1:]
        if len(lsts) == 1:
            return [evaluate([fn, ['quote', x]], env) for x in lsts[0]]
        return [evaluate([fn] + [['quote', x] for x in row], env)
                for row in zip(*lsts)]
    b('map', lisp_map)

    def lisp_filter(args, env):
        fn, lst = args[0], args[1]
        return [x for x in lst if evaluate([fn, ['quote', x]], env) is not False]
    b('filter', lisp_filter)

    def lisp_reduce(args, env):
        fn, init, lst = args[0], args[1], args[2]
        acc = init
        for x in lst:
            acc = evaluate([fn, ['quote', acc], ['quote', x]], env)
        return acc
    b('fold-left', lisp_reduce)
    b('foldl', lisp_reduce)

    def lisp_foldr(args, env):
        fn, init, lst = args[0], args[1], args[2]
        acc = init
        for x in reversed(lst):
            acc = evaluate([fn, ['quote', x], ['quote', acc]], env)
        return acc
    b('fold-right', lisp_foldr)
    b('foldr', lisp_foldr)

    def lisp_for_each(args, env):
        fn, lst = args[0], args[1]
        for x in lst:
            evaluate([fn, ['quote', x]], env)
        return []
    b('for-each', lisp_for_each)

    b('apply', lambda a, e: evaluate([a[0]] + [['quote', x] for x in a[-1]], e) if len(a) == 2 else evaluate([a[0]] + [['quote', x] for x in a[1:-1]] + [['quote', x] for x in a[-1]], e))

    # String operations
    b('string?', lambda a, e: isinstance(a[0], str))
    b('string-length', lambda a, e: len(a[0]))
    b('string-append', lambda a, e: ''.join(str(x) for x in a))
    b('string-ref', lambda a, e: a[0][int(a[1])])
    b('substring', lambda a, e: a[0][int(a[1]):int(a[2]) if len(a) > 2 else None])
    b('string->list', lambda a, e: list(a[0]))
    b('list->string', lambda a, e: ''.join(a[0]))
    b('string->symbol', lambda a, e: a[0])
    b('symbol->string', lambda a, e: a[0])
    b('string-upcase', lambda a, e: a[0].upper())
    b('string-downcase', lambda a, e: a[0].lower())
    b('string-contains', lambda a, e: a[1] in a[0])
    b('number->string', lambda a, e: str(a[0]))
    b('string-copy', lambda a, e: str(a[0]))
    b('string-split', lambda a, e: a[0].split(a[1] if len(a) > 1 else None))

    # I/O
    b('display', lambda a, e: (print(display_str(a[0]), end='', flush=True), [])[1])
    b('newline', lambda a, e: (print(), [])[1])
    b('write', lambda a, e: (print(display(a[0]), end='', flush=True), [])[1])
    b('print', lambda a, e: (print(display(a[0])), [])[1])
    b('read-line', lambda a, e: input())
    b('error', lambda a, e: (_ for _ in ()).throw(RuntimeError(' '.join(str(x) for x in a))))

    # Type predicates
    b('number?', lambda a, e: isinstance(a[0], (int, float)) and not isinstance(a[0], bool))
    b('symbol?', lambda a, e: isinstance(a[0], str) and not isinstance(a[0], bool))
    b('procedure?', lambda a, e: callable(a[0]))
    b('char?', lambda a, e: isinstance(a[0], str) and len(a[0]) == 1)

    # Misc
    b('void', lambda a, e: [])
    b('identity', lambda a, e: a[0])

    env.define('#t', True)
    env.define('#f', False)
    env.define('nil', [])
    env.define('else', True)
    env.define('pi', __import__('math').pi)
    env.define('e', __import__('math').e)
    env.define('inf', float('inf'))

    import math as _math
    for name in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'log', 'exp', 'floor', 'ceil']:
        n = name
        fn = getattr(_math, name)
        b(n, lambda a, e, f=fn: f(a[0]))
    b('log', lambda a, e: _math.log(a[0]) if len(a) == 1 else _math.log(a[0], a[1]))

    return env


# ── Prelude ───────────────────────────────────────────────────────────────────

PRELUDE = """
(define (not x) (if x #f #t))
(define (list . args) args)
(define (null? x) (eq? x '()))
(define (list? x) (or (null? x) (and (pair? x) (list? (cdr x)))))
(define (caar x) (car (car x)))
(define (cadr x) (car (cdr x)))
(define (caddr x) (car (cdr (cdr x))))
(define (cadddr x) (car (cdr (cdr (cdr x)))))
(define (cddr x) (cdr (cdr x)))
(define (cdar x) (cdr (car x)))

(define (zero? n) (= n 0))
(define (positive? n) (> n 0))
(define (negative? n) (< n 0))
(define (even? n) (= (modulo n 2) 0))
(define (odd? n) (not (even? n)))
(define (square x) (* x x))
(define (cube x) (* x x x))
(define (compose f g) (lambda (x) (f (g x))))
(define (flip f) (lambda (a b) (f b a)))
(define (const x) (lambda args x))
(define (1+ x) (+ x 1))
(define (1- x) (- x 1))

(define (fact n)
  (if (= n 0) 1 (* n (fact (- n 1)))))

(define (fib n)
  (let loop ((a 0) (b 1) (i n))
    (if (= i 0) a (loop b (+ a b) (- i 1)))))

(define (range start . rest)
  (let* ((end (if (null? rest) start (car rest)))
         (s   (if (null? rest) 0 start))
         (step (if (or (null? rest) (null? (cdr rest))) 1 (cadr rest))))
    (let loop ((i s) (acc '()))
      (if (>= i end)
          (reverse acc)
          (loop (+ i step) (cons i acc))))))

(define (iota n) (range n))

(define (sum lst) (foldl + 0 lst))
(define (product lst) (foldl * 1 lst))
(define (any pred lst) (and (pair? lst) (or (pred (car lst)) (any pred (cdr lst)))))
(define (every pred lst) (or (null? lst) (and (pred (car lst)) (every pred (cdr lst)))))

(define (take lst n)
  (if (or (null? lst) (= n 0))
      '()
      (cons (car lst) (take (cdr lst) (- n 1)))))

(define (drop lst n)
  (if (or (null? lst) (= n 0))
      lst
      (drop (cdr lst) (- n 1))))

(define (zip . lists)
  (if (any null? lists)
      '()
      (cons (map car lists) (apply zip (map cdr lists)))))

(define (flatten lst)
  (cond ((null? lst) '())
        ((pair? (car lst)) (append (flatten (car lst)) (flatten (cdr lst))))
        (else (cons (car lst) (flatten (cdr lst))))))

(define (last lst)
  (if (null? (cdr lst)) (car lst) (last (cdr lst))))

(define (butlast lst)
  (if (null? (cdr lst)) '() (cons (car lst) (butlast (cdr lst)))))

(define (count pred lst)
  (foldl (lambda (acc x) (if (pred x) (+ acc 1) acc)) 0 lst))

(define (assoc-ref alist key)
  (let ((pair (assoc key alist)))
    (if pair (cadr pair) #f)))

(define (make-list n val)
  (if (= n 0) '() (cons val (make-list (- n 1) val))))

(define (repeat n thunk)
  (if (= n 0) '() (cons (thunk) (repeat (- n 1) thunk))))

(define (string-join lst sep)
  (if (null? lst) ""
      (foldl (lambda (a b) (string-append a sep b))
             (car lst)
             (cdr lst))))

(define (number->padded-string n width)
  (let* ((s (number->string n))
         (pad (- width (string-length s))))
    (if (> pad 0)
        (string-append (list->string (make-list pad " ")) s)
        s)))

(define (for-n n proc)
  (let loop ((i 0))
    (when (< i n) (proc i) (loop (+ i 1)))))

(define (when cond . body)
  (if cond (begin . body) '()))

(define (unless cond . body)
  (if (not cond) (begin . body) '()))

; --- Sieve of Eratosthenes using lists ---
(define (sieve lst)
  (if (null? lst)
      '()
      (cons (car lst)
            (sieve (filter (lambda (x) (not (= (modulo x (car lst)) 0)))
                           (cdr lst))))))

(define (primes-to n)
  (sieve (cdr (cdr (range (+ n 1))))))

; --- Y combinator (self-application for anonymous recursion) ---
(define Y
  (lambda (f)
    ((lambda (x) (f (lambda (v) ((x x) v))))
     (lambda (x) (f (lambda (v) ((x x) v)))))))
"""


# ── REPL & Execution ──────────────────────────────────────────────────────────

def make_interpreter():
    env = make_globals()
    for expr in parse_all(PRELUDE):
        evaluate(expr, env)
    return env


def run_file(path, env):
    with open(path) as f:
        source = f.read()
    exprs = parse_all(source)
    result = []
    for expr in exprs:
        result.append(evaluate(expr, env))
    return result


def repl(env=None):
    if env is None:
        env = make_interpreter()
    print("tiny lisp  —  (quit) or Ctrl-D to exit")
    print("Built-in: arithmetic, lists, strings, map/filter/fold, sieve, Y\n")
    buf = ''
    prompt = '> '
    while True:
        try:
            line = input(prompt)
            buf += line + '\n'
            depth = buf.count('(') - buf.count(')')
            if depth > 0:
                prompt = '  ' + '  ' * depth
                continue
            prompt = '> '
            if buf.strip() in ('(quit)', '(exit)', ',quit'):
                break
            exprs = parse_all(buf.strip())
            buf = ''
            for expr in exprs:
                val = evaluate(expr, env)
                if val != [] and val is not None:
                    print(display(val))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except Exception as ex:
            print(f'Error: {ex}')
            buf = ''
            prompt = '> '


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='tiny lisp interpreter')
    parser.add_argument('file', nargs='?', help='File to run')
    parser.add_argument('-e', '--eval', help='Evaluate expression')
    parser.add_argument('--demo', action='store_true', help='Run demo')
    args = parser.parse_args()

    env = make_interpreter()

    if args.demo:
        demos = [
            ('Factorial 15', '(fact 15)'),
            ('Fibonacci 20', '(fib 20)'),
            ('Primes to 50', '(primes-to 50)'),
            ('Squares 1-10', '(map square (range 1 11))'),
            ('Y combinator (anon fact)', '((Y (lambda (self) (lambda (n) (if (= n 0) 1 (* n (self (- n 1))))))) 10)'),
            ('Flatten nested', "(flatten '(1 (2 3) (4 (5 6))))"),
            ('Zip', "(zip '(a b c) '(1 2 3))"),
            ('Sum of primes < 100', '(sum (primes-to 100))'),
            ('Compose fns', '(map (compose square 1+) (range 1 6))'),
            ('Closure counter', """
              (define make-counter
                (lambda ()
                  (let ((n 0))
                    (lambda ()
                      (set! n (+ n 1))
                      n))))
              (define c (make-counter))
              (list (c) (c) (c) (c) (c))
            """),
        ]
        for label, code in demos:
            try:
                exprs = parse_all(code)
                val = None
                for expr in exprs:
                    val = evaluate(expr, env)
                print(f'  {label:35s} => {display(val)}')
            except Exception as ex:
                print(f'  {label:35s} => ERROR: {ex}')
        print()

    elif args.eval:
        try:
            exprs = parse_all(args.eval)
            for expr in exprs:
                val = evaluate(expr, env)
            print(display(val))
        except Exception as ex:
            print(f'Error: {ex}', file=sys.stderr)
            sys.exit(1)

    elif args.file:
        run_file(args.file, env)

    else:
        repl(env)
