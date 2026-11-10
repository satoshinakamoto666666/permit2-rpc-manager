"""The 2-primary part of Sha(E), certified from PARI's 2-descent, with a CONTROL.

WHAT IS PROVED HERE, AND HOW
----------------------------
PARI/GP's `ellrank` returns [r, R, s, L] where

  * r  is a lower bound for the rank of E(Q),
  * R  is an UPPER bound for the rank of E(Q), obtained from the 2-Selmer
       group:  R = C - T,  where C = dim_F2 Sel_2(E) (the 2-Selmer rank, which
       PARI computes exactly) and T = dim_F2 E(Q)[2] (the rank of the rational
       2-torsion),
  * s  is the rank of Sha[2]/2 Sha[4] -- it is only a MINORATION of the
       2-rank of Sha, and s = 0 does NOT imply Sha[2] = 0.

PARI's manual states the identity

    C = T + R + S,          S = the 2-rank of Sha (i.e. dim_F2 Sha[2])

where R is the TRUE rank and C = dim_F2 Sel_2(E) is the 2-Selmer rank, which
PARI computes exactly.  The SECOND component of ellrank's output is the
2-descent upper bound on the rank, namely

    R_upper = C - T.

Combining the two gives

    S = C - T - R_true = R_upper - R_true.

CAUTION -- THIS IS NOT IN GENERAL EQUAL TO R_upper - r, because r is only a
LOWER bound on R_true.  In general all we get is S <= R_upper - r.  The
inference is EXACT precisely when the two bounds COINCIDE (r == R_upper),
because then R_true = r = R_upper and

    S = R_upper - r.

For our curve ellrank returns [0, 0, 0, []], so r == R_upper == 0, the rank
is exactly 0, and S = 0.  Since Sha[2] is an F_2-vector space, S = 0 means
Sha[2] is trivial.

EQUIVALENT ARGUMENT (no reliance on the r/R coincidence): T = 2 because E
has full rational 2-torsion ({O,(0,0),(1,0),(-1,0)}), and R_upper = C - T =
0 forces C = 2.  The 2-Selmer group surjects onto E(Q)/2E(Q), whose
dimension is 2 (E(Q) = (Z/2)^2, proved in PROOF.md), so the two have equal
dimension and Sha[2] = 0.

WHY THE `s` COMPONENT CANNOT BE USED.  Per ??ellrank, the algorithm computes
"the rank of G[2]/2G[4] (s)", and "the value s gives a minoration of S".
So s = 0 does NOT imply S = 0 -- (Z/4)^2 has s = 0 but S = 2.  Any claim
of the form "PARI's ellrank returned s = 0, hence Sha[2] = 0" is WRONG.

THE CONTROL
-----------
The inference above is validated on PARI's OWN worked example, where the
manual states the answer independently:

    E = ellinit([-113^2, 0])   ->  ellrank = [0, 2, 0, []]
    The manual then shows, assuming BSD, that Sha has cardinal 16 and is
    isomorphic to (Z/4Z)^2, i.e. its 2-rank is S = 2.

Our formula predicts S = R_upper - r = 2 - 0 = 2 (here the true rank is 0,
so r = R_true and the inference is exact).  If the formula were wrong --
wrong sign, wrong offset -- this control would fail.  (Note that this example
ALSO shows why `s` cannot be used: its s = 0 while Sha is nontrivial -- s measures Sha[2]/2Sha[4], which
vanishes for (Z/4)^2.)

WHAT IS NOT PROVED HERE
-----------------------
This establishes the 2-PRIMARY part only.  The ODD part of Sha is not
settled by a 2-descent and is treated as CITED in CLAIMS.md.
"""

import re
import shutil
import subprocess

# The control from PARI's manual: ellrank = [0, 2, 0, []] and the manual
# states Sha is (Z/4Z)^2, i.e. 2-rank 2.
CONTROL_CURVE = [-113 ** 2, 0]
CONTROL_EXPECTED_S = 2


def _gp(script, timeout=300):
    proc = subprocess.run(["gp", "-q", "-f"], input=script,
                          capture_output=True, text=True, timeout=timeout)
    return proc.stdout


def _first_vec(text):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            return line
    return None


def _parse_vec(text):
    """Parse a GP vector literal such as '[0, 0, 0, []]'."""
    text = re.sub(r"Mat\((\[[^\[\]]*\])\)", r"\1", text.strip())
    inner = text[1:-1].strip()
    if not inner:
        return []
    out, depth, cur = [], 0, ""
    for ch in inner:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return [_parse_vec(x) if x.startswith("[") else int(x) for x in out]


def ellrank(model):
    """Run PARI's ellrank on a short Weierstrass model; return (r, R, s)."""
    script = "E=ellinit([0,0,0,%d,%d],1);\nprint(ellrank(E));\n" % tuple(model)
    line = _first_vec(_gp(script))
    if line is None:
        raise RuntimeError("could not read PARI's ellrank output")
    vec = _parse_vec(line)
    return vec[0], vec[1], vec[2]


def two_rank_of_sha(model):
    """The 2-rank S of Sha(E) for the given model, from ellrank's rank bounds.

    S = R_upper - R_true, and R_true is only bracketed by [r, R_upper].  When
    the bounds COINCIDE (r == R_upper) the value is exact; otherwise
    R_upper - r is merely an UPPER bound on S.  We therefore return both the
    value and a flag saying whether it is exact.
    """
    r, R, _s = ellrank(model)
    exact = (r == R)
    return R - r, (r, R), exact


def check():
    """Run the control and the curve of interest.  Returns a report dict."""
    if shutil.which("gp") is None:
        raise RuntimeError("PARI/GP ('gp') is required for this certificate")

    # ---- control: PARI's own worked example -----------------------------
    s_ctrl, (r_ctrl, R_ctrl), exact_ctrl = two_rank_of_sha(CONTROL_CURVE)
    if s_ctrl != CONTROL_EXPECTED_S:
        raise AssertionError(
            "CONTROL FAILED: PARI's manual states Sha ~ (Z/4Z)^2 (2-rank 2) for "
            "ellinit([-113^2,0]), but the inference S = R_upper - r gives %d.  "
            "The inference is wrong, so it must not be used for the real curve."
            % s_ctrl)

    # ---- the curve of interest ------------------------------------------
    s_real, (r_real, R_real), exact_real = two_rank_of_sha([-1, 0])

    report = {
        "control_2rank": s_ctrl,
        "control_ok": True,
        "real_r": r_real,
        "real_R": R_real,
        "real_2rank_of_sha": s_real,
        "real_2rank_exact": exact_real,
        "sha_2_is_trivial": s_real == 0,
        "rank_certified_zero": r_real == 0 and R_real == 0,
    }
    if r_real != 0 or R_real != 0:
        raise AssertionError("PARI's ellrank did not certify rank 0: %r" % ((r_real, R_real),))
    if not exact_real:
        raise AssertionError(
            "the rank bounds do not coincide (%d, %d), so S = R_upper - r is "
            "only an upper bound on the 2-rank of Sha and cannot certify "
            "Sha[2] = 0" % (r_real, R_real))
    if s_real != 0:
        raise AssertionError("Sha[2] is not trivial: 2-rank = %d" % s_real)
    return report


def main():
    rep = check()
    print("2-primary part of Sha(E) for E : y^2 = x^3 - x")
    print("  inference used : S = R_upper - r, from PARI C = T + R + S (exact when the bounds coincide)")
    print("  CONTROL on PARI's own worked example ellinit([-113^2,0]):")
    print("    inferred 2-rank of Sha = %d (manual states Sha ~ (Z/4Z)^2, "
          "2-rank 2)  -> CONTROL OK" % rep["control_2rank"])
    print()
    print("  ellrank(E) rank bounds : r = %d, R = %d  (rank certified 0: %s)" % (
        rep["real_r"], rep["real_R"], rep["rank_certified_zero"]))
    print("  2-rank of Sha          : %d" % rep["real_2rank_of_sha"])
    print("  => Sha(E)[2] = 0 (trivial): %s" % rep["sha_2_is_trivial"])
    print()
    print("  NOTE: this certifies the 2-PRIMARY part only.  The odd part of Sha")
    print("  is NOT settled by a 2-descent and is CITED, not proved, here.")


if __name__ == "__main__":
    main()
