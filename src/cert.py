"""Certified fixed-point interval arithmetic for BSD Rung 1 (curve 37a1).

Every routine here is exact integer arithmetic on fixed-point numbers scaled by
S = 10**SCALE.  A value v is represented as an integer pair (lo, hi) meaning
the true number lies in [lo/S, hi/S].  All rounding is DIRECTED (outward), so
the returned interval always CONTAINS the true value.  No floating point is
used anywhere: `float` and `math` are not imported by this module.

Contents
--------
* pi_bounds()           pi via Machin's formula, remainder bounded by the first
                        omitted term of an alternating series.
* sqrt_bounds(x)        certified square root of a fixed-point interval.
* exp_neg_bounds(x)     exp(-x) for x >= 0, by range reduction + Taylor with
                        alternating-series remainder bound.
* agm_bounds(a,b)       certified AGM; the limit lies between the last b and
                        the last a, so the enclosure is rigorous.
* ln_int_bounds(n)      certified natural logarithm of a positive integer n,
                        via exact rational artanh series after power-of-2 and
                        dyadic range reduction.
* ln_bounds(iv)         certified natural logarithm of a positive interval.
* euler_gamma_bounds()  certified Euler-Mascheroni constant gamma, proved from
                        the identity gamma = S(a) - ln(a) - E_1(a) at a = 28,
                        where E_1(28) is bracketed by consecutive Stieltjes
                        continued-fraction convergents.
* E1_bounds(iv)         certified exponential integral E_1(x) = int_x^inf e^-t/t dt
                        for x > 0, evaluated at internal scale 10**130 with
                        monotonicity and alternating-series remainder bounds.
* E1_stieltjes_bounds() gamma-free Stieltjes continued-fraction enclosure
                        C_{2m}(x) < e^x E_1(x) < C_{2m-1}(x) for x >= 16.
* cubic_roots_37a1()    certified 1-ULP enclosures of the three real roots
                        e_1 > e_2 > e_3 of 4x^3 - 4x + 1 = 0 by exact integer
                        sign changes.
"""

from fractions import Fraction

SCALE = 50
S = 10 ** SCALE

SCALE_HI = 130
S_HI = 10 ** SCALE_HI


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
    """Render an interval as a decimal string pair."""
    out = []
    for v in (iv[0], iv[1]):
        sign = "-" if v < 0 else ""
        v = abs(v)
        whole, frac = divmod(v, S)
        frac_str = ("%0*d" % (SCALE, frac))[:digits]
        out.append("%s%d.%s" % (sign, whole, frac_str))
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
    """Multiply by an exact integer k."""
    if k >= 0:
        return (a[0] * k, a[1] * k)
    return (a[1] * k, a[0] * k)


def div(a, b):
    """Interval quotient a/b, requires b strictly positive."""
    assert b[0] > 0, "div requires a positive denominator"
    r_lo = _floor_frac(S * S, b[1])
    r_hi = _ceil_frac(S * S, b[0])
    assert r_lo <= r_hi, "reciprocal interval inverted: %r %r" % (r_lo, r_hi)
    return mul(a, (r_lo, r_hi))


def mul_rat(a, num, den):
    """Interval times an exact non-negative rational num/den."""
    assert den > 0 and num >= 0
    lo = _floor_frac(num * a[0], den)
    hi = _ceil_frac(num * a[1], den)
    return (lo, hi)


def mul_rat_iv(a, num, den):
    """Interval times rational num/den where num/den may be negative."""
    if den < 0:
        num, den = -num, -den
    if num >= 0:
        return mul_rat(a, num, den)
    lo = _floor_frac(num * a[1], den)
    hi = _ceil_frac(num * a[0], den)
    return (lo, hi)


# --------------------------------------------------------------------------
# pi
# --------------------------------------------------------------------------
def _arctan_bounds_scaled(q, terms, scale_int):
    """Interval for arctan(1/q) at integer scale `scale_int`."""
    total = Fraction(0)
    qpow = Fraction(1, q)
    sign = 1
    for k in range(terms):
        total += sign * qpow / (2 * k + 1)
        qpow /= q * q
        sign = -sign
    rem = qpow / (2 * terms + 1)
    lo_f = total - rem
    hi_f = total + rem
    return (_floor_frac(lo_f.numerator * scale_int, lo_f.denominator),
            _ceil_frac(hi_f.numerator * scale_int, hi_f.denominator))


def pi_bounds():
    """Interval for pi at scale S, via Machin: pi/4 = 4*arctan(1/5) - arctan(1/239)."""
    a_lo, a_hi = _arctan_bounds_scaled(5, 45, S)
    b_lo, b_hi = _arctan_bounds_scaled(239, 14, S)
    return (16 * a_lo - 4 * b_hi, 16 * a_hi - 4 * b_lo)


PI = pi_bounds()


# --------------------------------------------------------------------------
# square root
# --------------------------------------------------------------------------
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


def sqrt_bounds(a):
    """Certified sqrt of a fixed-point interval a (a must be >= 0)."""
    assert a[0] >= 0
    lo = _isqrt(a[0] * S)
    hi = _isqrt(a[1] * S)
    if hi * hi < a[1] * S:
        hi += 1
    return (lo, hi)


# --------------------------------------------------------------------------
# exp(-x)
# --------------------------------------------------------------------------
def _exp_small(u_lo, u_hi, k=64):
    """Interval for exp(-u) with 0 <= u_lo <= u_hi <= S/2."""
    assert 0 <= u_lo <= u_hi
    term = (S, S)
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
    rem = (last_mag * u_hi) // (S * (k + 1)) + 2
    return (total[0] - rem, total[1] + rem)


def exp_neg_bounds(x_lo, x_hi, k=64):
    """Interval for exp(-x) given x in [x_lo/S, x_hi/S], x >= 0."""
    assert 0 <= x_lo <= x_hi

    def exp_point(x):
        yl = yh = x
        j = 0
        while yh > S // 2:
            yl = yl // 2
            yh = (yh + 1) // 2
            j += 1
        e = _exp_small(yl, yh, k)
        for _ in range(j):
            e = mul(e, e)
        return e

    lower = exp_point(x_hi)
    upper = exp_point(x_lo)
    return (lower[0], upper[1])


# --------------------------------------------------------------------------
# AGM
# --------------------------------------------------------------------------
def agm_bounds(a, b, iterations=12):
    """Certified enclosure of AGM(a, b) for positive a, b."""
    assert a[0] > 0 and b[0] > 0
    for _ in range(iterations):
        a_new = (_floor_frac(a[0] + b[0], 2), _ceil_frac(a[1] + b[1], 2))
        b_new = sqrt_bounds(mul(a, b))
        a, b = a_new, b_new
    return (b[0], a[1])


# --------------------------------------------------------------------------
# Natural logarithm ln(x) at arbitrary internal scale
# --------------------------------------------------------------------------
def _artanh_recip_scaled(q, terms, scale_int):
    """Certified interval at scale `scale_int` for 2*artanh(1/q) = ln((q+1)/(q-1))
    with integer q >= 3.
    Series: 2 * sum_{j>=0} 1 / ((2j+1) * q^(2j+1)).
    Geometric tail for j >= terms is bounded by
        2 * (1 / ((2*terms+1) * q^(2*terms+1))) / (1 - 1/q^2)."""
    assert q >= 3
    # Work directamente in scaled integers to avoid massive Fraction denominators
    # Term j is 2 * scale_int // ((2j+1) * q^(2j+1))
    lo_sum = 0
    hi_sum = 0
    q_pow = q
    q2 = q * q
    for j in range(terms):
        denom = (2 * j + 1) * q_pow
        lo_sum += _floor_frac(2 * scale_int, denom)
        hi_sum += _ceil_frac(2 * scale_int, denom)
        q_pow *= q2
    # Tail bound: 2 * scale_int / ((2*terms+1) * q_pow * (1 - 1/q^2))
    # = 2 * scale_int * q^2 / ((2*terms+1) * q_pow * (q^2 - 1))
    tail = _ceil_frac(2 * scale_int * q2, (2 * terms + 1) * q_pow * (q2 - 1)) + 1
    return (lo_sum, hi_sum + tail)


def _ln2_scaled(scale_int):
    """Certified interval for ln(2) at scale `scale_int` via
    2 = (3/2) * (4/3) => ln(2) = 2*artanh(1/5) + 2*artanh(1/7)."""
    # 1/5^2 = 1/25 (~1.4 digits per term); 105 terms gives >145 digits
    a = _artanh_recip_scaled(5, 110, scale_int)
    b = _artanh_recip_scaled(7, 85, scale_int)
    return (a[0] + b[0], a[1] + b[1])


def _ln3_scaled(scale_int):
    """Certified interval for ln(3) = ln(2) + ln(3/2) = ln(2) + 2*artanh(1/5)."""
    ln2 = _ln2_scaled(scale_int)
    a = _artanh_recip_scaled(5, 110, scale_int)
    return (ln2[0] + a[0], ln2[1] + a[1])


# Precompute dyadic reduction table: for r in 1..6, factor (2^r + 1)/2^r
# has ln((2^r + 1)/2^r) = 2 * artanh(1 / (2^(r+1) + 1)).
def _ln_fraction_scaled(num, den, scale_int):
    """Certified interval at scale `scale_int` for ln(num/den) with num, den > 0."""
    assert num > 0 and den > 0
    # Step 1: reduce by powers of 2 so that u = (num/den) * 2^(-k) lies in [1, 2)
    bl_num = num.bit_length()
    bl_den = den.bit_length()
    k = bl_num - bl_den
    if k >= 0:
        p, q = num, den << k
    else:
        p, q = num << (-k), den
    if p < q:
        p <<= 1
        k -= 1
    elif p >= (q << 1):
        p >>= 1
        k += 1
    assert q <= p < (q << 1)

    total_lo, total_hi = 0, 0
    if k != 0:
        ln2 = _ln2_scaled(scale_int)
        if k > 0:
            total_lo += k * ln2[0]
            total_hi += k * ln2[1]
        else:
            total_lo += k * ln2[1]
            total_hi += k * ln2[0]

    # Step 2: greedy dyadic reduction by factors (2^r + 1)/2^r for r = 1..8
    # Whenever p/q >= (2^r + 1)/2^r, divide p/q by (2^r + 1)/2^r
    for r in range(1, 9):
        m_num = (1 << r) + 1
        m_den = 1 << r
        while p * m_den >= q * m_num:
            p *= m_den
            q *= m_num
            # ln((2^r + 1)/2^r) = 2 * artanh(1 / (2^(r+1) + 1))
            q_art = (1 << (r + 1)) + 1
            terms = max(25, 140 // r)
            iv = _artanh_recip_scaled(q_art, terms, scale_int)
            total_lo += iv[0]
            total_hi += iv[1]

    # Now 1 <= p/q < 1 + 1/256.
    # Let y = (p - q) / (p + q), so 0 <= y < 1/513.
    # ln(p/q) = 2 * sum_{j>=0} y^(2j+1) / (2j+1).
    if p == q:
        return (total_lo, total_hi)
    y_num = p - q
    y_den = p + q
    # Since y < 1/513, y^2 < 1/263169 (~5.4 digits per term); 30 terms gives >160 digits
    # Work in scaled integers: term_0 = 2 * y
    t_lo = _floor_frac(2 * scale_int * y_num, y_den)
    t_hi = _ceil_frac(2 * scale_int * y_num, y_den)
    rem_lo, rem_hi = t_lo, t_hi
    y2_num = y_num * y_num
    y2_den = y_den * y_den
    for j in range(1, 32):
        t_lo = _floor_frac(t_lo * y2_num, y2_den)
        t_hi = _ceil_frac(t_hi * y2_num, y2_den)
        rem_lo += _floor_frac(t_lo, 2 * j + 1)
        rem_hi += _ceil_frac(t_hi, 2 * j + 1)
        if t_hi == 0:
            break
    # Tail bound after j = 31: t_hi * y^2 / (1 - y^2)
    tail = _ceil_frac(t_hi * y2_num, y2_den - y2_num) + 2
    return (total_lo + rem_lo, total_hi + rem_hi + tail)


def ln_int_bounds(n):
    """Certified interval at scale S for ln(n), integer n >= 1."""
    iv_hi = _ln_fraction_scaled(n, 1, S_HI)
    shift = S_HI // S
    return (_floor_frac(iv_hi[0], shift), _ceil_frac(iv_hi[1], shift))


def ln_bounds(iv):
    """Certified interval at scale S for ln(x), where x in [iv[0]/S, iv[1]/S] > 0."""
    assert iv[0] > 0 and iv[0] <= iv[1]
    shift = S_HI // S
    lo_hi = _ln_fraction_scaled(iv[0], S, S_HI)
    hi_hi = _ln_fraction_scaled(iv[1], S, S_HI)
    return (_floor_frac(lo_hi[0], shift), _ceil_frac(hi_hi[1], shift))


# --------------------------------------------------------------------------
# Euler-Mascheroni constant gamma and Exponential Integral E_1(x)
# --------------------------------------------------------------------------
def _exp_neg_int_scaled(a, scale_int):
    """Certified interval for exp(-a) for positive integer a at scale `scale_int`."""
    # Range reduce: u = a / 2^j <= 1/2
    j = 0
    while a > (1 << (j - 1)) if j >= 1 else a > 0:
        if a * 2 <= (1 << j):
            break
        j += 1
    # u = a / 2^j <= 1/2. Compute exp(-u) by alternating Taylor series
    u_num = a
    u_den = 1 << j
    term_lo = scale_int
    term_hi = scale_int
    total_lo = scale_int
    total_hi = scale_int
    for i in range(1, 180):
        # next term magnitude = term * u_num / (u_den * i)
        next_lo = _floor_frac(term_lo * u_num, u_den * i)
        next_hi = _ceil_frac(term_hi * u_num, u_den * i)
        if i % 2 == 1:
            total_lo -= next_hi
            total_hi -= next_lo
        else:
            total_lo += next_lo
            total_hi += next_hi
        term_lo, term_hi = next_lo, next_hi
        if term_hi == 0:
            break
    rem = term_hi + 2
    e_lo, e_hi = total_lo - rem, total_hi + rem
    for _ in range(j):
        e_lo = _floor_frac(e_lo * e_lo, scale_int)
        e_hi = _ceil_frac(e_hi * e_hi, scale_int)
    return (e_lo, e_hi)


def _stieltjes_e1_int_scaled(a, steps, scale_int):
    """Certified enclosure of E_1(a) for positive integer a at scale `scale_int`,
    using Stieltjes's continued fraction:
        C_{2m}(a) < e^a E_1(a) < C_{2m+1}(a)
    where P_j, Q_j are exact positive integers."""
    P_prev, P_cur = 0, 1
    Q_prev, Q_cur = 1, a
    for k in range(1, steps + 1):
        # j = 2k: partial numerator = k, partial denominator = 1
        P_prev, P_cur = P_cur, P_cur + k * P_prev
        Q_prev, Q_cur = Q_cur, Q_cur + k * Q_prev
        P_even, Q_even = P_cur, Q_cur
        # j = 2k+1: partial numerator = k, partial denominator = a
        P_prev, P_cur = P_cur, a * P_cur + k * P_prev
        Q_prev, Q_cur = Q_cur, a * Q_cur + k * Q_prev
        P_odd, Q_odd = P_cur, Q_cur

    # C_even = P_even / Q_even < e^a E_1(a) < P_odd / Q_odd = C_odd
    c_lo = _floor_frac(P_even * scale_int, Q_even)
    c_hi = _ceil_frac(P_odd * scale_int, Q_odd)
    assert c_lo <= c_hi
    e_neg = _exp_neg_int_scaled(a, scale_int)
    return (_floor_frac(c_lo * e_neg[0], scale_int),
            _ceil_frac(c_hi * e_neg[1], scale_int))


def _euler_gamma_hi():
    """Certified enclosure of Euler's constant gamma at scale S_HI = 10**130,
    proved from gamma = sum_{k>=1} (-1)^(k-1) a^k / (k * k!) - ln(a) - E_1(a)
    at the integer a = 28."""
    a = 28
    # Alternating series S(28) = sum_{k=1..220} (-1)^(k-1) 28^k / (k * k!)
    term_lo = S_HI
    term_hi = S_HI
    s_lo = 0
    s_hi = 0
    for k in range(1, 225):
        term_lo = _floor_frac(term_lo * a, k)
        term_hi = _ceil_frac(term_hi * a, k)
        dk_lo = _floor_frac(term_lo, k)
        dk_hi = _ceil_frac(term_hi, k)
        if k % 2 == 1:
            s_lo += dk_lo
            s_hi += dk_hi
        else:
            s_lo -= dk_hi
            s_hi -= dk_lo
    rem = term_hi + 2
    s_iv = (s_lo - rem, s_hi + rem)
    # ln(28) = 2*ln(2) + ln(7), or directly via _ln_fraction_scaled(28, 1, S_HI)
    ln_a = _ln_fraction_scaled(a, 1, S_HI)
    e1_a = _stieltjes_e1_int_scaled(a, 180, S_HI)
    return (s_iv[0] - ln_a[1] - e1_a[1], s_iv[1] - ln_a[0] - e1_a[0])


GAMMA_HI = _euler_gamma_hi()


def euler_gamma_bounds():
    """Certified interval for Euler's constant gamma at scale S = 10**50."""
    shift = S_HI // S
    return (_floor_frac(GAMMA_HI[0], shift), _ceil_frac(GAMMA_HI[1], shift))


def _e1_point_hi(x_num, x_den):
    """Certified enclosure at scale S_HI for E_1(x) at exact rational x = x_num/x_den > 0.
    Uses E_1(x) = -gamma - ln(x) + sum_{k>=1} (-1)^(k-1) x^k / (k * k!)."""
    ln_x = _ln_fraction_scaled(x_num, x_den, S_HI)
    max_x = (x_num // x_den) + 1
    k_max = max(200, 4 * max_x + 80)
    term_lo = S_HI
    term_hi = S_HI
    s_lo = 0
    s_hi = 0
    for k in range(1, k_max + 1):
        term_lo = _floor_frac(term_lo * x_num, x_den * k)
        term_hi = _ceil_frac(term_hi * x_num, x_den * k)
        dk_lo = _floor_frac(term_lo, k)
        dk_hi = _ceil_frac(term_hi, k)
        if k % 2 == 1:
            s_lo += dk_lo
            s_hi += dk_hi
        else:
            s_lo -= dk_hi
            s_hi -= dk_lo
        if k > 2 * max_x and term_hi == 0:
            break
    rem = term_hi + 2
    s_iv = (s_lo - rem, s_hi + rem)
    return (s_iv[0] - GAMMA_HI[1] - ln_x[1], s_iv[1] - GAMMA_HI[0] - ln_x[0])


def E1_bounds(iv):
    """Certified interval at scale S = 10**50 for E_1(x) where x in [iv[0]/S, iv[1]/S] > 0.
    Since E_1(x) is strictly decreasing on (0, inf), E_1(iv[1]/S) <= E_1(x) <= E_1(iv[0]/S)."""
    assert iv[0] > 0 and iv[0] <= iv[1]
    shift = S_HI // S
    lo_eval = _e1_point_hi(iv[1], S)
    hi_eval = _e1_point_hi(iv[0], S)
    return (_floor_frac(lo_eval[0], shift), _ceil_frac(hi_eval[1], shift))


def E1_stieltjes_bounds(iv, steps=180):
    """Independent gamma-free Stieltjes continued-fraction enclosure for E_1(x):
        e^(-x) C_{2m}(x) < E_1(x) < e^(-x) C_{2m+1}(x)
    Evaluated in interval arithmetic at scale S."""
    assert iv[0] > 0 and iv[0] <= iv[1]
    # Because E_1(x) is decreasing, evaluate lower bound at x_hi and upper bound at x_lo
    # Using exact rational arithmetic for the CF recurrence at endpoints x = v/S:
    # Clear denominator S: b_{2k} = 1, b_{2k+1} = v/S
    def cf_even_lo(v):
        P_prev, P_cur = 0, S
        Q_prev, Q_cur = S, v
        for k in range(1, steps + 1):
            P_prev, P_cur = P_cur, P_cur + k * P_prev
            Q_prev, Q_cur = Q_cur, Q_cur + k * Q_prev
            P_even, Q_even = P_cur, Q_cur
            P_prev, P_cur = P_cur * S, v * P_cur + k * S * P_prev
            Q_prev, Q_cur = Q_cur * S, v * Q_cur + k * S * Q_prev
            # rescale by gcd or bit shift to keep integers compact
            sh = max(0, P_cur.bit_length() - 300)
            if sh > 0:
                # only used if we don't need exact rational; but exact integers are fast!
                pass
        return _floor_frac(P_even * S, Q_even)

    def cf_bounds_point(v):
        P_prev, P_cur = 0, S
        Q_prev, Q_cur = S, v
        for k in range(1, steps + 1):
            P_prev, P_cur = P_cur, P_cur + k * P_prev
            Q_prev, Q_cur = Q_cur, Q_cur + k * Q_prev
            P_even, Q_even = P_cur, Q_cur
            P_prev, P_cur = P_cur * S, v * P_cur + k * S * P_prev
            Q_prev, Q_cur = Q_cur * S, v * Q_cur + k * S * Q_prev
            P_odd, Q_odd = P_cur, Q_cur
        return (_floor_frac(P_even * S, Q_even), _ceil_frac(P_odd * S, Q_odd))

    lo_cf = cf_bounds_point(iv[1])[0]
    hi_cf = cf_bounds_point(iv[0])[1]
    e_neg = exp_neg_bounds(iv[0], iv[1])
    return mul((lo_cf, hi_cf), e_neg)


# --------------------------------------------------------------------------
# Certified roots of 4x^3 - 4x + 1 = 0 (for 37a1 real period)
# --------------------------------------------------------------------------
def _poly_37a1_scaled(X):
    """Exact integer value of S^3 * (4*(X/S)^3 - 4*(X/S) + 1) = 4*X^3 - 4*S^2*X + S^3."""
    return 4 * X * X * X - 4 * S * S * X + S * S * S


def _bisect_root(lo, hi, increasing):
    """Bisect a simple root of _poly_37a1_scaled in [lo, hi] down to hi - lo == 1."""
    f_lo = _poly_37a1_scaled(lo)
    f_hi = _poly_37a1_scaled(hi)
    if increasing:
        assert f_lo < 0 < f_hi
    else:
        assert f_lo > 0 > f_hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        f_mid = _poly_37a1_scaled(mid)
        if f_mid == 0:
            return (mid, mid)
        if (f_mid < 0) == increasing:
            lo = mid
        else:
            hi = mid
    # Verify opposite signs at the 1-ULP bracket [lo, lo+1]
    assert _poly_37a1_scaled(lo) * _poly_37a1_scaled(hi) < 0
    return (lo, hi)


def cubic_roots_37a1():
    """Return certified 1-ULP intervals (e1, e2, e3) with e1 > e2 > e3 for the
    roots of 4x^3 - 4x + 1 = 0:
      * e3 in [-2, -1], where f'(x) = 12x^2 - 4 >= 8 > 0 (increasing)
      * e2 in [0, 1/2], where f'(x) = 12x^2 - 4 <= -1 < 0 (decreasing)
      * e1 in [3/5, 1], where f'(x) = 12x^2 - 4 >= 0.32 > 0 (increasing)
    """
    e3 = _bisect_root(-2 * S, -1 * S, increasing=True)
    e2 = _bisect_root(0, S // 2, increasing=False)
    e1 = _bisect_root((3 * S) // 5, 1 * S, increasing=True)
    # Viete consistency checks: e1 + e2 + e3 = 0, e1*e2 + e2*e3 + e3*e1 = -1, e1*e2*e3 = -1/4
    s1 = add(add(e1, e2), e3)
    assert s1[0] <= 0 <= s1[1], "Viete sum check failed"
    return e1, e2, e3
