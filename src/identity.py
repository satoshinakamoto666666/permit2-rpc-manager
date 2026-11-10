"""The rank-1 BSD leading-coefficient identity for E : y^2 + y = x^3 - x (Cremona 37a1),
assembled in certified fixed-point interval arithmetic.

For a curve E/Q of rank r = 1, the BSD leading-coefficient formula asserts:

    L'(E, 1)  =  Omega_E * Reg_E * (prod_p c_p) * #Sha(E) / (#E(Q)_tors)^2.

For 37a1:
  * #E(Q)_tors = 1          (PROVED in src/invariants.py)
  * prod_p c_p = c_37 = 1   (PROVED in src/invariants.py)
  * Reg_E = h_hat(P)        (COMPUTED in src/height.py, 3 certified routes)
  * Omega_E                 (COMPUTED in src/period.py, 3 certified routes)
  * L'(E, 1)                (COMPUTED in src/lprime.py, certified interval)
  * #Sha(E) = 1             (CITED: Gross-Zagier / Kolyvagin / Cremona ecdata)

We compute the implied Sha order
    R := L'(E, 1) * (#E(Q)_tors)^2 / (Omega_E * Reg_E * prod_p c_p)
as a certified interval and assert that 1 lies inside R with width < 10^-40.

Convention control (two real components):
E(R) has two connected components.  Using the identity-component period
Omega_conn = Omega_E / 2 instead of Omega_E gives R_conn = 2, which would
falsely imply #Sha(E) = 2 (impossible for an alternating bilinear Cassels-Tate
pairing).  This script asserts that Omega_E / 2 gives 2, guarding the period
convention against silent regressions.
"""

import sys

from cert import S, _floor_frac, _ceil_frac, mul, div, scale, to_decimal
from height import reg_certified
from identity_data import (
    CREMONA_LABEL, LMFDB_LABEL, CONDUCTOR, TORS_ORDER,
    TAMAGAWA_PRODUCT, GENERATOR_P, SHA_ORDER_CITED,
)
from invariants import weierstrass_invariants, local_reduction_37, prove_trivial_torsion
from lprime import lprime_certified
from period import omega_certified


def verify_identity():
    inv = weierstrass_invariants()
    loc = local_reduction_37()
    tors = prove_trivial_torsion()
    assert tors["torsion_order"] == TORS_ORDER == 1
    assert loc["tamagawa_product"] == TAMAGAWA_PRODUCT == 1

    omega_iv, _, _, _ = omega_certified()
    reg_iv, _, _, _ = reg_certified()
    lprime_iv, _, _ = lprime_certified(135)

    # Numerator: L'(E, 1) * (#E(Q)_tors)^2
    num_iv = scale(lprime_iv, TORS_ORDER * TORS_ORDER)
    # Denominator: Omega_E * Reg_E * (prod_p c_p)
    den_iv = scale(mul(omega_iv, reg_iv), TAMAGAWA_PRODUCT)
    ratio_iv = div(num_iv, den_iv)

    # Assert 1 is contained in ratio_iv and both endpoints are within 10^-40 of 1
    tol = 10 ** (50 - 40)  # 10^-40 in fixed-point scale S = 10^50
    if not (ratio_iv[0] <= S <= ratio_iv[1]):
        raise AssertionError("Certified BSD ratio interval does not contain 1: %r" % (ratio_iv,))
    if S - ratio_iv[0] > tol or ratio_iv[1] - S > tol:
        raise AssertionError("Certified BSD ratio interval wider than 10^-40: %r" % (ratio_iv,))

    # Convention control: identity-component period Omega_conn = Omega_E / 2 must give 2
    omega_conn = (_floor_frac(omega_iv[0], 2), _ceil_frac(omega_iv[1], 2))
    ratio_conn = div(num_iv, scale(mul(omega_conn, reg_iv), TAMAGAWA_PRODUCT))
    if not (ratio_conn[0] <= 2 * S <= ratio_conn[1]):
        raise AssertionError("Convention control failed: Omega_E/2 did not give 2: %r" % (ratio_conn,))

    return {
        "omega_iv": omega_iv,
        "reg_iv": reg_iv,
        "lprime_iv": lprime_iv,
        "rhs_iv": den_iv,
        "ratio_iv": ratio_iv,
        "ratio_conn_iv": ratio_conn,
        "inv": inv,
    }


def main():
    res = verify_identity()
    print("=" * 72)
    print("BSD RUNG 1 CERTIFICATE: E : y^2 + y = x^3 - x (%s / %s)" % (
        CREMONA_LABEL, LMFDB_LABEL))
    print("=" * 72)
    print("  conductor N                    :", CONDUCTOR)
    print("  generator P of E(Q)            :", GENERATOR_P)
    print("  #E(Q)_tors (PROVED)            :", TORS_ORDER)
    print("  prod_p c_p = c_37 (PROVED)     :", TAMAGAWA_PRODUCT)
    print("  #Sha(E/Q) (CITED)              :", SHA_ORDER_CITED)
    print("  Omega_E (COMPUTED, 3 routes)   :", to_decimal(res["omega_iv"], 45)[0])
    print("                                  ", to_decimal(res["omega_iv"], 45)[1])
    print("  Reg_E = h_hat(P) (3 routes)    :", to_decimal(res["reg_iv"], 45)[0])
    print("                                  ", to_decimal(res["reg_iv"], 45)[1])
    print("  Omega_E * Reg_E                :", to_decimal(res["rhs_iv"], 45)[0])
    print("                                  ", to_decimal(res["rhs_iv"], 45)[1])
    print("  L'(E, 1) (COMPUTED)            :", to_decimal(res["lprime_iv"], 45)[0])
    print("                                  ", to_decimal(res["lprime_iv"], 45)[1])
    print("  implied #Sha = L'/(Omega*Reg)  :", to_decimal(res["ratio_iv"], 45)[0])
    print("                                  ", to_decimal(res["ratio_iv"], 45)[1])
    print("  implied #Sha (integer)         : 1")
    print("  convention control (Omega_E/2) :", to_decimal(res["ratio_conn_iv"], 40)[0], "-> 2 (guarded)")
    print("IDENTITY-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
