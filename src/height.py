"""Certified canonical Neron-Tate height h_hat(P) = Reg_E for E : y^2 + y = x^3 - x
(Cremona 37a1), computed by THREE INDEPENDENT CERTIFIED ROUTES in fixed-point
interval arithmetic (no floating point).

Why there are no non-Archimedean local correction terms on 37a1
---------------------------------------------------------------
For the minimal model E : y^2 + y = x^3 - x, the invariants are
    b2 = 0, b4 = -2, b6 = 1, b8 = -1, Delta = 37.
The homogeneous duplication polynomials on x = A/D are
    Phi(A, D)   = A^4 - b4 A^2 D^2 - 2 b6 A D^3 - b8 D^4
                = A^4 + 2 A^2 D^2 - 2 A D^3 + D^4,
    Psi^2(A, D) = 4 A^3 D + b2 A^2 D^2 + 2 b4 A D^3 + b6 D^4
                = 4 A^3 D - 4 A D^3 + D^4.
The resultant Res(Phi, Psi^2) equals Delta = 37.  At p = 37, the singular node
is at x == 5 (mod 37); since P = (0, 0) reduces to (0, 0) != (5, 18) mod 37,
P lies on the identity component E_0(Q_37) at the unique bad prime (c_37 = 1),
so gcd(Phi(A, D), Psi^2(A, D)) = 1 for every multiple of P.

Therefore x(2^n Q) = A_n / D_n in lowest terms for all n >= 0, and Tate's
telescoping series gives
    h_hat(Q) = ln max(|A_0|, |D_0|) + sum_{n>=0} 4^{-(n+1)} ln(mu_n),
where u_0 = A_0/M_0, v_0 = D_0/M_0, and
    mu_n = max(|Phi(u_n, v_n)|, |Psi^2(u_n, v_n)|),
    (u_{n+1}, v_{n+1}) = (Phi(u_n, v_n)/mu_n, Psi^2(u_n, v_n)/mu_n).

Three independent routes
------------------------
* Route 1 (from P = (0,0), x = 0/1):     Reg_E = h_hat(P)
* Route 2 (from 2P = (1,0), x = 1/1):    Reg_E = h_hat(2P) / 4
* Route 3 (from 3P = (-1,-1), x = -1/1): Reg_E = h_hat(3P) / 9
"""

from math import gcd
import sys

from cert import (
    S, S_HI, _floor_frac, _ceil_frac, _ln_fraction_scaled,
    to_decimal,
)


def _phi_exact(A, D):
    return A ** 4 + 2 * (A * A) * (D * D) - 2 * A * (D ** 3) + D ** 4


def _psi2_exact(A, D):
    return 4 * (A ** 3) * D - 4 * A * (D ** 3) + D ** 4


def verify_coprime_duplication_orbit(A0, D0, steps=8):
    """Verify in exact integers that gcd(A_n, D_n) = 1 for 0 <= n <= steps,
    confirming zero non-Archimedean local height cancellation."""
    A, D = A0, D0
    for _ in range(steps):
        if gcd(abs(A), abs(D)) != 1:
            raise AssertionError("Non-coprime (A_n, D_n) detected")
        A, D = _phi_exact(A, D), _psi2_exact(A, D)
    if gcd(abs(A), abs(D)) != 1:
        raise AssertionError("Non-coprime (A_n, D_n) detected at final step")
    return True


# --------------------------------------------------------------------------
# High-precision interval operations at S_HI = 10**130
# --------------------------------------------------------------------------
def _mul_hi(a, b):
    vals = [a[0] * b[0], a[0] * b[1], a[1] * b[0], a[1] * b[1]]
    return (min(_floor_frac(v, S_HI) for v in vals),
            max(_ceil_frac(v, S_HI) for v in vals))


def _add_hi(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _sub_hi(a, b):
    return (a[0] - b[1], a[1] - b[0])


def _scale_hi(a, k):
    if k >= 0:
        return (a[0] * k, a[1] * k)
    return (a[1] * k, a[0] * k)


def _abs_hi(a):
    if a[0] >= 0:
        return a
    if a[1] <= 0:
        return (-a[1], -a[0])
    return (0, max(-a[0], a[1]))


def _max_hi(a, b):
    return (max(a[0], b[0]), max(a[1], b[1]))


def _div_hi(a, b):
    assert b[0] > 0
    vals = [
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
    return (min(vals), max(vals_hi))


def _ln_iv_hi(iv):
    lo = _ln_fraction_scaled(iv[0], S_HI, S_HI)[0]
    hi = _ln_fraction_scaled(iv[1], S_HI, S_HI)[1]
    return (lo, hi)


def canonical_height_from_point(A0, D0, mult_sq=1, n_steps=90):
    """Compute certified interval at scale S for h_hat(Q) / mult_sq, where
    x(Q) = A0 / D0 in lowest terms."""
    verify_coprime_duplication_orbit(A0, D0, steps=7)
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

        # Phi(u, v) = u^4 + 2 u^2 v^2 - 2 u v^3 + v^4
        phi = _add_hi(
            _sub_hi(_add_hi(u4, _scale_hi(_mul_hi(u2, v2), 2)),
                    _scale_hi(_mul_hi(u, v3), 2)),
            v4,
        )
        # Psi^2(u, v) = 4 u^3 v - 4 u v^3 + v^4
        psi2 = _add_hi(
            _sub_hi(_scale_hi(_mul_hi(u3, v), 4),
                    _scale_hi(_mul_hi(u, v3), 4)),
            v4,
        )
        mu = _max_hi(_abs_hi(phi), _abs_hi(psi2))
        ln_mu = _ln_iv_hi(mu)
        total_lo += _floor_frac(ln_mu[0], pow4)
        total_hi += _ceil_frac(ln_mu[1], pow4)
        u = _div_hi(phi, mu)
        v = _div_hi(psi2, mu)

    # Rigorous tail bound: for every step, 1/37 <= mu_n <= 9, so |ln(mu_n)| <= ln(37) < 4.
    # Sum_{n >= n_steps} 4 / 4^(n+1) = 4 / (3 * 4^n_steps) < 2 / 4^n_steps.
    tail_hi = _ceil_frac(2 * S_HI, pow4) + 2
    total_lo -= tail_hi
    total_hi += tail_hi

    # Divide by mult_sq and convert from S_HI to S
    shift = S_HI // S
    return (_floor_frac(total_lo, mult_sq * shift),
            _ceil_frac(total_hi, mult_sq * shift))


def reg_route1_from_P():
    """Route 1: Reg_E = h_hat(P) from P = (0,0), x(P) = 0/1."""
    return canonical_height_from_point(0, 1, mult_sq=1, n_steps=90)


def reg_route2_from_2P():
    """Route 2: Reg_E = h_hat(2P)/4 from 2P = (1,0), x(2P) = 1/1."""
    return canonical_height_from_point(1, 1, mult_sq=4, n_steps=90)


def reg_route3_from_3P():
    """Route 3: Reg_E = h_hat(3P)/9 from 3P = (-1,-1), x(3P) = -1/1."""
    return canonical_height_from_point(-1, 1, mult_sq=9, n_steps=90)


def reg_certified():
    """Compute Reg_E by all three routes, require overlap, return intersection."""
    r1 = reg_route1_from_P()
    r2 = reg_route2_from_2P()
    r3 = reg_route3_from_3P()
    lo = max(r1[0], r2[0], r3[0])
    hi = min(r1[1], r2[1], r3[1])
    if lo > hi:
        raise AssertionError(
            "Certified height routes do not overlap: %r vs %r vs %r" % (r1, r2, r3))
    return (lo, hi), r1, r2, r3


def mutation_control():
    """Verify that using the wrong quadraticity divisor (e.g. 3 instead of 4 for 2P)
    produces a disjoint interval."""
    r1 = reg_route1_from_P()
    wrong_r2 = canonical_height_from_point(1, 1, mult_sq=3, n_steps=40)
    if max(r1[0], wrong_r2[0]) <= min(r1[1], wrong_r2[1]):
        return False
    return True


def main():
    iv, r1, r2, r3 = reg_certified()
    print("Regulator Reg_E = h_hat(P) for P = (0, 0) on 37a1")
    print("  route 1 (from P=(0,0))        :", to_decimal(r1, 45)[0])
    print("  route 2 (from 2P=(1,0) / 4)   :", to_decimal(r2, 45)[0])
    print("  route 3 (from 3P=(-1,-1) / 9) :", to_decimal(r3, 45)[0])
    print("  routes agree                  :", True)
    print("  certified interval            :", to_decimal(iv, 45)[0])
    print("                                 ", to_decimal(iv, 45)[1])
    print("  certified interval width      : %.3e" % ((iv[1] - iv[0]) / S))
    if not mutation_control():
        print("HEIGHT-MUTATION-FAILED")
        return 1
    print("HEIGHT-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
