"""Certified real period Omega_E for E : y^2 + y = x^3 - x (Cremona 37a1),
computed by THREE INDEPENDENT CERTIFIED ROUTES in fixed-point interval
arithmetic (no floating point).

Why Omega_E has a factor of 2 (two real components)
---------------------------------------------------
Completing the square (2y + 1)^2 = 4x^3 - 4x + 1 shows that the real locus
E(R) is fibred over {x in R : 4x^3 - 4x + 1 >= 0}.  Since disc(x^3 - x + 1/4)
= 37/16 > 0, the cubic 4x^3 - 4x + 1 has three distinct real roots
    e_3 < e_2 < e_1
enclosed to 1 ULP (10^-50) in cert.cubic_roots_37a1() by exact integer sign
changes:
    e_3 = -1.1071598716887656...,  e_2 = 0.2695944364054446...,  e_1 = 0.8375654352833210...

Hence E(R) has TWO connected components: the compact oval over [e_3, e_2] and
the identity component over [e_1, +inf).  Each component has period
    Omega_conn = pi / AGM(sqrt(e_1 - e_3), sqrt(e_1 - e_2)) = 2.9934586462319596...,
and the BSD formula uses the integral over the FULL real locus:
    Omega_E = 2 * Omega_conn = 5.98691729246391925966401995890501635559516758274...

Three independent routes
------------------------
* Route 1 (Gauss AGM):
    Omega_E = 2 * pi / AGM(sqrt(e_1 - e_3), sqrt(e_1 - e_2)).
* Route 2 (Gauss hypergeometric series after descending Landen transformations):
    Starting from k_0^2 = (e_2 - e_3)/(e_1 - e_3) and k_0' = sqrt((e_1 - e_2)/(e_1 - e_3)),
    three descending Landen steps k_{j+1} = (1 - k_j')/(1 + k_j') reduce k_3^2 below 10^-11,
    where the hypergeometric series sum_{n>=0} (C(2n,n)/4^n)^2 k_3^(2n) converges to 50 digits
    in 10 terms with an explicit geometric tail bound.
* Route 3 (Jacobi theta / elliptic nome series):
    With q = exp(-pi * K(k') / K(k)), Jacobi's identity K(k) = (pi/2) * theta_3(q)^2
    gives Omega_E = 2 * pi * theta_3(q)^2 / sqrt(e_1 - e_3), where
    theta_3(q) = 1 + 2 * sum_{m>=1} q^(m^2).
"""

import sys

from cert import (
    S, PI, _floor_frac, _ceil_frac, from_int, add, sub, mul, div,
    scale, mul_rat, sqrt_bounds, exp_neg_bounds, agm_bounds,
    cubic_roots_37a1, to_decimal,
)


def omega_route1_agm():
    """Route 1: Omega_E = 2 * pi / AGM(sqrt(e_1 - e_3), sqrt(e_1 - e_2))."""
    e1, e2, e3 = cubic_roots_37a1()
    a0 = sqrt_bounds(sub(e1, e3))
    b0 = sqrt_bounds(sub(e1, e2))
    agm = agm_bounds(a0, b0, iterations=12)
    return div(scale(PI, 2), agm)


def omega_route2_hypergeom():
    """Route 2: Descending Landen reduction + Gauss hypergeometric series."""
    e1, e2, e3 = cubic_roots_37a1()
    d13 = sub(e1, e3)
    d12 = sub(e1, e2)
    d23 = sub(e2, e3)
    sqrt_d13 = sqrt_bounds(d13)
    # Initial complementary modulus kp = sqrt((e1 - e2)/(e1 - e3))
    # Initial modulus squared k2 = (e2 - e3)/(e1 - e3)
    kp = sqrt_bounds(div(d12, d13))
    k = sqrt_bounds(div(d23, d13))
    one = from_int(1)
    # Apply 3 descending Landen steps:
    # K(k) = (2 / (1 + kp)) * K(k_next), where k_next = (1 - kp)/(1 + kp)
    # Equivalently k_next = k^2 / (1 + kp)^2 (avoids subtraction cancellation).
    scale_factor = one
    for _ in range(3):
        one_plus_kp = add(one, kp)
        scale_factor = div(scale(scale_factor, 2), one_plus_kp)
        k_next = div(mul(k, k), mul(one_plus_kp, one_plus_kp))
        kp = div( mul(from_int(2), sqrt_bounds(kp)), one_plus_kp )
        k = k_next

    # Evaluate Gauss hypergeometric series sum_{n=0..N} (C(2n,n)/4^n)^2 * k^(2n)
    k2 = mul(k, k)
    total = one
    k2_pow = one
    coeff_num = 1
    coeff_den = 1
    N = 12
    for n in range(1, N + 1):
        k2_pow = mul(k2_pow, k2)
        coeff_num *= (2 * n - 1) ** 2
        coeff_den *= (2 * n) ** 2
        term = mul_rat(k2_pow, coeff_num, coeff_den)
        total = add(total, term)

    # Geometric tail bound: next term <= k2_pow * k2 / (1 - k2)
    next_k2 = mul(k2_pow, k2)
    tail = div(next_k2, sub(one, k2))[1] + 2
    series_iv = (total[0], total[1] + tail)

    # K(k_0) = scale_factor * (pi / 2) * series_iv
    # Omega_E = 4 * K(k_0) / sqrt(e1 - e3) = 2 * pi * scale_factor * series_iv / sqrt(e1 - e3)
    num = mul(mul(scale(PI, 2), scale_factor), series_iv)
    return div(num, sqrt_d13)


def omega_route3_theta():
    """Route 3: Jacobi theta series Omega_E = 2 * pi * theta_3(q)^2 / sqrt(e_1 - e_3)
    where q = exp(-pi * K(k') / K(k)) = exp(-pi * AGM(1, k') / AGM(1, k))."""
    e1, e2, e3 = cubic_roots_37a1()
    d13 = sub(e1, e3)
    d12 = sub(e1, e2)
    d23 = sub(e2, e3)
    sqrt_d13 = sqrt_bounds(d13)
    k = sqrt_bounds(div(d23, d13))
    kp = sqrt_bounds(div(d12, d13))
    one = from_int(1)
    # K(k) = pi / (2 * AGM(1, k')) and K(k') = pi / (2 * AGM(1, k)),
    # so K(k') / K(k) = AGM(1, k') / AGM(1, k).
    ratio = div(agm_bounds(one, kp, 12), agm_bounds(one, k, 12))
    pi_ratio = mul(PI, ratio)

    # theta_3(q) = 1 + 2 * sum_{m=1..M} q^(m^2)
    # Here K(k')/K(k) ~ 0.55052, so pi * ratio ~ 1.72951, q ~ 0.17737.
    # At M = 10, q^(121) < 10^-90.
    M = 10
    theta = one
    for m in range(1, M + 1):
        exp_m = scale(pi_ratio, m * m)
        qm2 = exp_neg_bounds(exp_m[0], exp_m[1])
        theta = add(theta, scale(qm2, 2))
    # Tail bound for m >= M+1: 2 * q^((M+1)^2) / (1 - q^(2M+3))
    exp_tail = scale(pi_ratio, (M + 1) ** 2)
    q_tail = exp_neg_bounds(exp_tail[0], exp_tail[1])
    tail = scale(q_tail, 4)[1] + 2
    theta_iv = (theta[0], theta[1] + tail)
    theta_sq = mul(theta_iv, theta_iv)
    return div(mul(scale(PI, 2), theta_sq), sqrt_d13)


def omega_certified():
    """Run all three routes, assert overlap, and return the intersection."""
    r1 = omega_route1_agm()
    r2 = omega_route2_hypergeom()
    r3 = omega_route3_theta()
    lo = max(r1[0], r2[0], r3[0])
    hi = min(r1[1], r2[1], r3[1])
    if lo > hi:
        raise AssertionError(
            "Certified period routes do not overlap: %r vs %r vs %r" % (r1, r2, r3))
    return (lo, hi), r1, r2, r3


def mutation_control():
    """Verify that omitting the 2-component factor (using Omega_conn = Omega_E / 2)
    produces an interval disjoint from Omega_E."""
    iv, r1, _, _ = omega_certified()
    half_r1 = (_floor_frac(r1[0], 2), _ceil_frac(r1[1], 2))
    if max(iv[0], half_r1[0]) <= min(iv[1], half_r1[1]):
        return False
    return True


def main():
    iv, r1, r2, r3 = omega_certified()
    print("Real period Omega_E for E : y^2 + y = x^3 - x (Cremona 37a1)")
    print("  route 1 (AGM)            :", to_decimal(r1, 45)[0])
    print("  route 2 (hypergeometric) :", to_decimal(r2, 45)[0])
    print("  route 3 (theta series)   :", to_decimal(r3, 45)[0])
    print("  routes agree             :", True)
    print("  certified interval       :", to_decimal(iv, 45)[0])
    print("                            ", to_decimal(iv, 45)[1])
    print("  certified interval width : %.3e" % ((iv[1] - iv[0]) / S))
    if not mutation_control():
        print("PERIOD-MUTATION-FAILED")
        return 1
    print("PERIOD-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
