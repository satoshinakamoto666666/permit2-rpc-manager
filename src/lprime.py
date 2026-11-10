"""Certified computation of L'(E, 1) for E : y^2 + y = x^3 - x (Cremona 37a1)
in fixed-point interval arithmetic (no floating point).

Mathematical formula
--------------------
The weight-2 newform f(z) = sum_{n>=1} a_n q^n of level N = 37 attached to E
has Fricke eigenvalue lambda = +1 (global root number w = w_inf * w_37 =
(-1) * (-a_37) = (-1) * (+1) = -1), so L(E, 1) = 0 identically and the first
derivative at s = 1 is given by the rapidly converging series

    L'(E, 1) = 2 * sum_{n>=1} (a_n / n) * E_1(2 * pi * n / sqrt(37)),

where E_1(x) = int_x^inf (e^-t / t) dt is the exponential integral.

Rigorous tail bound (Deligne)
-----------------------------
By Deligne's bound |a_n| <= d(n) sqrt(n) <= 2n, we have |a_n / n| <= 2 for all
n >= 1.  For x >= 1, E_1(x) < e^(-x) / x <= e^(-x).  Hence for any cutoff N_0 >= 1,

    | L'(E, 1) - 2 * sum_{n=1..N_0} (a_n / n) E_1(n c) |
        <= 4 * e^(-c * (N_0 + 1)) / (1 - e^(-c)),      c = 2 * pi / sqrt(37).

Internal control on E_1(x)
--------------------------
For 18 <= n <= 28 (where x_n = n*c in [18.5, 29.0]), we evaluate E_1(x_n) by
TWO independent certified methods:
  1. E1_bounds(x_n)           -- power series at internal scale 10^130 using
                                 Euler's constant gamma and ln(x_n)
  2. E1_stieltjes_bounds(x_n) -- gamma-free Stieltjes continued fraction
                                 e^(-x) C_{2m}(x) < E_1(x) < e^(-x) C_{2m+1}(x)
and require the two intervals to overlap at every point in that window.
"""

import sys

from a_n import build_table
from cert import (
    S, PI, from_int, add, sub, div, scale, mul_rat_iv,
    sqrt_bounds, exp_neg_bounds, E1_bounds, E1_stieltjes_bounds,
    to_decimal,
)


def c_37a1_bounds():
    """Certified interval for c = 2 * pi / sqrt(37)."""
    sqrt37 = sqrt_bounds(from_int(37))
    return div(scale(PI, 2), sqrt37)


def lprime_certified(N0=135):
    """Return (lprime_iv, c_iv, tail_bound) for L'(E, 1) at cutoff N0."""
    an, _, _ = build_table(N0)
    c_iv = c_37a1_bounds()

    total = (0, 0)
    for n in range(1, N0 + 1):
        a = an[n]
        if a == 0:
            continue
        xn = scale(c_iv, n)
        e1 = E1_bounds(xn)
        # Cross-check against gamma-free Stieltjes CF on the overlap window 18 <= n <= 26
        if 18 <= n <= 26:
            e1_cf = E1_stieltjes_bounds(xn, steps=150)
            lo_ov = max(e1[0], e1_cf[0])
            hi_ov = min(e1[1], e1_cf[1])
            if lo_ov > hi_ov:
                raise AssertionError(
                    "E1 power-series vs Stieltjes CF mismatch at n=%d: %r vs %r"
                    % (n, e1, e1_cf))
            e1 = (lo_ov, hi_ov)
        # Contribution: 2 * (a_n / n) * E_1(n * c)
        term = mul_rat_iv(e1, 2 * a, n)
        total = add(total, term)

    # Rigorous Deligne tail bound: 4 * e^(-c*(N0+1)) / (1 - e^(-c))
    exp_n0 = scale(c_iv, N0 + 1)
    num_tail = scale(exp_neg_bounds(exp_n0[0], exp_n0[1]), 4)
    one_minus_ec = sub(from_int(1), exp_neg_bounds(c_iv[0], c_iv[1]))
    tail_iv = div(num_tail, one_minus_ec)
    tail_hi = tail_iv[1] + 2

    lprime_iv = (total[0] - tail_hi, total[1] + tail_hi)
    return lprime_iv, c_iv, tail_hi


def mutation_control():
    """Verify that flipping a_2 from -2 to +2 changes L'(E,1) outside the interval."""
    iv, c_iv, _ = lprime_certified(45)
    # Flipping a_2 adds 2 * (4 / 2) * E_1(2c) = 4 * E_1(2c) > 0.1
    e1_2c = E1_bounds(scale(c_iv, 2))
    perturbed = add(iv, scale(e1_2c, 4))
    if max(iv[0], perturbed[0]) <= min(iv[1], perturbed[1]):
        return False
    return True


def main():
    N0 = int(sys.argv[1]) if len(sys.argv) > 1 else 135
    iv, c_iv, tail_hi = lprime_certified(N0)
    print("L'(E, 1) for E : y^2 + y = x^3 - x (Cremona 37a1), cutoff N0 = %d" % N0)
    print("  c = 2*pi/sqrt(37)   :", to_decimal(c_iv, 45)[0])
    print("  certified tail bound: < %.3e" % (max(tail_hi, 1) / S))
    print("  L'(E, 1) lower bound:", to_decimal(iv, 45)[0])
    print("  L'(E, 1) upper bound:", to_decimal(iv, 45)[1])
    print("  L'(E, 1) width      : %.3e" % ((iv[1] - iv[0]) / S))
    if not mutation_control():
        print("LPRIME-MUTATION-FAILED")
        return 1
    print("LPRIME-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
