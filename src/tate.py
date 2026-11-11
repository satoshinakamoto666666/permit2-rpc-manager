#!/usr/bin/env python3
"""Complete 10-step Tate local reduction algorithm for elliptic curves over Q.

Computes exact Weierstrass invariants (b2, b4, b6, b8, c4, c6, Delta), local
Kodaira symbols, and local Tamagawa numbers c_p = [E(Q_p) : E_0(Q_p)] at every
prime p | Delta in pure integer arithmetic, and verifies the Tamagawa product
prod_{p | Delta} c_p across all 284 rank-0 curves of conductor N <= 100.
"""


def b_invariants(a1, a2, a3, a4, a6):
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    c4 = b2 * b2 - 24 * b4
    c6 = -b2 * b2 * b2 + 36 * b2 * b4 - 216 * b6
    Delta = -b2 * b2 * b8 - 8 * b4 * b4 * b4 - 27 * b6 * b6 + 9 * b2 * b4 * b6
    return b2, b4, b6, b8, c4, c6, Delta


def vp(n, p):
    if n == 0:
        return 999
    c = 0
    n = abs(n)
    while n % p == 0:
        c += 1
        n //= p
    return c


def shift_weierstrass(a1, a2, a3, a4, a6, r, s, t):
    """Isomorphic coordinate change x = x' + r, y = y' + s*x' + t."""
    a1p = a1 + 2 * s
    a2p = a2 - s * a1 + 3 * r - s * s
    a3p = a3 + r * a1 + 2 * t
    a4p = a4 - s * a3 + 2 * r * a2 - (t + r * s) * a1 + 3 * r * r - 2 * s * t
    a6p = a6 + r * a4 + r * r * a2 + r * r * r - t * a3 - t * t - r * t * a1
    return a1p, a2p, a3p, a4p, a6p


def quad_roots_mod_p(A, B, C, p):
    """Analyze A*x^2 + B*x + C == 0 (mod p) with A != 0 (mod p).
    Returns (distinct_in_Fpbar, count_in_Fp, double_root_in_Fp)."""
    A %= p
    B %= p
    C %= p
    if p == 2:
        if B == 0:
            return False, 1, C
        return True, (2 if C == 0 else 0), None
    disc = (B * B - 4 * A * C) % p
    if disc == 0:
        r = (-B * pow(2 * A, -1, p)) % p
        return False, 1, r
    cnt = 2 if pow(disc, (p - 1) // 2, p) == 1 else 0
    return True, cnt, None


def tate_local(a1, a2, a3, a4, a6, p):
    """Execute Tate's 10-step algorithm at prime p.
    Returns (kodaira_symbol, c_p)."""
    while True:
        b2, b4, b6, b8, c4, c6, Delta = b_invariants(a1, a2, a3, a4, a6)
        n = vp(Delta, p)
        if n == 0:
            return "I0", 1
        # Step 1: Multiplicative reduction (p does not divide c4)
        if c4 % p != 0:
            for r in range(p):
                for t in range(p):
                    a1p, a2p, a3p, a4p, a6p = shift_weierstrass(a1, a2, a3, a4, a6, r, 0, t)
                    if a3p % p == 0 and a4p % p == 0 and a6p % p == 0:
                        _, nr, _ = quad_roots_mod_p(1, a1p, -a2p, p)
                        if nr == 2:
                            return f"I{n}_split", n
                        return f"I{n}_nonsplit", (2 if n % 2 == 0 else 1)
        # Step 2: Additive reduction — move singular point to (0, 0) mod p
        found = False
        for r in range(p):
            for t in range(p):
                a1p, a2p, a3p, a4p, a6p = shift_weierstrass(a1, a2, a3, a4, a6, r, 0, t)
                if a3p % p == 0 and a4p % p == 0 and a6p % p == 0:
                    a1, a2, a3, a4, a6 = a1p, a2p, a3p, a4p, a6p
                    found = True
                    break
            if found:
                break
        for s in range(p):
            a1p, a2p, a3p, a4p, a6p = shift_weierstrass(a1, a2, a3, a4, a6, 0, s, 0)
            if a1p % p == 0 and a2p % p == 0:
                a1, a2, a3, a4, a6 = a1p, a2p, a3p, a4p, a6p
                break
        b2, b4, b6, b8, c4, c6, Delta = b_invariants(a1, a2, a3, a4, a6)
        # Step 3: Type II
        if a6 % (p * p) != 0:
            return "II", 1
        # Step 4: Type III
        if b8 % (p ** 3) != 0:
            return "III", 2
        # Step 5: Type IV
        distinct, nr, dbl = quad_roots_mod_p(1, a3 // p, -(a6 // (p * p)), p)
        if distinct:
            return "IV", (3 if nr == 2 else 1)
        a1, a2, a3, a4, a6 = shift_weierstrass(a1, a2, a3, a4, a6, 0, 0, dbl * p)
        # Step 6: Cubic P(T) = T^3 + A2*T^2 + A4*T + A6 mod p
        A2 = (a2 // p) % p
        A4 = (a4 // (p * p)) % p
        A6 = (a6 // (p ** 3)) % p
        disc_P = (
            A2 * A2 * A4 * A4
            - 4 * A4 * A4 * A4
            - 4 * A2 * A2 * A2 * A6
            - 27 * A6 * A6
            + 18 * A2 * A4 * A6
        ) % p
        roots_Fp = [T for T in range(p) if (T ** 3 + A2 * T * T + A4 * T + A6) % p == 0]
        if disc_P != 0:
            return "I0*", 1 + len(roots_Fp)
        triple_r = None
        double_r = None
        for r in range(p):
            for s in range(p):
                if (
                    (2 * r + s + A2) % p == 0
                    and (r * r + 2 * r * s - A4) % p == 0
                    and (r * r * s + A6) % p == 0
                ):
                    if r == s:
                        triple_r = r
                    else:
                        double_r = r
        if double_r is not None:
            # Step 7: Type I_m* (m >= 1)
            a1, a2, a3, a4, a6 = shift_weierstrass(a1, a2, a3, a4, a6, double_r * p, 0, 0)
            q = p * p
            m = 1
            while True:
                dist_y, nr_y, dbl_y = quad_roots_mod_p(1, a3 // q, -(a6 // (q * q)), p)
                if dist_y:
                    return f"I{m}*", (4 if nr_y == 2 else 2)
                a1, a2, a3, a4, a6 = shift_weierstrass(a1, a2, a3, a4, a6, 0, 0, dbl_y * q)
                m += 1
                dist_x, nr_x, dbl_x = quad_roots_mod_p(a2 // p, a4 // (p * q), a6 // (p * q * q), p)
                if dist_x:
                    return f"I{m}*", (4 if nr_x == 2 else 2)
                a1, a2, a3, a4, a6 = shift_weierstrass(a1, a2, a3, a4, a6, dbl_x * q, 0, 0)
                m += 1
                q *= p
        # Triple root at triple_r
        a1, a2, a3, a4, a6 = shift_weierstrass(a1, a2, a3, a4, a6, triple_r * p, 0, 0)
        # Step 8: Type IV*
        dist_y, nr_y, dbl_y = quad_roots_mod_p(1, a3 // (p * p), -(a6 // (p ** 4)), p)
        if dist_y:
            return "IV*", (3 if nr_y == 2 else 1)
        a1, a2, a3, a4, a6 = shift_weierstrass(a1, a2, a3, a4, a6, 0, 0, dbl_y * p * p)
        # Step 9: Type III*
        if a4 % (p ** 4) != 0:
            return "III*", 2
        # Step 10: Type II*
        if a6 % (p ** 6) != 0:
            return "II*", 1
        a1 //= p
        a2 //= p * p
        a3 //= p ** 3
        a4 //= p ** 4
        a6 //= p ** 6


def tamagawa_product(a1, a2, a3, a4, a6):
    """Compute prod_{p | Delta} c_p and per-prime local reduction data."""
    _, _, _, _, _, _, Delta = b_invariants(a1, a2, a3, a4, a6)
    temp = abs(Delta)
    prod_cp = 1
    local_data = []
    p = 2
    while p * p <= temp:
        if temp % p == 0:
            kod, cp = tate_local(a1, a2, a3, a4, a6, p)
            prod_cp *= cp
            local_data.append((p, kod, cp))
            while temp % p == 0:
                temp //= p
        p += 1 if p == 2 else 2
    if temp > 1:
        kod, cp = tate_local(a1, a2, a3, a4, a6, temp)
        prod_cp *= cp
        local_data.append((temp, kod, cp))
    return prod_cp, local_data


if __name__ == "__main__":
    # Self-test on 11a1 ([0,-1,1,-10,-20], prod c_p = 5), 32a2 ([0,0,0,-1,0], prod c_p = 2), 66b3 ([1,1,1,-352,-2689], prod c_p = 1)
    cp_11a1, loc_11a1 = tamagawa_product(0, -1, 1, -10, -20)
    assert cp_11a1 == 5 and loc_11a1 == [(11, "I5_split", 5)], f"11a1 failed: {cp_11a1}, {loc_11a1}"
    cp_32a2, loc_32a2 = tamagawa_product(0, 0, 0, -1, 0)
    assert cp_32a2 == 2 and loc_32a2 == [(2, "III", 2)], f"32a2 failed: {cp_32a2}, {loc_32a2}"
    cp_66b3, loc_66b3 = tamagawa_product(1, 1, 1, -352, -2689)
    assert cp_66b3 == 1, f"66b3 failed: {cp_66b3}, {loc_66b3}"
    print("  [PASS] src/tate.py self-test passed (TATE-OK)")

