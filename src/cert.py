#!/usr/bin/env python3
"""Pure fixed-point integer interval arithmetic for BSD Rank-0 Family (N <= 100).

Every real number x is enclosed by a pair of Python ints (lo, hi) representing
the closed interval [lo / S, hi / S] at scale S = 10^40.
Internal transcendental series run at S_HI = 10^80.

HARD RULE: float, math, decimal, fractions, and external packages are NEVER
imported in this module.
"""

S_EXP = 40
S = 10 ** S_EXP

S_HI_EXP = 80
S_HI = 10 ** S_HI_EXP


def isqrt(n):
    """Exact integer floor(sqrt(n)) for n >= 0 using Newton's method in pure int."""
    if n < 0:
        raise ValueError("isqrt of negative integer")
    if n < 2:
        return n
    shift = (n.bit_length() + 1) >> 1
    x = 1 << shift
    while True:
        y = (x + n // x) >> 1
        if y >= x:
            return x
        x = y


def icbrt_ub(n):
    """Safe integer upper bound on n^(1/3) + 2 for n >= 0 in pure int."""
    if n <= 0:
        return 2
    shift = (n.bit_length() + 2) // 3
    return (1 << shift) + 2


def floor_div(a, b):
    if b <= 0:
        raise ValueError("b must be positive")
    return a // b


def ceil_div(a, b):
    if b <= 0:
        raise ValueError("b must be positive")
    return -((-a) // b)


class Interval:
    """Closed real interval [lo / S, hi / S] with exact Python int endpoints."""

    __slots__ = ("lo", "hi")

    def __init__(self, lo, hi):
        if not isinstance(lo, int) or not isinstance(hi, int):
            raise TypeError("Interval endpoints must be Python ints")
        if lo > hi:
            raise ValueError(f"Inverted interval: lo={lo} > hi={hi}")
        self.lo = lo
        self.hi = hi

    @staticmethod
    def from_int(n):
        v = int(n) * S
        return Interval(v, v)

    @staticmethod
    def from_ratio(num, den):
        if den < 0:
            num, den = -num, -den
        return Interval(floor_div(num * S, den), ceil_div(num * S, den))

    def width_str(self):
        w = self.hi - self.lo
        if w == 0:
            return "0.000e+00"
        s = str(w)
        exp = len(s) - 1 - S_EXP
        mant = s[0] + "." + (s[1:4].ljust(3, "0"))
        sign = "+" if exp >= 0 else "-"
        return f"{mant}e{sign}{abs(exp):02d}"

    def to_decimal_str(self, digits=20):
        mid = (self.lo + self.hi) // 2
        neg = mid < 0
        v = -mid if neg else mid
        int_part = v // S
        frac_part = v % S
        frac_str = str(frac_part).rjust(S_EXP, "0")[:digits]
        prefix = "-" if neg else ""
        return f"{prefix}{int_part}.{frac_str}"

    def contains_int(self, n):
        target = int(n) * S
        return self.lo <= target <= self.hi

    def __add__(self, other):
        if isinstance(other, int):
            other = Interval.from_int(other)
        return Interval(self.lo + other.lo, self.hi + other.hi)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, int):
            other = Interval.from_int(other)
        return Interval(self.lo - other.hi, self.hi - other.lo)

    def __rsub__(self, other):
        if isinstance(other, int):
            other = Interval.from_int(other)
        return other.__sub__(self)

    def __neg__(self):
        return Interval(-self.hi, -self.lo)

    def __mul__(self, other):
        if isinstance(other, int):
            if other >= 0:
                return Interval(self.lo * other, self.hi * other)
            return Interval(self.hi * other, self.lo * other)
        p1 = self.lo * other.lo
        p2 = self.lo * other.hi
        p3 = self.hi * other.lo
        p4 = self.hi * other.hi
        pmin = min(p1, p2, p3, p4)
        pmax = max(p1, p2, p3, p4)
        return Interval(floor_div(pmin, S), ceil_div(pmax, S))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, int):
            if other == 0:
                raise ZeroDivisionError("Interval division by zero")
            if other > 0:
                return Interval(floor_div(self.lo, other), ceil_div(self.hi, other))
            return Interval(floor_div(-self.hi, -other), ceil_div(-self.lo, -other))
        if other.lo <= 0 <= other.hi:
            raise ZeroDivisionError("Interval divisor straddles zero")
        if other.lo > 0:
            q1 = floor_div(self.lo * S, other.hi if self.lo >= 0 else other.lo)
            q2 = ceil_div(self.hi * S, other.lo if self.hi >= 0 else other.hi)
            return Interval(q1, q2)
        return (-self) / (-other)


def sqrt_bounds(iv):
    """Certified interval for sqrt(iv) on iv >= 0."""
    if iv.lo < 0:
        raise ValueError("sqrt_bounds on negative interval")
    lo_sq = isqrt(iv.lo * S)
    hi_arg = iv.hi * S
    hi_sq = isqrt(hi_arg)
    if hi_sq * hi_sq < hi_arg:
        hi_sq += 1
    return Interval(lo_sq, hi_sq)


_PI_CACHE = None


def pi_bounds():
    """Machin's formula pi/4 = 4*arctan(1/5) - arctan(1/239) at internal scale S_HI."""
    global _PI_CACHE
    if _PI_CACHE is not None:
        return _PI_CACHE

    def arctan_inv_hi(m, terms):
        m2 = m * m
        power = S_HI // m
        lo_sum = 0
        hi_sum = 0
        for k in range(terms):
            denom = 2 * k + 1
            if k % 2 == 0:
                lo_sum += power // denom
                hi_sum += (power + denom - 1) // denom + 1
            else:
                lo_sum -= (power + denom - 1) // denom + 1
                hi_sum -= power // denom
            power //= m2
        rem = (power + 1) // (2 * terms + 1) + 2
        return lo_sum - rem, hi_sum + rem

    a5_lo, a5_hi = arctan_inv_hi(5, 70)
    a239_lo, a239_hi = arctan_inv_hi(239, 25)
    pi_hi_lo = 16 * a5_lo - 4 * a239_hi
    pi_hi_hi = 16 * a5_hi - 4 * a239_lo
    scale_diff = S_HI // S
    _PI_CACHE = Interval(floor_div(pi_hi_lo, scale_diff), ceil_div(pi_hi_hi, scale_diff))
    return _PI_CACHE


def exp_neg_bounds(x_iv):
    """Certified interval for exp(-x) for x_iv >= 0 via argument halving at S_HI."""
    if x_iv.lo < 0:
        raise ValueError("exp_neg_bounds requires x >= 0")
    if x_iv.hi == 0:
        return Interval.from_int(1)

    scale_diff = S_HI // S

    def exp_neg_point_hi(x_hi):
        if x_hi == 0:
            return S_HI, S_HI
        halvings = 0
        u = x_hi
        while u > S_HI // 4:
            u = (u + 1) // 2
            halvings += 1
        u_lo = x_hi >> halvings
        u_hi = (x_hi + (1 << halvings) - 1) >> halvings

        def series_small(z_lo, z_hi, N_pairs=30):
            s_lo = S_HI
            s_hi = S_HI
            t_lo = S_HI
            t_hi = S_HI
            for m in range(1, 2 * N_pairs + 1):
                t_lo = (t_lo * z_lo) // (m * S_HI)
                t_hi = ceil_div(t_hi * z_hi, m * S_HI)
                if m % 2 == 1:
                    s_lo -= t_hi
                    s_hi -= t_lo
                else:
                    s_lo += t_lo
                    s_hi += t_hi
            s_lo -= t_hi + 4
            s_hi += 4
            return max(0, s_lo), s_hi

        r_lo, r_hi = series_small(u_lo, u_hi, 30)
        for _ in range(halvings):
            r_lo = (r_lo * r_lo) // S_HI
            r_hi = ceil_div(r_hi * r_hi, S_HI)
        return r_lo, r_hi

    hi_val_lo, _ = exp_neg_point_hi(x_iv.hi * scale_diff)
    _, lo_val_hi = exp_neg_point_hi(x_iv.lo * scale_diff)
    return Interval(floor_div(hi_val_lo, scale_diff), ceil_div(lo_val_hi, scale_diff))


def agm_bounds(a_iv, b_iv):
    """Certified Arithmetic-Geometric Mean AGM(a, b) for a, b > 0."""
    if a_iv.lo <= 0 or b_iv.lo <= 0:
        raise ValueError("AGM requires positive intervals")
    a = Interval(min(a_iv.lo, b_iv.lo), max(a_iv.hi, b_iv.hi))
    b = Interval(min(a_iv.lo, b_iv.lo), max(a_iv.hi, b_iv.hi))
    cur_a = a_iv
    cur_b = b_iv
    for _ in range(30):
        nxt_a = (cur_a + cur_b) / 2
        nxt_b = sqrt_bounds(cur_a * cur_b)
        cur_a, cur_b = nxt_a, nxt_b
    lo = min(cur_a.lo, cur_b.lo)
    hi = max(cur_a.hi, cur_b.hi)
    return Interval(lo, hi)


def bisect_depressed_cubic(c4, c6, lo_s, hi_s):
    """Certified 1-ULP enclosure of a root of P(T) = T^3 - 3*c4*T - 2*c6 = 0
    for scaled integer T_s in [lo_s, hi_s] representing T = T_s / S."""
    c4_S2 = 3 * c4 * S * S
    c6_S3 = 2 * c6 * S * S * S

    def eval_p(Ts):
        return Ts * Ts * Ts - c4_S2 * Ts - c6_S3

    flo = eval_p(lo_s)
    fhi = eval_p(hi_s)
    if flo == 0:
        return Interval(lo_s, lo_s)
    if fhi == 0:
        return Interval(hi_s, hi_s)
    if (flo < 0 and fhi < 0) or (flo > 0 and fhi > 0):
        raise ValueError("No sign change in bisect_depressed_cubic")
    a, b = lo_s, hi_s
    fa = flo
    while b - a > 1:
        mid = (a + b) >> 1
        fm = eval_p(mid)
        if fm == 0:
            return Interval(mid, mid)
        if (fa < 0 and fm < 0) or (fa > 0 and fm > 0):
            a = mid
            fa = fm
        else:
            b = mid
    return Interval(a, b)


def int_roots_depressed_cubic(c4, K):
    """Find all exact integer roots T in Z of T^3 - 3*c4*T - K = 0 via integer bisection."""
    bound = 2 * max(1, isqrt(abs(3 * c4)) + 1, icbrt_ub(abs(K)))

    def bisect_int(lo, hi):
        flo = lo * lo * lo - 3 * c4 * lo - K
        fhi = hi * hi * hi - 3 * c4 * hi - K
        res = []
        if flo == 0:
            res.append(lo)
        if fhi == 0:
            res.append(hi)
        if (flo < 0 and fhi < 0) or (flo > 0 and fhi > 0):
            return res
        a, b = lo, hi
        fa = flo
        while b - a > 1:
            mid = (a + b) >> 1
            fm = mid * mid * mid - 3 * c4 * mid - K
            if fm == 0:
                res.append(mid)
                return res
            if (fa < 0 and fm < 0) or (fa > 0 and fm > 0):
                a = mid
                fa = fm
            else:
                b = mid
        return res

    if c4 <= 0:
        return sorted(set(bisect_int(-bound, bound)))
    e = isqrt(c4)
    out = set()
    for lo, hi in ((-bound, -e), (-e, e), (e, bound)):
        for r in bisect_int(lo, hi):
            out.add(r)
    for r in (-e - 1, -e, -e + 1, e - 1, e, e + 1):
        if r * r * r - 3 * c4 * r - K == 0:
            out.add(r)
    return sorted(out)


def verify_cert_self_test():
    pi = pi_bounds()
    assert pi.to_decimal_str(15).startswith("3.141592653589793"), "pi check failed"
    e1 = exp_neg_bounds(Interval.from_int(1))
    assert e1.to_decimal_str(15).startswith("0.367879441171442"), "exp(-1) check failed"
    print(f"  [PASS] cert.py self-test: S=10^{S_EXP}, pi={pi.to_decimal_str(18)} (width {pi.width_str()})")


if __name__ == "__main__":
    verify_cert_self_test()
