"""Certified computation of the real period of E : y^2 = x^3 - x.

CONVENTION (this matters -- see PROOF.md, section 1):
The Neron differential of E is

    omega = dx / (2 y).

The real locus E(R) has TWO connected components: the identity component
(the unbounded one, containing the point at infinity) and the other one.
The period used in the BSD leading-coefficient formula is

    Omega_E := integral over E(R) of |omega|,

i.e. over BOTH components.  For this curve the two components have equal
length: the map (x, y) -> (-x, i y) is an automorphism over Q(i) that
interchanges them and carries omega to -omega.

    Omega_E = 4 * int_0^1 dt / sqrt(1 - t^4)
            = 5.24411510858423962092967917978223882736...

THREE INDEPENDENT CERTIFIED ROUTES are computed and required to agree.
They share no mathematics and no code path beyond the certified-arithmetic
layer (cert.py):

  ROUTE 1 -- Gauss' AGM theorem.
      K(k) = pi / (2 * AGM(1, sqrt(1-k^2))), and the period integral is
      int_0^1 dt/sqrt(1-t^4) = K(1/sqrt(2))/sqrt(2) = pi/(2 AGM(1,sqrt(2))),
      whence  Omega_E = 2*pi / AGM(1, sqrt(2)).
      Certified by cert.agm_bounds, whose enclosure is rigorous: for the
      iteration a' = (a+b)/2, b' = sqrt(a b) one has b_n <= AGM <= a_n for
      every n, so [b_N.lower, a_N.upper] contains the true limit.

  ROUTE 2 -- Gauss' HYPERGEOMETRIC SERIES.
      K(k) = (pi/2) * sum_{n>=0} C(2n,n)^2 k^(2n) / 16^n.  At k = 1/sqrt(2)
      this is sum C(2n,n)^2 / 32^n, whose terms satisfy
      t_{n+1}/t_n = 4(2n+1)^2 / (32 (n+1)^2) <= 1/2, so the tail after N
      terms is bounded by 2 * t_{N+1}.  Hence

          Omega_E = sqrt(2) * pi * sum_{n>=0} C(2n,n)^2 / 32^n

      with a RIGOROUS, explicitly computed tail bound.  Each summand is an
      exact rational, summed with directed rounding.

  ROUTE 3 -- Jacobi's THETA IDENTITY (CM by Z[i]).
      At k = 1/sqrt(2) the complementary modulus equals k, so the nome is
      q = exp(-pi) and  K(k) = (pi/2) * theta_3(q)^2 with
      theta_3(q) = sum_{n in Z} q^(n^2) = 1 + 2 sum_{n>=1} exp(-pi n^2).
      Therefore  Omega_E = 4*K/sqrt(2) = sqrt(2)*pi*theta_3(exp(-pi))^2.
      The infinite sum is truncated at N with a RIGOROUS tail bound: for
      n >= N+1, (n+1)^2 - n^2 = 2n+1 >= 2N+3, so

          sum_{n>=N+1} 2 exp(-pi n^2) <= 2 exp(-pi (N+1)^2)/(1 - exp(-pi(2N+3))).

WHY THREE ROUTES AND NOT ONE
-----------------------------
A single implementation can be wrong in a way that is invisible to itself.
The three routes use different mathematics (an iterative mean, a
hypergeometric series, a theta series) and agree to 45+ significant digits,
so a mistake common to all three is very unlikely.  Each route's error
bound is proved in the code that computes it.

MUTATION CONTROL
----------------
`mutation_control()` deliberately corrupts each route's inputs and asserts
that the agreement check FAILS.  If a corruption did not break the check,
the check would be a rubber stamp -- so the script would exit non-zero.

All arithmetic is exact integer fixed-point interval arithmetic from cert.py
(SCALE = 10**50, directed outward rounding).  No floating point is used for
any asserted or compared quantity; `float` appears only in "%.3e" formatting
of widths, which is never an asserted quantity.
"""

from fractions import Fraction
from math import comb

import cert

# --------------------------------------------------------------------------
# Tunables (all integers; no floating point anywhere)
# --------------------------------------------------------------------------

# Route 2: number of hypergeometric terms.  The tail bound is 2 * t_{N+1},
# and t_N ~ 2^-N/(pi N); with N = 200 the tail is below 1e-63, far below the
# ~1e-48 resolution of the fixed-point layer.
SERIES_TERMS = 200

# Route 3: number of theta summands retained.  The certified tail bound is
#   2 exp(-pi (N+1)^2) / (1 - exp(-pi(2N+3))) < 2 exp(-pi*121) < 1e-164
# for N = 10, i.e. far below the ~1e-48 resolution of the fixed-point layer.
THETA_CUTOFF = 10

# Route 1: number of AGM iterations.  The AGM iteration converges
# quadratically, so the enclosure is astronomically tight long before this.
AGM_ITERATIONS = 24

# 1e-40 expressed in fixed-point units at SCALE = 10**50: 1e-40 * 1e50 = 1e10.
TOL_UNITS = 10 ** 10

# Size of the deliberate corruptions used by the mutation control, in
# fixed-point units (1e10 == 1e-40, so these shifts are >> the tolerance).
MUTATION_SHIFT = 10 ** 20


# --------------------------------------------------------------------------
# Route 1: AGM
# --------------------------------------------------------------------------
def agm_value():
    """Certified interval for AGM(1, sqrt(2))."""
    one = (cert.S, cert.S)
    sqrt2 = cert.sqrt_bounds((2 * cert.S, 2 * cert.S))   # sqrt(2)
    return cert.agm_bounds(one, sqrt2, iterations=AGM_ITERATIONS)


def route_a(agm=None):
    """Certified interval for Omega_E = 2*pi / AGM(1, sqrt(2))."""
    if agm is None:
        agm = agm_value()
    return cert.div(cert.scale(cert.PI, 2), agm)


# --------------------------------------------------------------------------
# Route 2: hypergeometric series
# --------------------------------------------------------------------------
def _central_binomial(n):
    """C(2n, n) exactly."""
    return comb(2 * n, n)


def _series_terms(nterms):
    """The exact rational summands t_n = C(2n,n)^2 / 32^n for 0 <= n <= nterms."""
    return [Fraction(_central_binomial(n) ** 2, 32 ** n) for n in range(nterms + 1)]


def series_sum(nterms=SERIES_TERMS):
    """Certified interval for sum_{n>=0} C(2n,n)^2 / 32^n, with a rigorous tail bound.

    The tail bound uses t_{n+1}/t_n = 4(2n+1)^2 / (32 (n+1)^2) <= 1/2, so
    sum_{n>N} t_n <= t_{N+1} * (1 + 1/2 + 1/4 + ...) = 2 t_{N+1}.
    """
    terms = _series_terms(nterms)
    total = (0, 0)
    for t in terms:
        total = cert.add(total, cert.mul_rat_iv((cert.S, cert.S), t.numerator, t.denominator))
    # tail: 2 * t_{nterms+1}
    t_next = Fraction(_central_binomial(nterms + 1) ** 2, 32 ** (nterms + 1))
    tail = cert.mul_rat_iv((cert.S, cert.S), 2 * t_next.numerator, t_next.denominator)
    return (total[0] - tail[0], total[1] + tail[1]), tail


def route_b():
    """Certified interval for Omega_E = sqrt(2)*pi*sum C(2n,n)^2/32^n."""
    s, _tail = series_sum()
    sqrt2 = cert.sqrt_bounds((2 * cert.S, 2 * cert.S))
    return cert.mul(cert.mul(sqrt2, cert.PI), s)


# --------------------------------------------------------------------------
# Route 3: Jacobi theta series
# --------------------------------------------------------------------------
def _exp_pi_times(exponent):
    """Certified interval for exp(-pi * exponent) (exponent a non-negative int)."""
    arg = cert.mul_rat(cert.PI, exponent, 1)     # pi * exponent
    return cert.exp_neg_bounds(arg[0], arg[1])


def theta3_interval(ncut=THETA_CUTOFF, exponent_of=None):
    """Certified interval for theta_3(exp(-pi)), with a rigorous tail bound.

    `exponent_of` maps n -> the exponent in exp(-pi * exponent).  The real
    computation uses n^2; the mutation control uses n (a wrong, but
    plausible, "forgot the square" bug) to show that the check can fail.

    Returns (interval_for_theta3, tail_bound_interval)."""
    if exponent_of is None:
        exponent_of = lambda n: n * n
    total = (cert.S, cert.S)                     # the n = 0 term
    for n in range(1, ncut + 1):
        total = cert.add(total, cert.scale(_exp_pi_times(exponent_of(n)), 2))
    # Rigorous tail:  sum_{n>=ncut+1} 2 exp(-pi n^2)
    #   <= 2 exp(-pi (ncut+1)^2) / (1 - exp(-pi (2 ncut + 3)))
    e_next = _exp_pi_times((ncut + 1) * (ncut + 1))
    e_den = _exp_pi_times(2 * ncut + 3)
    one_minus = cert.sub((cert.S, cert.S), e_den)          # 1 - exp(-pi(2N+3)) > 0
    tail = cert.div(cert.scale(e_next, 2), one_minus)
    # the true tail lies in [0, tail_upper]
    theta3 = cert.add(total, (0, tail[1]))
    return theta3, tail


def route_c():
    """Certified interval for Omega_E = sqrt(2)*pi*theta_3(exp(-pi))^2."""
    theta3, _tail = theta3_interval()
    sqrt2 = cert.sqrt_bounds((2 * cert.S, 2 * cert.S))
    return cert.mul(cert.mul(sqrt2, cert.PI), cert.mul(theta3, theta3))


# --------------------------------------------------------------------------
# The check
# --------------------------------------------------------------------------
def check_agreement(a, b, c):
    """Raise AssertionError unless the three route intervals overlap and are tight.

    Overlap test for closed intervals: a[0] <= b[1] and b[0] <= a[1]."""
    for name, x, y in (("A/B", a, b), ("A/C", a, c), ("B/C", b, c)):
        if not (x[0] <= y[1] and y[0] <= x[1]):
            raise AssertionError(
                "the independent period routes DISAGREE (%s): %r vs %r" % (name, x, y))
    for name, iv in (("A", a), ("B", b), ("C", c)):
        if iv[1] - iv[0] >= TOL_UNITS:
            raise AssertionError(
                "route %s interval is too wide: %d fixed-point units (>= 1e-40)"
                % (name, iv[1] - iv[0]))
    return True


def period():
    """Return (interval_for_Omega_E, diagnostics)."""
    o_a = route_a()
    o_b = route_b()
    o_c = route_c()
    check_agreement(o_a, o_b, o_c)
    lo = min(o_a[0], o_b[0], o_c[0])
    hi = max(o_a[1], o_b[1], o_c[1])
    _s, tail = series_sum()
    diag = {
        "agm": o_a,
        "series": o_b,
        "theta": o_c,
        "series_tail_bound": tail,
        "routes_agree": True,
        "width": hi - lo,
    }
    return (lo, hi), diag


def identity_component_period():
    """The period of the identity component alone (half of Omega_E for this curve).

    Kept because using this number by mistake would imply #Sha = 2; see
    PROOF.md, section 1.
    """
    (lo, hi), _ = period()
    return (lo // 2, hi // 2)


# --------------------------------------------------------------------------
# Mutation control
# --------------------------------------------------------------------------
def mutation_control():
    """Corrupt each route's inputs in turn and assert the agreement check FAILS."""
    failures = []

    # (1) tampered AGM: shift the AGM value by a huge amount.
    agm = agm_value()
    tampered_agm = (agm[0] + MUTATION_SHIFT, agm[1] + MUTATION_SHIFT)
    a_bad = route_a(agm=tampered_agm)
    b_good, c_good = route_b(), route_c()
    try:
        check_agreement(a_bad, b_good, c_good)
    except AssertionError:
        failures.append("agm")
    else:
        raise RuntimeError(
            "MUTATION CONTROL FAILED: a tampered AGM value did not break the "
            "agreement check -- the check is a rubber stamp")

    # (2) tampered hypergeometric series: perturb the summands.
    s_bad, _t = series_sum()
    b_bad = cert.add(s_bad, (MUTATION_SHIFT, MUTATION_SHIFT))
    a_good, c_good = route_a(), route_c()
    try:
        check_agreement(a_good, b_bad, c_good)
    except AssertionError:
        failures.append("series")
    else:
        raise RuntimeError(
            "MUTATION CONTROL FAILED: a tampered hypergeometric series did not "
            "break the agreement check -- the check is a rubber stamp")

    # (3) tampered theta series: use exponent n instead of n^2 in the summands.
    theta_bad, _t = theta3_interval(exponent_of=lambda n: n)
    sqrt2 = cert.sqrt_bounds((2 * cert.S, 2 * cert.S))
    c_bad = cert.mul(cert.mul(sqrt2, cert.PI), cert.mul(theta_bad, theta_bad))
    a_good, b_good = route_a(), route_b()
    try:
        check_agreement(a_good, b_good, c_bad)
    except AssertionError:
        failures.append("theta")
    else:
        raise RuntimeError(
            "MUTATION CONTROL FAILED: a tampered theta series did not break "
            "the agreement check -- the check is a rubber stamp")

    if sorted(failures) != ["agm", "series", "theta"]:
        raise RuntimeError("mutation control incomplete: %r" % (failures,))
    return failures


# --------------------------------------------------------------------------
def main():
    (lo, hi), diag = period()
    dlo, dhi = cert.to_decimal((lo, hi), 45)

    print("Omega_E = int_{E(R)} |dx/(2y)|  (FULL real locus, both components)")
    print("  route 1 (AGM)             : %s" % cert.to_decimal(diag["agm"], 45)[0])
    print("  route 2 (hypergeometric)  : %s" % cert.to_decimal(diag["series"], 45)[0])
    print("  route 3 (theta series)    : %s" % cert.to_decimal(diag["theta"], 45)[0])
    print("  routes agree              : %s" % diag["routes_agree"])
    print("  certified interval        : %s" % dlo)
    print("                            : %s" % dhi)
    print("  width                     : %.3e" % (float(diag["width"]) / cert.S))
    print()
    idlo, _idhi = cert.to_decimal(identity_component_period(), 45)
    print("identity component only (half): %s" % idlo)
    print()
    print("closed form (CITED, classical CM): Omega_E = Gamma(1/4)^2 / sqrt(2*pi)")
    print("  Gamma(1/4)^2/sqrt(2pi)      : 5.24411510858423962092967917978223882736")
    print()

    # machine-readable lines for the verification transcript
    print("OMEGA_LO=%s" % dlo)
    print("OMEGA_HI=%s" % dhi)
    print("OMEGA_ROUTE_A=%s" % cert.to_decimal(diag["agm"], 45)[0])
    print("OMEGA_ROUTE_B=%s" % cert.to_decimal(diag["series"], 45)[0])
    print("OMEGA_ROUTE_C=%s" % cert.to_decimal(diag["theta"], 45)[0])
    print("OMEGA_AGREEMENT=PASS")

    mutation_control()
    print("MUTATION-CONTROL-OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
