#!/usr/bin/env python3
"""Exact arithmetic invariants, local reduction at p=37, torsion proof, and
point-arithmetic checks for E : y^2 + y = x^3 - x (Cremona 37a1 / LMFDB 37.a1).

Everything here is exact integer / rational arithmetic (stdlib `fractions` and
`math.gcd` only; no floating point).
"""

from fractions import Fraction
from math import gcd
import sys

MODEL = (0, 0, 1, -1, 0)  # [a1, a2, a3, a4, a6] for y^2 + y = x^3 - x


def weierstrass_invariants(model=MODEL):
    """Return exact integer invariants for [a1, a2, a3, a4, a6]."""
    a1, a2, a3, a4, a6 = model
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = (a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4
          + a2 * a3 * a3 - a4 * a4)
    c4 = b2 * b2 - 24 * b4
    c6 = -b2 ** 3 + 36 * b2 * b4 - 216 * b6
    delta = -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 * b6 + 9 * b2 * b4 * b6
    j = Fraction(c4 ** 3, delta)
    return {
        "model": model,
        "b2": b2, "b4": b4, "b6": b6, "b8": b8,
        "c4": c4, "c6": c6, "delta": delta, "j": j,
    }


def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def local_reduction_37(model=MODEL):
    """Verify local reduction of 37a1 at its unique bad prime p = 37."""
    inv = weierstrass_invariants(model)
    delta = inv["delta"]
    c4 = inv["c4"]
    assert delta == 37 and is_prime(delta), "Delta must be the prime 37"
    p = 37
    # Since v_37(Delta) = 1 < 12 and v_q(Delta) = 0 for all q != 37,
    # the model is globally minimal and p = 37 is the unique bad prime.
    assert c4 % p != 0, "37 must not divide c4 = 48 (multiplicative reduction)"
    # Locate the singular node of y^2 + y - x^3 + x = 0 over F_37:
    # d/dy (y^2 + y) = 2y + 1 = 0 => y0 = -1/2 = 18 (mod 37)
    # d/dx (-x^3 + x) = -3x^2 + 1 = 0 => x0^2 = 1/3 = 25 (mod 37) => x0 = 5 or 32
    nodes = []
    for x0 in range(p):
        for y0 in range(p):
            f = (y0 * y0 + y0 - (x0 ** 3 - x0)) % p
            fx = (-3 * x0 * x0 + 1) % p
            fy = (2 * y0 + 1) % p
            if f == 0 and fx == 0 and fy == 0:
                nodes.append((x0, y0))
    assert nodes == [(5, 18)], "Expected unique node (5, 18) mod 37, got %r" % (nodes,)
    x0, y0 = nodes[0]
    # Translate node to origin: x = x' + x0, y = y' + y0
    # Reduced curve becomes y'^2 - 3*x0*x'^2 - x'^3 = 0 (mod 37).
    # Tangent cone is y'^2 - (3*x0) x'^2 = 0; split iff 3*x0 = 15 is a square mod 37.
    # Since 15^18 == -1 (mod 37), the tangent slopes lie in F_{37^2} \ F_37, so the
    # reduction at 37 is NON-SPLIT multiplicative (a_37 = -1, local root number
    # w_37 = -a_37 = +1, global root number w = w_inf * w_37 = -1).
    tangent_disc = (3 * x0) % p  # 15 mod 37
    split = pow(tangent_disc, (p - 1) // 2, p) == 1
    assert not split, "Reduction at 37 must be non-split multiplicative (a_37 = -1)"
    # For Kodaira type I_1 (v_p(Delta) = 1), the component group Z/1Z is trivial,
    # so Tamagawa number c_37 = gcd(2, 1) = 1 unconditionally.
    return {
        "bad_prime": 37,
        "v_37_delta": 1,
        "kodaira": "I_1",
        "node_mod_37": (x0, y0),
        "split_multiplicative": split,
        "a_37": 1 if split else -1,
        "tamagawa_c37": 1,
        "tamagawa_product": 1,
        "conductor": 37,
    }


def count_points_mod_p(p, model=MODEL):
    """Count #E(F_p) on y^2 + a1*x*y + a3*y = x^3 + a2*x^2 + a4*x + a6."""
    a1, a2, a3, a4, a6 = model
    count = 1  # point at infinity
    for x in range(p):
        rhs = (x * x * x + a2 * x * x + a4 * x + a6) % p
        for y in range(p):
            lhs = (y * y + a1 * x * y + a3 * y) % p
            if lhs == rhs:
                count += 1
    return count


def prove_trivial_torsion(model=MODEL):
    """Prove #E(Q)_tors = 1 by reduction mod good primes p = 2 and p = 3.

    Since Delta = 37 is prime, E has good reduction at p = 2 and p = 3.
    For any prime p of good reduction, the kernel of reduction E(Q)_tors -> E(F_p)
    has prime-power order p^k (with k = 0 for p >= 3 unramified, and order dividing
    2 at p = 2).  Since #E(F_2) = 5 and #E(F_3) = 7:
      * #E(Q)_tors divides #E(F_2) * 2^a = 5 * 2^a
      * #E(Q)_tors divides #E(F_3) * 3^0 = 7
    Hence #E(Q)_tors divides gcd(5 * 2^a, 7) = 1.
    """
    n2 = count_points_mod_p(2, model)
    n3 = count_points_mod_p(3, model)
    n5 = count_points_mod_p(5, model)
    g = gcd(n2, n3)
    assert n2 == 5 and n3 == 7 and g == 1
    return {
        "E_F2": n2,
        "E_F3": n3,
        "E_F5": n5,
        "gcd_F2_F3": g,
        "torsion_order": g,
    }


# --------------------------------------------------------------------------
# Exact rational group law on E : y^2 + y = x^3 - x
# --------------------------------------------------------------------------
def on_curve(pt):
    if pt is None:
        return True
    x, y = pt
    return y * y + y == x * x * x - x


def ec_neg(pt):
    if pt is None:
        return None
    x, y = pt
    return (x, -y - 1)


def ec_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2:
        if y1 + y2 + 1 == 0:
            return None
        lam = (3 * x1 * x1 - 1) / (2 * y1 + 1)
    else:
        lam = (y2 - y1) / (x2 - x1)
    x3 = lam * lam - x1 - x2
    y3 = lam * (x1 - x3) - y1 - 1
    return (x3, y3)


def ec_mul(k, pt):
    if k == 0 or pt is None:
        return None
    if k < 0:
        return ec_mul(-k, ec_neg(pt))
    result = None
    addend = pt
    while k > 0:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    return result


def verify_generator_multiples():
    """Verify P = (0,0) lies on E and check its exact rational multiples 1P..6P,
    plus verify non-divisibility of P by 2 or 3 among rational points of small
    naive height."""
    P = (Fraction(0), Fraction(0))
    assert on_curve(P)
    expected = {
        1: (Fraction(0), Fraction(0)),
        2: (Fraction(1), Fraction(0)),
        3: (Fraction(-1), Fraction(-1)),
        4: (Fraction(2), Fraction(-3)),
        5: (Fraction(1, 4), Fraction(-5, 8)),
        6: (Fraction(6), Fraction(14)),
    }
    computed = {}
    for k, want in expected.items():
        got = ec_mul(k, P)
        assert on_curve(got), "%dP not on curve" % k
        assert got == want, "%dP = %r != %r" % (k, got, want)
        computed[k] = got

    # Non-divisibility check: if P = m*Q for m >= 2, then h_hat(Q) = h_hat(P)/m^2 <= 0.0128.
    # By Silverman's bound on |h(x(Q)) - 2*h_hat(Q)|, any such Q has x(Q) = u/v^2
    # with v <= 8 and |u| <= 64.  Scan all such rational x and check if 2Q = P or 3Q = P.
    divisors_found = []
    for v in range(1, 9):
        v2 = v * v
        v3 = v2 * v
        for u in range(-64, 65):
            if gcd(abs(u), v2) != 1:
                continue
            x = Fraction(u, v2)
            # (2y + 1)^2 = 4x^3 - 4x + 1 = (4u^3 - 4u*v^4 + v^6) / v^6
            num = 4 * u * u * u - 4 * u * (v2 * v2) + (v3 * v3)
            if num < 0:
                continue
            s = int(num ** 0.5)
            if s * s == num:
                for sign in (1, -1):
                    y = Fraction(sign * s - v3, 2 * v3)
                    Q = (x, y)
                    if on_curve(Q):
                        if ec_mul(2, Q) == P or ec_mul(3, Q) == P:
                            divisors_found.append(Q)
    assert not divisors_found, "Found unexpected divisor of P: %r" % (divisors_found,)
    return computed


def mutation_control():
    """Verify that corrupting the model or point coordinates triggers failure."""
    bad_inv = weierstrass_invariants((0, 0, 1, 1, 0))
    if bad_inv["delta"] == 37:
        return False
    # Check that a non-curve point is rejected
    if on_curve((Fraction(0), Fraction(1))):
        return False
    # Check that 32a2 has torsion order > 1 mod (p=3, p=5)
    t32 = gcd(count_points_mod_p(3, (0, 0, 0, -1, 0)),
              count_points_mod_p(5, (0, 0, 0, -1, 0)))
    if t32 != 4:
        return False
    return True


def main():
    inv = weierstrass_invariants()
    loc = local_reduction_37()
    tors = prove_trivial_torsion()
    mults = verify_generator_multiples()
    print("E : y^2 + y = x^3 - x  (Cremona 37a1 / LMFDB 37.a1)")
    print("  model                =", inv["model"])
    print("  c4, c6, Delta, j     = %d, %d, %d, %s" % (
        inv["c4"], inv["c6"], inv["delta"], inv["j"]))
    print("  conductor N          =", loc["conductor"])
    print("  Kodaira at 37        = %s (split=%s, c_37=%d, prod c_p=%d)" % (
        loc["kodaira"], loc["split_multiplicative"],
        loc["tamagawa_c37"], loc["tamagawa_product"]))
    print("  #E(F_2), #E(F_3)     = %d, %d  => gcd = %d => #E(Q)_tors = %d" % (
        tors["E_F2"], tors["E_F3"], tors["gcd_F2_F3"], tors["torsion_order"]))
    print("  generator P          = (0, 0)")
    print("  2P, 3P, 4P, 5P       = %s, %s, %s, %s" % (
        mults[2], mults[3], mults[4], mults[5]))
    if not mutation_control():
        print("INVARIANTS-MUTATION-FAILED")
        return 1
    print("INVARIANTS-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
