#!/usr/bin/env python3
"""Certified central L-value L(E, 1) for all rank-0 isogeny classes of conductor N <= 100.

For an elliptic curve E/Q of conductor N with global root number w(E) = +1
(Fricke eigenvalue lambda_N = -1), the completed L-function satisfies
Lambda(E, s) = +Lambda(E, 2 - s), yielding the rapidly converging series:
    L(E, 1) = 2 * sum_{n=1}^infty (a_n(E) / n) * exp(-2 * pi * n / sqrt(N)).
All calculations use pure fixed-point integer interval arithmetic (src/cert.py).
"""

from cert import Interval, S, exp_neg_bounds, isqrt, pi_bounds, sqrt_bounds
from tate import b_invariants


def ap_minimal_weierstrass(a1, a2, a3, a4, a6, p):
    """Compute a_p(E) = p + 1 - #E_tilde(F_p) on a minimal Weierstrass model.
    Holds uniformly for good reduction (smooth), multiplicative reduction (nodal:
    #E_tilde(F_p) = p for split, p+2 for non-split), and additive reduction
    (cuspidal: #E_tilde(F_p) = p+1 => a_p = 0)."""
    cnt = 1
    for x in range(p):
        rhs = (x * x * x + a2 * x * x + a4 * x + a6) % p
        b = (a1 * x + a3) % p
        for y in range(p):
            if (y * y + b * y - rhs) % p == 0:
                cnt += 1
    return p + 1 - cnt


def ap_short_legendre(c4, c6, p):
    """Independent computation of a_p(E) at odd prime p via Legendre character sum
    on the short model Y^2 = X^3 - 27*c4*X - 54*c6."""
    A = (-27 * c4) % p
    B = (-54 * c6) % p
    half = (p - 1) // 2
    s = 0
    for X in range(p):
        rhs = (X * X * X + A * X + B) % p
        if rhs != 0:
            leg = pow(rhs, half, p)
            s += 1 if leg == 1 else -1
    return -s


def compute_an_table(N, a1, a2, a3, a4, a6, M=120):
    """Compute Fourier coefficients a_1 .. a_M and cross-check every odd good prime
    between projective Weierstrass counting and short-model Legendre character sum."""
    _, _, _, _, c4, c6, Delta = b_invariants(a1, a2, a3, a4, a6)
    an = [0] * (M + 1)
    an[1] = 1
    primes = [p for p in range(2, M + 1) if all(p % d != 0 for d in range(2, isqrt(p) + 1))]
    for p in primes:
        ap = ap_minimal_weierstrass(a1, a2, a3, a4, a6, p)
        if p >= 5 and Delta % p != 0:
            ap2 = ap_short_legendre(c4, c6, p)
            if ap != ap2:
                raise AssertionError(f"a_p mismatch at p={p}: Weierstrass={ap} vs Legendre={ap2}")
        an[p] = ap
        pk = p * p
        p_prev = p
        while pk <= M:
            an[pk] = ap * an[p_prev] - (0 if N % p == 0 else p) * an[p_prev // p]
            p_prev = pk
            pk *= p
    for m in range(2, M + 1):
        if an[m] == 0 and m not in primes:
            for p in primes:
                if m % p == 0:
                    pk = p
                    while (m // pk) % p == 0:
                        pk *= p
                    if pk < m:
                        an[m] = an[pk] * an[m // pk]
                    break
    return an


def certified_l_at_1(N, a1, a2, a3, a4, a6, N0=115):
    """Compute certified interval for L(E, 1) using N0 terms and rigorous Deligne tail bound.
    For N <= 100 and N0 = 115, 2*pi/sqrt(N) >= 0.6283185, and by Deligne's bound
    |a_n| <= d(n)*sqrt(n) <= 2*n, the tail 2 * sum_{n > N0} (|a_n|/n) e^{-c*n}
    is bounded by 4 * e^{-c*(N0+1)} / (1 - e^{-c}) < 10^{-29}."""
    an = compute_an_table(N, a1, a2, a3, a4, a6, M=N0)
    pi_iv = pi_bounds()
    sqrtN_iv = sqrt_bounds(Interval.from_int(N))
    c_iv = (2 * pi_iv) / sqrtN_iv

    total = Interval.from_int(0)
    for n in range(1, N0 + 1):
        a = an[n]
        if a == 0:
            continue
        term_exp = exp_neg_bounds(n * c_iv)
        term = (a * term_exp) / n
        total = total + term

    val_iv = 2 * total
    # Certified Deligne tail bound: 4 * exp(-c * (N0 + 1)) / (1 - exp(-c))
    tail_num = 4 * exp_neg_bounds((N0 + 1) * c_iv)
    tail_den = Interval.from_int(1) - exp_neg_bounds(c_iv)
    tail_bound = (tail_num / tail_den).hi + 10
    return Interval(val_iv.lo - tail_bound, val_iv.hi + tail_bound), an


if __name__ == "__main__":
    l_32a2, _ = certified_l_at_1(32, 0, 0, 0, -1, 0, N0=115)
    assert l_32a2.to_decimal_str(12).startswith("0.65551438857"), f"32a2 L(E,1) failed: {l_32a2.to_decimal_str(15)}"
    l_66b3, _ = certified_l_at_1(66, 1, 1, 1, -352, -2689, N0=115)
    assert l_66b3.to_decimal_str(12).startswith("1.10219253012"), f"66b3 L(E,1) failed: {l_66b3.to_decimal_str(15)}"
    print("  [PASS] src/lval.py self-test passed (LVAL-OK)")

