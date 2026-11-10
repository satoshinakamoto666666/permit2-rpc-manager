"""The BSD leading-coefficient identity for E : y^2 = x^3 - x, checked numerically.

THE IDENTITY.  For an elliptic curve E/Q of rank 0, the BSD conjecture asserts

    L(E,1) = Omega_E * prod_p c_p * #Sha(E) / #E(Q)_tors^2                (BSD)

where
    Omega_E   = integral over E(R) of |omega|, omega = dx/(2y)  (FULL real
                locus, i.e. BOTH connected components -- see PROOF.md, sec. 1),
    c_p       = the Tamagawa number at p (1 for every good prime),
    #Sha(E)   = the order of the Tate-Shafarevich group,
    #E(Q)_tors= the number of rational torsion points.

Everything in (BSD) except #Sha(E) is determined by data we can compute and
certify:

    #E(Q)_tors = 4   -- PROVED in PROOF.md by Fermat's infinite descent
                        (E(Q) = E[2](Q) = {O,(0,0),(1,0),(-1,0)}), hence
                        rank 0 and torsion (Z/2)^2.
    prod_p c_p = c_2 = 2 -- computed by Tate's algorithm in tate.py
                        (self-contained), cross-checked against PARI/GP.
    Omega_E       -- certified in period.py by THREE independent routes.
    L(E,1)        -- certified in lvalue.py by the Fricke exponential sum,
                        cross-checked against PARI/GP.

So (BSD) for this curve reduces to a single numerical question:

    R := L(E,1) * #tors^2 / (Omega_E * c_2)   =?   #Sha(E).

We compute R as a certified interval and check that it contains 1 to within
the certified error.

WHY THAT IS A MEANINGFUL CHECK.  #Sha(E) is a positive INTEGER.  If the
certified interval for R is contained in (1 - 1e-40, 1 + 1e-40), then the
only integer it can contain is 1.  So the computation does not merely "look
close to 1"; it pins the implied value to exactly 1, provided the other
ingredients are right.  Equivalently: IF #Sha(E) = 1 (a CITED fact, see
PROOF.md section 6), THEN every other ingredient of the identity is
numerically correct to ~45 digits.

This does NOT prove BSD: it verifies one curve's leading coefficient, and
the odd-primary part of Sha is not settled here.  See OPEN_REMAINDER.md.

WHY THE CONVENTION MATTERS.  If one used the period of the IDENTITY
COMPONENT ALONE (half of Omega_E for this curve), then R would come out as 2
instead of 1, i.e. one would "discover" a Sha of order 2 that does not exist.
The convention is stated explicitly above and RE-CHECKED in the code below:
the identity-component variant is computed and asserted to give 2, so a
future edit that changes the period convention cannot pass unnoticed.

MUTATION CONTROL.  After the real computation we deliberately corrupt the
certified interval for L(E,1) and assert that the identity check FAILS.  If
the corruption did not break the check, the check would be a rubber stamp --
so the script would exit non-zero.
"""

import cert
import identity_data as idata
import lvalue
import period

# 1e-40 in fixed-point units at SCALE = 10**50: 1e-40 * 1e50 = 1e10.
TOL_UNITS = 10 ** 10

# Size of the deliberate corruption used by the mutation control, in
# fixed-point units (1e10 == 1e-40, so this shift is >> the tolerance).
MUTATION_SHIFT = 10 ** 20

# Cutoff of the Fricke exponential sum for L(E,1).
L_CUTOFF = 400


def implied_sha_interval(interval_L, interval_omega, c2, tors_order):
    """Certified interval for R = L * tors^2 / (Omega * c2)."""
    numerator = cert.scale(interval_L, tors_order * tors_order)
    denominator = cert.scale(interval_omega, c2)
    return cert.div(numerator, denominator)


def check_identity(R):
    """Raise AssertionError unless R is within a certified 1e-40 of 1.

    The interval [R[0], R[1]] must be CONTAINED in [1-1e-40, 1+1e-40], i.e.
        R[0] >= S - TOL_UNITS   and   R[1] <= S + TOL_UNITS,
    with S = 10**50 and TOL_UNITS = 10**10."""
    one = cert.S
    if R[0] < one - TOL_UNITS or R[1] > one + TOL_UNITS:
        raise AssertionError(
            "the BSD leading-coefficient identity FAILS: R = %r is not within "
            "1e-40 of 1" % (R,))
    return True


def implied_sha_integer(R):
    """The implied #Sha(E): R is a positive integer and lies within 1e-40 of 1,
    so the only possible integer value is 1."""
    one = cert.S
    lo_int = -((-R[0]) // one) if R[0] > 0 else 0          # ceil(R[0])
    hi_int = R[1] // one                                     # floor(R[1])
    ints = [n for n in range(max(lo_int, 1), hi_int + 1)]
    if ints != [1]:
        raise AssertionError("implied #Sha is not 1: candidate integers %r" % (ints,))
    return 1


def check():
    """Return a report dict.  Raises AssertionError if any certified check fails."""
    (L, _ldiag) = lvalue.lvalue(L_CUTOFF)
    (Om, _pdiag) = period.period()

    tors = idata.TORS_ORDER
    c2 = idata.TAMAGAWA_C2

    R = implied_sha_interval(L, Om, c2, tors)
    check_identity(R)
    sha = implied_sha_integer(R)

    # The convention control: the identity-component period must give 2,
    # NOT 1.  Asserted so that a change of period convention cannot pass
    # unnoticed.
    Om_half = period.identity_component_period()
    R_half = implied_sha_interval(L, Om_half, c2, tors)
    half_is_two = (R_half[1] >= 2 * cert.S - TOL_UNITS
                   and R_half[0] <= 2 * cert.S + TOL_UNITS)
    if not half_is_two:
        raise AssertionError(
            "convention control failed: the identity-component period gave %r, "
            "expected ~2" % (R_half,))

    return {
        "L": L,
        "Omega": Om,
        "R": R,
        "implied_sha": sha,
        "half_is_two": half_is_two,
        "tors_order": tors,
        "c2": c2,
    }


def mutation_control():
    """Corrupt the certified interval for L(E,1) and assert the check FAILS."""
    (L, _diag) = lvalue.lvalue(L_CUTOFF)
    Om, _p = period.period()
    tampered_L = (L[0] + MUTATION_SHIFT, L[1] + MUTATION_SHIFT)
    R_bad = implied_sha_interval(tampered_L, Om,
                                 idata.TAMAGAWA_C2, idata.TORS_ORDER)
    try:
        check_identity(R_bad)
    except AssertionError:
        pass
    else:
        raise RuntimeError(
            "MUTATION CONTROL FAILED: a tampered L(E,1) interval did not break "
            "the identity check -- the check is a rubber stamp")
    return "L"


def main():
    rep = check()
    L, Om, R = rep["L"], rep["Omega"], rep["R"]
    l_lo, l_hi = cert.to_decimal(L, 45)
    o_lo, o_hi = cert.to_decimal(Om, 45)
    r_lo, r_hi = cert.to_decimal(R, 45)

    print("BSD leading-coefficient identity for E: y^2 = x^3 - x  (Cremona 32a2)")
    print("  L(E,1)                       : %s" % l_lo)
    print("  Omega_E (full real locus)    : %s" % o_lo)
    print("  #E(Q)_tors                   : %d   (PROVED by Fermat descent)" % rep["tors_order"])
    print("  prod_p c_p = c_2             : %d   (Tate's algorithm, PARI cross-check)" % rep["c2"])
    print()
    print("  implied #Sha = L*%d^2/(Omega*c_2) : %s" % (
        rep["tors_order"], r_lo))
    print("                                    : %s" % r_hi)
    print("  implied #Sha (integer)       : %d" % rep["implied_sha"])
    print()
    print("  convention control: using the identity-component period alone would give")
    h_lo, _h_hi = cert.to_decimal(period.identity_component_period(), 45)
    print("    Omega_id = %s   -> implied #Sha = 2 (NOT 1): %s" % (
        h_lo, rep["half_is_two"]))
    print()

    # machine-readable lines for the verification transcript
    print("L_LO=%s" % l_lo)
    print("L_HI=%s" % l_hi)
    print("RATIO_LO=%s" % r_lo)
    print("RATIO_HI=%s" % r_hi)
    print("SHA_IMPLIED=%d" % rep["implied_sha"])
    print("IDENTITY=PASS")

    mutation_control()
    print("MUTATION-CONTROL-OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
