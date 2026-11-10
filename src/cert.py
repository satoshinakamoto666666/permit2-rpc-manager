"""Certified fixed-point interval arithmetic.

Every routine here is exact integer arithmetic on fixed-point numbers scaled by
S = 10**SCALE.  A value v is represented as an integer pair (lo, hi) meaning
the true number lies in [lo/S, hi/S].  All rounding is DIRECTED (outward), so
the returned interval always CONTAINS the true value.  No floating point is
used anywhere: `float` and `math` are not imported by this module.

Contents
--------
* pi_bounds()      pi via Machin's formula, remainder bounded by the first
                   omitted term of an alternating series.
* sqrt_bounds(x)   certified square root of a fixed-point interval.
* exp_neg_bounds() exp(-x) for x >= 0, by range reduction + Taylor with the
                   alternating-series remainder bound.
* agm_bounds(a,b)  certified AGM; the limit lies between the last b and the
                   last a, so the enclosure is rigorous.
* Interval helpers: add, sub, mul, div, scale, from_fraction, to_decimal.
"""

from fractions import Fraction

SCALE = 50
S = 10 ** SCALE


# --------------------------------------------------------------------------
# integer / fixed-point helpers
# --------------------------------------------------------------------------
def _floor_frac(num, den):
    """floor(num/den) for den > 0 (Python's // already floors)."""
    return num // den


def _ceil_frac(num, den):
    """ceil(num/den) for den > 0."""
    return -((-num) // den)


def from_fraction(x):
    """Exact fixed-point interval for a Fraction (point interval)."""
    x = Fraction(x)
    return (_floor_frac(x.numerator * S, x.denominator),
            _ceil_frac(x.numerator * S, x.denominator))


def from_int(n):
    return (n * S, n * S)


def to_decimal(iv, digits=45):
    """Render an interval as a decimal string pair, e.g. ('0.6555...', '0.6555...')."""
    out = []
    for v in (iv[0], iv[1]):
        sign = "-" if v < 0 else ""
        v = abs(v)
        whole, frac = divmod(v, S)
        out.append("%s%d.%0*d" % (sign, whole, digits, frac))
    return tuple(out)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[1], a[1] - b[0])


def neg(a):
    return (-a[1], -a[0])


def mul(a, b):
    """Interval product with directed rounding; handles signs."""
    (a1, a2), (b1, b2) = a, b
    vals = [a1 * b1, a1 * b2, a2 * b1, a2 * b2]
    lo = min(_floor_frac(v, S) for v in vals)
    hi = max(_ceil_frac(v, S) for v in vals)
    return (lo, hi)


def scale(a, k):
    """Multiply by an exact integer k.

    A fixed-point integer v represents the value v/S, so multiplying the value
    by an integer k gives the fixed-point integer v*k -- there is NO division
    by S here (that would be a bug: it rescales the value by 1/S)."""
    if k >= 0:
        return (a[0] * k, a[1] * k)
    return (a[1] * k, a[0] * k)


def div(a, b):
    """Interval quotient a/b, requires b strictly positive."""
    assert b[0] > 0, "div requires a positive denominator"
    # b holds b_val*S.  The reciprocal of b_val is in [S/b1, S/b0]; stored in
    # fixed point that is [S*S/b1, S*S/b0].  The LOWER bound must be floored
    # and the UPPER bound ceiled -- the other way round would make the
    # enclosure exclude the true value (and can even invert it).
    r_lo = _floor_frac(S * S, b[1])
    r_hi = _ceil_frac(S * S, b[0])
    assert r_lo <= r_hi, "reciprocal interval inverted: %r %r" % (r_lo, r_hi)
    return mul(a, (r_lo, r_hi))


# --------------------------------------------------------------------------
# pi
# --------------------------------------------------------------------------
def _arctan_bounds(q, terms):
    """Interval for arctan(1/q) via the alternating series
         arctan(1/q) = sum_{k>=0} (-1)^k / ((2k+1) q^(2k+1)).
    The remainder after `terms` terms is bounded by the first omitted term
    (alternating series test)."""
    total = Fraction(0)
    qpow = Fraction(1, q)
    sign = 1
    for k in range(terms):
        total += sign * qpow / (2 * k + 1)
        qpow /= q * q
        sign = -sign
    rem = qpow / (2 * terms + 1)
    return (from_fraction(total - rem), from_fraction(total + rem))


def pi_bounds():
    """Interval for pi, via Machin: pi/4 = 4*arctan(1/5) - arctan(1/239)."""
    a_lo, a_hi = _arctan_bounds(5, 45)
    b_lo, b_hi = _arctan_bounds(239, 14)
    # pi = 16*arctan(1/5) - 4*arctan(1/239)
    return (sub(scale(a_lo, 16), scale(b_hi, 4))[0],
            sub(scale(a_hi, 16), scale(b_lo, 4))[1])


PI = pi_bounds()


# --------------------------------------------------------------------------
# square root
# --------------------------------------------------------------------------
def sqrt_bounds(a):
    """Certified sqrt of a fixed-point interval a (a must be >= 0)."""
    assert a[0] >= 0
    # sqrt(v/S) * S = sqrt(v*S)
    lo = _isqrt(a[0] * S)
    hi = _isqrt(a[1] * S)
    if _isqrt(a[1] * S) ** 2 < a[1] * S:
        hi += 1
    return (lo, hi)


def _isqrt(n):
    """Exact floor(sqrt(n)) for n >= 0, integer arithmetic only."""
    if n < 0:
        raise ValueError("isqrt of negative")
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) // 2)
    while True:
        y = (x + n // x) // 2
        if y >= x:
            return x
        x = y


# --------------------------------------------------------------------------
# exp(-x)
# --------------------------------------------------------------------------
def _exp_small(u_lo, u_hi, k=64):
    """Interval for exp(-u) with 0 <= u_lo <= u_hi <= S/2.

    Taylor: exp(-u) = sum_{i>=0} (-u)^i / i!.  For u <= 1/2 the terms
    alternate with decreasing magnitude, so the truncation error is bounded by
    the first omitted term."""
    assert 0 <= u_lo <= u_hi
    term = (S, S)        # i = 0
    total = (S, S)
    last_mag = S
    for i in range(1, k + 1):
        t = mul(term, (-u_hi, -u_lo))
        t = (_floor_frac(t[0], i), _ceil_frac(t[1], i))
        term = t
        total = add(total, term)
        last_mag = max(abs(term[0]), abs(term[1]))
        if last_mag == 0:
            break
    # first omitted term magnitude <= last_mag * u_hi / (S*(k+1))
    rem = (last_mag * u_hi) // (S * (k + 1)) + 2
    return (total[0] - rem, total[1] + rem)


def exp_neg_bounds(x_lo, x_hi, k=64):
    """Interval for exp(-x) given x in [x_lo/S, x_hi/S], x >= 0.

    exp is decreasing, so exp(-x_hi) <= exp(-x) <= exp(-x_lo).
    Range reduction: exp(-x) = exp(-x/2^j) ** (2^j) with x/2^j <= 1/2."""
    assert 0 <= x_lo <= x_hi

    def exp_point(x):
        yl = yh = x
        j = 0
        while yh > S // 2:
            # LOWER bound must stay <= true x/2 (floor); UPPER bound must stay
            # >= true x/2 (ceil).  Using ceil for the lower bound would push it
            # ABOVE the true value and silently invalidate the enclosure.
            yl = yl // 2
            yh = (yh + 1) // 2
            j += 1
        e = _exp_small(yl, yh, k)
        for _ in range(j):
            e = mul(e, e)
        return e

    lower = exp_point(x_hi)   # exp(-x_hi) <= exp(-x)
    upper = exp_point(x_lo)   # exp(-x) <= exp(-x_lo)
    return (lower[0], upper[1])


# --------------------------------------------------------------------------
# AGM
# --------------------------------------------------------------------------
def agm_bounds(a, b, iterations=12):
    """Certified enclosure of AGM(a, b) for positive a, b.

    The exact AGM iteration a' = (a+b)/2, b' = sqrt(a*b) satisfies
    b_n <= AGM <= a_n for every n, so the returned interval
    [b_N.lower, a_N.upper] rigorously contains the limit."""
    assert a[0] > 0 and b[0] > 0
    for _ in range(iterations):
        a_new = (_floor_frac(a[0] + b[0], 2), _ceil_frac(a[1] + b[1], 2))
        b_new = sqrt_bounds(mul(a, b))
        a, b = a_new, b_new
    return (b[0], a[1])


def mul_rat(a, num, den):
    """Interval times an exact rational num/den, with directed rounding.

    The rational is applied directly (not rounded to fixed point first), so
    no precision is lost to the representation of the rational itself."""
    assert den > 0
    lo = _floor_frac(num * a[0], den)
    hi = _ceil_frac(num * a[1], den)
    return (lo, hi)


def mul_rat_iv(a, num, den):
    """Interval times rational num/den where num/den may be negative."""
    if den < 0:
        num, den = -num, -den
    if num >= 0:
        return (mul_rat(a, num, den))
    # negative rational: interval flips
    lo = _floor_frac(num * a[1], den)
    hi = _ceil_frac(num * a[0], den)
    return (lo, hi)
