#!/usr/bin/env python3
"""Exact rational torsion subgroup prover for elliptic curves over Q.

Uses the strong Lutz-Nagell theorem on minimal Weierstrass models:
every non-zero torsion point P = (x, y) in E(Q)_tors has W = 2*y + a1*x + a3
satisfying either W = 0 (2-torsion) or W in Z_{>0} with W^2 | 16*|Delta|,
and T = 12*x + b2 in Z satisfying the depressed integer cubic:
    T^3 - 3*c4*T - (2*c6 + 432*W^2) = 0.
Solved in exact integers via depressed-cubic bisection (src/cert.py), paired with
the reduction-mod-p injection upper bound #E(Q)_tors | gcd_{p not div 2*Delta} #E(F_p).
"""

from fractions import Fraction
import math

from cert import int_roots_depressed_cubic, isqrt
from tate import b_invariants


def square_divisors(n):
    """Return all positive integers d >= 1 such that d^2 | n."""
    n = abs(n)
    res = [1]
    p = 2
    temp = n
    while p * p <= temp:
        if temp % (p * p) == 0:
            pk = p
            mult = []
            while temp % (pk * pk) == 0:
                mult.append(pk)
                pk *= p
            res = [r * m for r in res for m in [1] + mult]
        while temp % p == 0:
            temp //= p
        p += 1 if p == 2 else 2
    return sorted(set(res))


def add_weierstrass(P, Q, a1, a2, a3, a4, a6):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and y1 + y2 + a1 * x1 + a3 == 0:
        return None
    if P == Q:
        lam = (3 * x1 * x1 + 2 * a2 * x1 + a4 - a1 * y1) / (2 * y1 + a1 * x1 + a3)
    else:
        lam = (y2 - y1) / (x2 - x1)
    x3 = lam * lam + a1 * lam - a2 - x1 - x2
    y3 = -lam * (x3 - x1) - y1 - a1 * x3 - a3
    return (x3, y3)


def point_torsion_order(P, a1, a2, a3, a4, a6):
    """Return exact torsion order k in {1..12} of P by Mazur's bound, or 0 if infinite order."""
    cur = P
    for k in range(1, 13):
        if cur is None:
            return k
        if cur[0].denominator > 4:
            return 0
        cur = add_weierstrass(cur, P, a1, a2, a3, a4, a6)
    return 0


def count_fp(a1, a2, a3, a4, a6, p):
    """Count projective points on E(F_p)."""
    cnt = 1
    for x in range(p):
        rhs = (x * x * x + a2 * x * x + a4 * x + a6) % p
        b = (a1 * x + a3) % p
        for y in range(p):
            if (y * y + b * y - rhs) % p == 0:
                cnt += 1
    return cnt


def compute_torsion_group(a1, a2, a3, a4, a6):
    """Compute exact torsion subgroup E(Q)_tors and reduction-mod-p upper bound.
    Returns (torsion_order, points_list, red_gcd_bound)."""
    b2, b4, b6, b8, c4, c6, Delta = b_invariants(a1, a2, a3, a4, a6)
    pts = {None}
    W_cands = [0] + square_divisors(16 * Delta)
    for W in W_cands:
        K = 2 * c6 + 432 * W * W
        for T in int_roots_depressed_cubic(c4, K):
            x = Fraction(T - b2, 12)
            for sgn in (-1, 1):
                y = (Fraction(sgn * W, 1) - a1 * x - a3) / 2
                if y.denominator == 1 or (W == 0 and y.denominator in (1, 2, 4, 8)):
                    if y * y + a1 * x * y + a3 * y == x * x * x + a2 * x * x + a4 * x + a6:
                        if point_torsion_order((x, y), a1, a2, a3, a4, a6) > 0:
                            pts.add((x, y))

    # Verify group closure
    pts_list = list(pts)
    for P in pts_list:
        for Q in pts_list:
            R = add_weierstrass(P, Q, a1, a2, a3, a4, a6)
            assert R in pts, "Torsion set failed group closure"

    # Compute reduction-mod-p gcd bound over first 8 good odd primes
    red_gcd = 0
    good_checked = 0
    p = 3
    while good_checked < 8:
        if all(p % d != 0 for d in range(2, isqrt(p) + 1)):
            if Delta % p != 0:
                np_val = count_fp(a1, a2, a3, a4, a6, p)
                red_gcd = np_val if red_gcd == 0 else math.gcd(red_gcd, np_val)
                good_checked += 1
        p += 2

    tors_order = len(pts)
    assert red_gcd % tors_order == 0, f"Torsion order {tors_order} does not divide reduction gcd {red_gcd}"
    return tors_order, pts_list, red_gcd
