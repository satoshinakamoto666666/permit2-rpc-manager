"""Fourier coefficients a_n of the weight-2 newform of level 37 attached to
E : y^2 + y = x^3 - x (Cremona 37a1 / LMFDB 37.a1), computed by TWO INDEPENDENT
methods in exact integer arithmetic.

Method A -- Minimal Weierstrass projective point counting over F_p:
    Counts solutions (x, y) in F_p^2 to y^2 + y = x^3 - x (mod p), plus the
    point at infinity, and sets a_p = p + 1 - #E(F_p).  Remarkably, at the
    non-split multiplicative prime p = 37 the singular cubic has p + 2 = 39
    projective F_37-points (37 smooth points of the norm-1 torus + 1 node),
    so p + 1 - #E_proj(F_37) = 38 - 39 = -1 gives the exact Euler factor
    a_37 = -1 as well.

Method B -- Legendre character sum on the short model Y^2 = X^3 - 16X + 16:
    For odd primes p, a_p = -sum_{X in F_p} ((X^3 - 16X + 16) / p), where
    (u / p) is the Legendre symbol u^((p-1)/2) mod p in {-1, 0, 1}.
    For p = 2, y^2 + y == 0 and x^3 - x == 0 identically on F_2, so all 4
    affine points of F_2^2 lie on E, giving #E(F_2) = 5 and a_2 = -2.

Hecke recursion then extends a_p to all n >= 1:
    a_{mn} = a_m a_n                      for gcd(m, n) = 1,
    a_{p^{k+1}} = a_p a_{p^k} - p a_{p^{k-1}}  for p != 37,
    a_{37^k} = (-1)^k                     (multiplicative reduction at 37).
"""

import sys


def primes_upto(n):
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
    return [i for i in range(2, n + 1) if sieve[i]]


def a_p_by_weierstrass_counting(p):
    """Method A: direct point counting on y^2 + y = x^3 - x over F_p."""
    total = 1  # point at infinity
    for x in range(p):
        rhs = (x * x * x - x) % p
        for y in range(p):
            if (y * y + y - rhs) % p == 0:
                total += 1
    return p + 1 - total


def a_p_by_legendre_sum(p):
    """Method B: character sum on Y^2 = X^3 - 16X + 16 for odd p, F_2 identity at p=2."""
    if p == 2:
        # On F_2, y(y+1) = 0 and x(x^2-1) = 0 for all x, y in {0, 1}
        affine = sum(1 for x in (0, 1) for y in (0, 1) if (y * y + y) % 2 == (x ** 3 - x) % 2)
        return 2 + 1 - (1 + affine)
    exp = (p - 1) // 2
    s = 0
    for X in range(p):
        u = (X * X * X - 16 * X + 16) % p
        if u == 0:
            continue
        leg = pow(u, exp, p)
        s += 1 if leg == 1 else -1
    return -s


def _hecke_extend(N, ap_dict):
    P = [p for p in sorted(ap_dict) if p <= N]
    out = [0] * (N + 1)
    out[1] = 1
    for n in range(2, N + 1):
        m = n
        result = 1
        for p in P:
            if m % p:
                continue
            k = 0
            while m % p == 0:
                m //= p
                k += 1
            if p == 37:
                cur = (-1) ** k
            else:
                prev, cur = 1, ap_dict[p]
                for _ in range(2, k + 1):
                    prev, cur = cur, ap_dict[p] * cur - p * prev
            result *= cur
            if m == 1:
                break
        assert m == 1, "factorisation incomplete for n=%d" % n
        out[n] = result
    return out


def build_table(N=160):
    """Compute a_1..a_N by Method A and Method B and assert complete agreement."""
    P = primes_upto(N)
    ap_a = {p: a_p_by_weierstrass_counting(p) for p in P}
    ap_b = {p: a_p_by_legendre_sum(p) for p in P}
    table_a = _hecke_extend(N, ap_a)
    table_b = _hecke_extend(N, ap_b)
    mismatches = [n for n in range(1, N + 1) if table_a[n] != table_b[n]]
    if mismatches:
        raise AssertionError("Method A vs Method B mismatch at n=%r" % (mismatches,))
    # Verify known first prime coefficients against Cremona / LMFDB:
    # a_2=-2, a_3=-3, a_5=-2, a_7=-1, a_11=-5, a_13=-2, a_17=0, a_19=0, a_23=2, a_29=6, a_31=-4, a_37=-1
    known = {2: -2, 3: -3, 5: -2, 7: -1, 11: -5, 13: -2, 17: 0, 19: 0, 23: 2, 29: 6, 31: -4, 37: -1}
    for p, want in known.items():
        if p <= N and ap_a[p] != want:
            raise AssertionError("a_%d = %d, expected %d" % (p, ap_a[p], want))
    return table_a, table_b, ap_a


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 160
    ta, tb, ap = build_table(N)
    bad = [n for n in range(1, N + 1) if ta[n] != tb[n]]
    print("a_p (primes <= 37):", {p: ap[p] for p in sorted(ap) if p <= 37})
    print("method A vs method B mismatches:", bad if bad else "NONE")
    print("a_1..a_20:", ta[1:21])
    if bad:
        return 1
    print("AN-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
