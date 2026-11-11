#!/usr/bin/env python3
"""Certified real period Omega_E in pure fixed-point integer interval arithmetic.

Under the linear transformation T = 12*x + b2, the 2-division cubic
4*x^3 + b2*x^2 + 2*b4*x + b6 = 0 becomes the depressed integer cubic:
    P(T) = T^3 - 3*c4*T - 2*c6 = 0.
- If Delta > 0 (c_inf = 2 real components, 3 real roots T1 > T2 > T3):
    Omega_E = (4 * pi * sqrt(3)) / AGM(sqrt(T1 - T3), sqrt(T1 - T2))
- If Delta < 0 (c_inf = 1 real component, 1 real root T1, M_T = sqrt(3*T1^2 - 3*c4)):
    Omega_E = (4 * pi * sqrt(3)) / AGM(2 * sqrt(M_T), sqrt(2*M_T + 3*T1))
"""

from cert import (
    Interval,
    S,
    agm_bounds,
    bisect_depressed_cubic,
    icbrt_ub,
    isqrt,
    pi_bounds,
    sqrt_bounds,
)
from tate import b_invariants


def certified_real_period(a1, a2, a3, a4, a6):
    """Return (omega_interval, c_inf) for minimal Weierstrass curve [a1, a2, a3, a4, a6]."""
    b2, b4, b6, b8, c4, c6, Delta = b_invariants(a1, a2, a3, a4, a6)
    pi_iv = pi_bounds()
    sqrt3_iv = sqrt_bounds(Interval.from_int(3))
    num_iv = 4 * pi_iv * sqrt3_iv

    bound_int = 4 * max(1, isqrt(abs(3 * c4)) + 1, icbrt_ub(abs(2 * c6)))
    bound_s = bound_int * S

    if Delta > 0:
        e_pos_s = isqrt(c4 * S * S)
        T3_iv = bisect_depressed_cubic(c4, c6, -bound_s, -e_pos_s)
        T2_iv = bisect_depressed_cubic(c4, c6, -e_pos_s, e_pos_s)
        T1_iv = bisect_depressed_cubic(c4, c6, e_pos_s, bound_s)
        a_arg = sqrt_bounds(T1_iv - T3_iv)
        b_arg = sqrt_bounds(T1_iv - T2_iv)
        agm_iv = agm_bounds(a_arg, b_arg)
        return num_iv / agm_iv, 2
    else:
        if c4 <= 0:
            T1_iv = bisect_depressed_cubic(c4, c6, -bound_s, bound_s)
        elif c6 > 0:
            e_pos_s = isqrt(c4 * S * S)
            T1_iv = bisect_depressed_cubic(c4, c6, e_pos_s, bound_s)
        else:
            e_pos_s = isqrt(c4 * S * S)
            T1_iv = bisect_depressed_cubic(c4, c6, -bound_s, -e_pos_s)
        # M_T = sqrt(3 * T1^2 - 3 * c4)
        t1_sq = T1_iv * T1_iv
        m_rad = 3 * t1_sq - Interval.from_int(3 * c4)
        M_T_iv = sqrt_bounds(m_rad)
        a_arg = 2 * sqrt_bounds(M_T_iv)
        b_arg = sqrt_bounds(2 * M_T_iv + 3 * T1_iv)
        agm_iv = agm_bounds(a_arg, b_arg)
        return num_iv / agm_iv, 1
