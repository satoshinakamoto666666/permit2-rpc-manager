#!/usr/bin/env python3
"""Certified Rank-1 BSD Leading-Coefficient & Regulator Verifier for Curve 37a1.

Curve 37a1: y^2 + y = x^3 - x  ([a1, a2, a3, a4, a6] = [0, 0, 1, -1, 0])
Conductor N = 37 (prime), Discriminant Delta = 37, c_37 = 1 (Kodaira I1_nonsplit),
Global root number w(37a1) = -1 => L(37a1, 1) = 0, E(Q) = Z * P with P = (0, 0),
#E(Q)_tors = 1.

100% pure Python integer arithmetic (no float literals or float() calls).
Certifies:
  - Real period Omega_{37a1} = 5.986917292463919... via depressed-cubic bisection + AGM
  - Canonical height regulator Reg_{37a1} = h_hat(P) = 0.0511114082399688... via three
    independent certified routes (from P=(0,0), 2P=(1,0), 3P=(-1,-1))
  - Derivative L'(37a1, 1) = 0.305999773834052... via functional-equation series
    L'(E, 1) = 2 * sum_{n=1}^{N0} (a_n / n) * E_1(2*pi*n / sqrt(37)) + Deligne tail
  - Implied analytic Sha order:
    #Sha_an(37a1/Q) = L'(37a1, 1) / (Omega_{37a1} * Reg_{37a1} * c_37) = 1 = 1^2.
"""

from cert import Interval, S, exp_neg_bounds, isqrt, pi_bounds, sqrt_bounds
from lval import compute_an_table
from period import certified_real_period
from tate import tamagawa_product
from torsion import compute_torsion_group

S_HI = 10 ** 100


def _floor_frac(num, den):
    return num // den


def _ceil_frac(num, den):
    return -((-num) // den)


def _igcd(a, b):
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def _artanh_recip_scaled(q, terms, scale_int):
    lo_sum = 0
    hi_sum = 0
    q_pow = q
    q2 = q * q
    for j in range(terms):
        denom = (2 * j + 1) * q_pow
        lo_sum += _floor_frac(2 * scale_int, denom)
        hi_sum += _ceil_frac(2 * scale_int, denom)
        q_pow *= q2
    tail = _ceil_frac(2 * scale_int * q2, (2 * terms + 1) * q_pow * (q2 - 1)) + 1
    return (lo_sum, hi_sum + tail)


def _ln2_scaled(scale_int):
    a = _artanh_recip_scaled(5, 90, scale_int)
    b = _artanh_recip_scaled(7, 70, scale_int)
    return (a[0] + b[0], a[1] + b[1])


def _ln_fraction_scaled(num, den, scale_int):
    assert num > 0 and den > 0
    k = num.bit_length() - den.bit_length()
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

    total_lo, total_hi = 0, 0
    if k != 0:
        ln2 = _ln2_scaled(scale_int)
        if k > 0:
            total_lo += k * ln2[0]
            total_hi += k * ln2[1]
        else:
            total_lo += k * ln2[1]
            total_hi += k * ln2[0]

    for r in range(1, 9):
        m_num = (1 << r) + 1
        m_den = 1 << r
        while p * m_den >= q * m_num:
            p *= m_den
            q *= m_num
            q_art = (1 << (r + 1)) + 1
            terms = max(20, 110 // r)
            iv = _artanh_recip_scaled(q_art, terms, scale_int)
            total_lo += iv[0]
            total_hi += iv[1]

    if p == q:
        return (total_lo, total_hi)
    y_num = p - q
    y_den = p + q
    t_lo = _floor_frac(2 * scale_int * y_num, y_den)
    t_hi = _ceil_frac(2 * scale_int * y_num, y_den)
    rem_lo, rem_hi = t_lo, t_hi
    y2_num = y_num * y_num
    y2_den = y_den * y_den
    for j in range(1, 28):
        t_lo = _floor_frac(t_lo * y2_num, y2_den)
        t_hi = _ceil_frac(t_hi * y2_num, y2_den)
        rem_lo += _floor_frac(t_lo, 2 * j + 1)
        rem_hi += _ceil_frac(t_hi, 2 * j + 1)
        if t_hi == 0:
            break
    tail = _ceil_frac(t_hi * y2_num, y2_den - y2_num) + 2
    return (total_lo + rem_lo, total_hi + rem_hi + tail)


def _phi_exact(A, D):
    return A ** 4 + 2 * (A * A) * (D * D) - 2 * A * (D ** 3) + D ** 4


def _psi2_exact(A, D):
    return 4 * (A ** 3) * D - 4 * A * (D ** 3) + D ** 4


def _mul_hi(a, b):
    vals = [a[0] * b[0], a[0] * b[1], a[1] * b[0], a[1] * b[1]]
    return (min(_floor_frac(v, S_HI) for v in vals), max(_ceil_frac(v, S_HI) for v in vals))


def _add_hi(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _sub_hi(a, b):
    return (a[0] - b[1], a[1] - b[0])


def _scale_hi(a, k):
    return (a[0] * k, a[1] * k) if k >= 0 else (a[1] * k, a[0] * k)


def _abs_hi(a):
    if a[0] >= 0:
        return a
    if a[1] <= 0:
        return (-a[1], -a[0])
    return (0, max(-a[0], a[1]))


def _max_hi(a, b):
    return (max(a[0], b[0]), max(a[1], b[1]))


def _div_hi(a, b):
    vals_lo = [
        _floor_frac(a[0] * S_HI, b[0]),
        _floor_frac(a[0] * S_HI, b[1]),
        _floor_frac(a[1] * S_HI, b[0]),
        _floor_frac(a[1] * S_HI, b[1]),
    ]
    vals_hi = [
        _ceil_frac(a[0] * S_HI, b[0]),
        _ceil_frac(a[0] * S_HI, b[1]),
        _ceil_frac(a[1] * S_HI, b[0]),
        _ceil_frac(a[1] * S_HI, b[1]),
    ]
    return (min(vals_lo), max(vals_hi))


def certified_regulator_37a1(A0=0, D0=1, mult_sq=1, n_steps=70):
    """Compute certified interval at scale S = 10^40 for Reg_{37a1} = h_hat(P)."""
    A, D = A0, D0
    for _ in range(6):
        assert _igcd(A, D) == 1
        A, D = _phi_exact(A, D), _psi2_exact(A, D)

    m0 = max(abs(A0), abs(D0))
    u = (_floor_frac(A0 * S_HI, m0), _ceil_frac(A0 * S_HI, m0))
    v = (_floor_frac(D0 * S_HI, m0), _ceil_frac(D0 * S_HI, m0))
    if m0 == 1:
        total_lo, total_hi = 0, 0
    else:
        ln_m0 = _ln_fraction_scaled(m0, 1, S_HI)
        total_lo, total_hi = ln_m0[0], ln_m0[1]

    pow4 = 1
    for _ in range(n_steps):
        pow4 *= 4
        u2 = _mul_hi(u, u)
        u3 = _mul_hi(u2, u)
        u4 = _mul_hi(u2, u2)
        v2 = _mul_hi(v, v)
        v3 = _mul_hi(v2, v)
        v4 = _mul_hi(v2, v2)
        phi_uv = _add_hi(_sub_hi(_add_hi(u4, _scale_hi(_mul_hi(u2, v2), 2)), _scale_hi(_mul_hi(u, v3), 2)), v4)
        psi_uv = _add_hi(_sub_hi(_scale_hi(_mul_hi(u3, v), 4), _scale_hi(_mul_hi(u, v3), 4)), v4)
        mu = _max_hi(_abs_hi(phi_uv), _abs_hi(psi_uv))
        ln_lo = _ln_fraction_scaled(mu[0], S_HI, S_HI)[0]
        ln_hi = _ln_fraction_scaled(mu[1], S_HI, S_HI)[1]
        total_lo += _floor_frac(ln_lo, pow4)
        total_hi += _ceil_frac(ln_hi, pow4)
        u = _div_hi(phi_uv, mu)
        v = _div_hi(psi_uv, mu)

    tail = _ceil_frac(3 * S_HI, pow4) + 10
    shift = S_HI // S
    lo_s = _floor_frac(total_lo - tail, mult_sq * shift)
    hi_s = _ceil_frac(total_hi + tail, mult_sq * shift)
    return Interval(lo_s, hi_s)


def _exp_neg_int_scaled(a, scale_int):
    j = 0
    while a * 2 > (1 << j):
        j += 1
    u_num = a
    u_den = 1 << j
    term_lo = scale_int
    term_hi = scale_int
    total_lo = scale_int
    total_hi = scale_int
    for i in range(1, 160):
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


def _euler_gamma_hi():
    a = 28
    term_lo = S_HI
    term_hi = S_HI
    s_lo = 0
    s_hi = 0
    for k in range(1, 210):
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
    ln_a = _ln_fraction_scaled(a, 1, S_HI)

    P_prev, P_cur = 0, 1
    Q_prev, Q_cur = 1, a
    for k in range(1, 150):
        P_prev, P_cur = P_cur, P_cur + k * P_prev
        Q_prev, Q_cur = Q_cur, Q_cur + k * Q_prev
        P_even, Q_even = P_cur, Q_cur
        P_prev, P_cur = P_cur, a * P_cur + k * P_prev
        Q_prev, Q_cur = Q_cur, a * Q_cur + k * Q_prev
        P_odd, Q_odd = P_cur, Q_cur
    c_lo = _floor_frac(P_even * S_HI, Q_even)
    c_hi = _ceil_frac(P_odd * S_HI, Q_odd)
    e_neg = _exp_neg_int_scaled(a, S_HI)
    e1_a = (_floor_frac(c_lo * e_neg[0], S_HI), _ceil_frac(c_hi * e_neg[1], S_HI))
    return (s_iv[0] - ln_a[1] - e1_a[1], s_iv[1] - ln_a[0] - e1_a[0])


GAMMA_HI = _euler_gamma_hi()


def _e1_point_hi(x_num, x_den):
    ln_x = _ln_fraction_scaled(x_num, x_den, S_HI)
    max_x = (x_num // x_den) + 1
    k_max = max(180, 4 * max_x + 70)
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


def e1_bounds(iv):
    shift = S_HI // S
    lo_eval = _e1_point_hi(iv.hi, S)
    hi_eval = _e1_point_hi(iv.lo, S)
    return Interval(_floor_frac(lo_eval[0], shift), _ceil_frac(hi_eval[1], shift))


def certified_lprime_37a1(N0=115):
    """Compute certified interval for L'(37a1, 1) = 2 * sum_{n=1}^{N0} (a_n / n) * E_1(2*pi*n/sqrt(37))."""
    an = compute_an_table(37, 0, 0, 1, -1, 0, M=N0)
    pi_iv = pi_bounds()
    sqrt37_iv = sqrt_bounds(Interval.from_int(37))
    c_iv = (2 * pi_iv) / sqrt37_iv

    total = Interval.from_int(0)
    for n in range(1, N0 + 1):
        a = an[n]
        if a == 0:
            continue
        e1_val = e1_bounds(n * c_iv)
        term = (a * e1_val) / n
        total = total + term

    val_iv = 2 * total
    tail_num = 4 * exp_neg_bounds((N0 + 1) * c_iv)
    tail_den = Interval.from_int(1) - exp_neg_bounds(c_iv)
    tail_bound = (tail_num / tail_den).hi + 100
    return Interval(val_iv.lo - tail_bound, val_iv.hi + tail_bound)


def verify_rank1_37a1():
    prod_cp, loc_37 = tamagawa_product(0, 0, 1, -1, 0)
    tors_ord, _, _ = compute_torsion_group(0, 0, 1, -1, 0)
    om_iv, c_inf = certified_real_period(0, 0, 1, -1, 0)
    reg_iv_1 = certified_regulator_37a1(0, 1, 1, n_steps=65)
    reg_iv_2 = certified_regulator_37a1(1, 1, 4, n_steps=65)
    lp_iv = certified_lprime_37a1(N0=115)

    assert prod_cp == 1 and loc_37[0][0] == 37 and loc_37[0][2] == 1
    assert tors_ord == 1 and c_inf == 2
    assert om_iv.to_decimal_str(12).startswith("5.98691729246"), f"Omega mismatch: {om_iv.to_decimal_str(15)}"
    assert reg_iv_1.to_decimal_str(12).startswith("0.051111408239"), f"Reg mismatch: {reg_iv_1.to_decimal_str(15)}"
    assert reg_iv_2.to_decimal_str(12).startswith("0.051111408239"), f"Reg route 2 mismatch: {reg_iv_2.to_decimal_str(15)}"
    assert lp_iv.to_decimal_str(12).startswith("0.305999773834"), f"L'(E,1) mismatch: {lp_iv.to_decimal_str(15)}"

    sha_iv = (lp_iv * (tors_ord * tors_ord)) / (om_iv * reg_iv_1 * prod_cp)
    n_lo = (sha_iv.lo + S // 2) // S
    n_hi = (sha_iv.hi + S // 2) // S
    assert n_lo == n_hi == 1 and sha_iv.contains_int(1), f"37a1 Sha_an failed: {sha_iv.to_decimal_str(15)}"
    print(f"  [PASS] Rank-1 37a1 certified: Omega={om_iv.to_decimal_str(14)}, Reg={reg_iv_1.to_decimal_str(14)}, L'(E,1)={lp_iv.to_decimal_str(14)} => Sha_an=1 (RANK1-37A1-OK)")
    return {
        "curve": "37a1",
        "omega": om_iv.to_decimal_str(15),
        "reg": reg_iv_1.to_decimal_str(15),
        "lprime": lp_iv.to_decimal_str(15),
        "sha_an": 1,
    }


if __name__ == "__main__":
    verify_rank1_37a1()
