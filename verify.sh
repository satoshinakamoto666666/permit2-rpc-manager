#!/usr/bin/env bash
# verify.sh -- verify this artefact from scratch.
#
# WHAT THIS DOES
#   Runs every computation in src/, checks the results against ground truth
#   that is INDEPENDENT of the code being tested, and exits non-zero if
#   anything disagrees.
#
# DESIGN RULES (these are the rules that make a PASS meaningful):
#
#   1. NO SELF-CHECK.  A check that compares a script against the script's
#      own internals proves nothing.  Every numeric assertion below is
#      made against an EXTERNAL value: a recorded transcript from PARI/GP
#      (an independent implementation) or from John Cremona's ecdata
#      tables (an independent database), or against a value derived by a
#      DIFFERENT algorithm inside this repository.
#
#   2. THE PERIOD HAS THREE INDEPENDENT ROUTES.  period.py computes Omega_E
#      by the AGM, by a hypergeometric series, and by a theta series; they
#      must agree.  The L-value is computed from the a_n of the newform, and
#      the a_n are computed two ways (point counting vs eta product).
#      Neither check compares a thing with itself.
#
#   3. THE CONVENTION IS GUARDED.  The identity-component period must give
#      an implied #Sha of 2, NOT 1.  A silent change of period convention
#      is the classic way to get this special case wrong.
#
#   4. MUTATION TESTS ARE SEPARATE AND MANDATORY.  tests/mutation_tests.sh
#      corrupts inputs and REQUIRES verify.sh to fail.  A harness that
#      cannot fail is not a harness.  Run it after verify.sh.
#
#   5. NO NETWORK.  The ground truth is committed in data/.  This must run
#      on a machine with no internet and no PARI installed.  The optional
#      PARI-dependent certificate (src/sha2.py) is run only if `gp` exists.
#
# EXIT STATUS: 0 = everything verified; non-zero = something did not.

set -u
cd "$(dirname "$0")" || exit 2

FAIL=0
STEP=0

say()   { printf '%s\n' "$*"; }
head1() { STEP=$((STEP+1)); printf '\n=== [%d] %s\n' "$STEP" "$*"; }
ok()    { printf '    OK   %s\n' "$*"; }
bad()   { printf '    FAIL %s\n' "$*"; FAIL=$((FAIL+1)); }

if python -c "import sys; assert sys.version_info >= (3, 6)" >/dev/null 2>&1; then
  PY=python
else
  PY=python3
fi
command -v "$PY" >/dev/null 2>&1 || { say "python3 not found"; exit 2; }

# --------------------------------------------------------------------------
head1 "environment"
say "    python3 : $("$PY" -V 2>&1)"
say "    repo    : $(pwd)"

# --------------------------------------------------------------------------
head1 "curve invariants (exact integer arithmetic)"
# Ground truth: PARI ellglobalred / Cremona curvedata, recorded in
# data/pari-32a2.txt and data/ecdata-32a2.txt.
if "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, "src")
import tate
res = tate.tate_algorithm(-1, 0, 0, 2)
checks = [
    ("model",     res["model"],          (0, 0, 0, -1, 0)),
    ("min_disc",  res["min_disc"],       64),
    ("c4",        res["c4"],             48),
    ("c6",        res["c6"],             0),
    ("tamagawa",  res["tamagawa"],       2),
    ("conductor", res["conductor_frob"], 5),
    ("kodaira",   res["kodaira"],        "III"),
]
bad = 0
for name, got, want in checks:
    if got != want:
        print("    MISMATCH %-10s got %r want %r" % (name, got, want))
        bad += 1
# Ogg's formula control: f_p = v_p(Delta_min) + 1 - m
m = tate.vp(res["min_disc"], 2) + 1 - res["conductor_frob"]
if m != tate._n_components(res["kodaira"]):
    print("    MISMATCH Ogg components %d vs %s" % (m, res["kodaira"]))
    bad += 1
# good reduction at 3
res3 = tate.tate_algorithm(-1, 0, 0, 3)
if (res3["kodaira"], res3["tamagawa"], res3["conductor_frob"]) != ("I_0", 1, 0):
    print("    MISMATCH at p=3: %r" % (res3,))
    bad += 1
sys.exit(1 if bad else 0)
PYEOF
then ok "model, discriminant, c4, c6, Kodaira III, c_2=2, f_2=5, Ogg control, good reduction at 3"
else bad "curve invariants disagree with the recorded ground truth"
fi

# --------------------------------------------------------------------------
head1 "a_n: point counting vs eta product (two definitions, must agree)"
if "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, "src")
from a_n import build_table
N = 400
counting, eta, ap = build_table(N)
bad = [n for n in range(1, N+1) if counting[n] != eta[n]]
if bad:
    print("    MISMATCH at n=%r" % bad[:10]); sys.exit(1)
if ap.get(2) != 0:
    print("    MISMATCH a_2 = %r, expected 0 (additive reduction at 2)" % ap.get(2)); sys.exit(1)
# external spot checks (published values for 32a2)
for n, want in [(3, 0), (5, -2), (7, 0), (11, 0), (13, 6)]:
    if counting[n] != want:
        print("    MISMATCH a_%d = %r want %r" % (n, counting[n], want)); sys.exit(1)
print("    a_n agree for all n <= %d" % N)
PYEOF
then ok "400 coefficients agree; a_2,a_3,a_5,a_7,a_11,a_13 match published values"
else bad "the two a_n methods disagree"
fi

# --------------------------------------------------------------------------
head1 "L(E,1): certified interval vs PARI ellL1 (independent implementation)"
# The PARI value is PARSED OUT OF THE COMMITTED TRANSCRIPT, not hardcoded
# here.  That matters: if the transcript were corrupted, the check must
# fail rather than silently compare against our own private copy.
if "$PY" - <<'PYEOF'
import sys, re
sys.path.insert(0, "src")
import cert, lvalue
txt = open("data/pari-32a2.txt").read()
m = re.search(r"ellL1\s*=\s*([0-9]*\.?[0-9]+)", txt)
if not m:
    print("    MISMATCH could not parse ellL1 from data/pari-32a2.txt"); sys.exit(1)
PARI = m.group(1)
if len(PARI.replace(".", "")) < 45:
    print("    MISMATCH ellL1 in the transcript has only %d digits" % len(PARI.replace(".", "")))
    sys.exit(1)
(lo, hi), diag = lvalue.lvalue(400)
dlo, dhi = cert.to_decimal((lo, hi))
pari = cert.from_fraction(PARI)
if not (lo <= pari[1] and pari[0] <= hi):
    print("    MISMATCH certified interval does not contain PARI's ellL1")
    print("      ours: %s .. %s" % (dlo, dhi))
    print("      pari: %s" % PARI)
    sys.exit(1)
a = dlo.replace("-", "").lstrip("0"); b = PARI.replace("-", "").lstrip("0")
n = 0
for x, y in zip(a, b):
    if x != y: break
    n += 1
print("    PARI ellL1 (from the committed transcript): %s" % PARI)
print("    certified interval: %s .. %s" % (dlo, dhi))
print("    agrees with PARI ellL1 in %d leading digits" % n)
if n < 40:
    print("    MISMATCH: fewer than 40 agreeing digits"); sys.exit(1)
PYEOF
then ok "certified L(E,1) interval contains PARI's 60-digit ellL1 (40+ digits)"
else bad "certified L(E,1) does not agree with PARI's ellL1"
fi

# --------------------------------------------------------------------------
head1 "Omega_E: THREE independent routes, plus PARI, plus Cremona"
if "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, "src")
import cert, period
(lo, hi), diag = period.period()
if not diag["routes_agree"]:
    print("    MISMATCH the period routes disagree"); sys.exit(1)
for key in ("agm", "series", "theta"):
    if key not in diag:
        print("    MISMATCH missing route %r" % key); sys.exit(1)
# PARI: gamma(1/4)^2/sqrt(2*pi) at 60 digits.  Parsed from the committed
# transcript in data/ecdata-32a2.txt, so a corrupted transcript fails.
import re
txt = open("data/ecdata-32a2.txt").read()
m = re.search(r"PARI:\s*\n?\s*([0-9]*\.?[0-9]{40,})", txt)
if not m:
    # fall back to the value recorded in data/pari-32a2.txt
    txt2 = open("data/pari-32a2.txt").read()
    m = re.search(r"Gamma\(1/4\)\^2/sqrt\(2\*pi\)\s*=\s*([0-9]*\.?[0-9]+)", txt2)
if not m:
    print("    MISMATCH could not parse PARI's Omega_E value from the transcripts")
    sys.exit(1)
PARI = m.group(1)
if len(PARI.replace(".", "")) < 45:
    print("    MISMATCH PARI's Omega_E in the transcript has too few digits"); sys.exit(1)
pari = cert.from_fraction(PARI)
if not (lo <= pari[1] and pari[0] <= hi):
    print("    MISMATCH certified Omega_E interval does not contain PARI's value")
    print("      ours: %s .. %s" % cert.to_decimal((lo, hi)))
    print("      pari: %s" % PARI)
    sys.exit(1)
# Cremona curvedata field 39 stores 28 decimal places, ROUNDED, so the
# stored string may sit up to one ulp ABOVE the true value.  The correct
# check is agreement TO THE STORED PRECISION, not containment.
mm = re.search(r"field 39\s*=\s*([0-9]*\.?[0-9]+)", txt)
if not mm:
    print("    MISMATCH could not parse Cremona's real period from the transcript")
    sys.exit(1)
CREM = mm.group(1)
CREM_DIGITS = len(CREM.split(".")[1])
crem = cert.from_fraction(CREM)
tol = cert.S // (10 ** (CREM_DIGITS - 1))
if crem[0] - hi > tol or lo - crem[1] > tol:
    print("    MISMATCH certified Omega_E interval does not agree with Cremona's real period")
    sys.exit(1)
# the identity-component period must be exactly half
half = period.identity_component_period()
if not (half[1] * 2 >= lo and half[0] * 2 <= hi):
    print("    MISMATCH identity-component period is not half of Omega_E"); sys.exit(1)
dlo, dhi = cert.to_decimal((lo, hi))
a = dlo.replace("-", "").lstrip("0"); b = PARI.replace("-", "").lstrip("0")
n = 0
for x, y in zip(a, b):
    if x != y: break
    n += 1
print("    certified Omega_E: %s .. %s" % (dlo, dhi))
print("    routes A(AGM), B(hypergeometric), C(theta) agree; matches PARI in %d digits; matches Cremona" % n)
if n < 40:
    print("    MISMATCH: fewer than 40 agreeing digits with PARI"); sys.exit(1)
PYEOF
then ok "all three routes agree with each other, with PARI (40+ digits), and with Cremona's real period"
else bad "the period computation disagrees with the recorded ground truth"
fi

# --------------------------------------------------------------------------
head1 "the BSD identity itself (certified interval arithmetic)"
if "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, "src")
import cert, identity
rep = identity.check()
R = rep["R"]
one = cert.S
# the certified interval for R must be CONTAINED in [1-1e-40, 1+1e-40]
if R[0] < one - identity.TOL_UNITS or R[1] > one + identity.TOL_UNITS:
    print("    MISMATCH implied #Sha interval %r is not within 1e-40 of 1" % (R,)); sys.exit(1)
if rep["implied_sha"] != 1:
    print("    MISMATCH implied #Sha is %r, expected the integer 1" % rep["implied_sha"]); sys.exit(1)
if not rep["half_is_two"]:
    print("    MISMATCH the period-convention control did not give 2"); sys.exit(1)
dlo, dhi = cert.to_decimal(R)
print("    implied #Sha = %s .. %s" % (dlo, dhi))
print("    the only integer in the interval is 1")
print("    convention control: identity-component period gives 2, as required")
PYEOF
then ok "L(E,1)*16 = Omega_E*2 within 1e-40; implied #Sha is the integer 1; convention control fires"
else bad "the BSD leading-coefficient identity check failed"
fi

# --------------------------------------------------------------------------
head1 "the identity agrees with PARI's own BSD routine"
if grep -q "ellbsd         = 0.6555143885730299526162098974727798534207" data/pari-32a2.txt; then
  ok "data/pari-32a2.txt records PARI ellbsd = ellL1 (BSD ratio 1)"
else
  bad "data/pari-32a2.txt does not record the expected PARI ellbsd value"
fi

# --------------------------------------------------------------------------
head1 "independent database cross-check (Cremona ecdata)"
if grep -q "^[[:space:]]*32 a 2 \[0,0,0,-1,0\] 0 4 2 5.24411510858424 0.655514388573030 1.00000000000000 1$" data/ecdata-32a2.txt; then
  ok "Cremona allbsd row: rank 0, tors 4, Tamagawa 2, real period 5.24411510858424, BSD ratio 1"
else
  bad "Cremona allbsd row for 32a2 not found or altered"
fi
if grep -q "32 a 2 32 a 3" data/ecdata-32a2.txt; then
  ok "Cremona alllabels: Cremona 32a2 == LMFDB 32.a3 (NOT LMFDB 32.a2)"
else
  bad "the LMFDB label mapping is missing from data/ecdata-32a2.txt"
fi

# --------------------------------------------------------------------------
head1 "Sha[2] certificate (needs PARI/GP; skipped if 'gp' is absent)"
if command -v gp >/dev/null 2>&1; then
  if (cd src && "$PY" sha2.py >/tmp/bsd32a2-sha2.log 2>&1); then
    if grep -q "CONTROL OK" /tmp/bsd32a2-sha2.log && grep -q "Sha(E)\[2\] = 0 (trivial): True" /tmp/bsd32a2-sha2.log; then
      ok "2-descent certificate: rank 0 and Sha[2] trivial, with PARI's own worked example as control"
    else
      bad "sha2.py ran but did not report the expected certificate"
    fi
  else
    bad "sha2.py failed"
    tail -5 /tmp/bsd32a2-sha2.log | sed 's/^/       /'
  fi
else
  say "    SKIP 'gp' (PARI/GP) not installed -- the 2-descent certificate is"
  say "         optional; the committed transcript is in data/sha2-certificate.txt"
fi

# --------------------------------------------------------------------------
head1 "odd-primary Sha(E/Q) certificate (CM Grossencharacter + Cl_f(K)=1 + Hurwitz/Rubin)"
if "$PY" src/odd_sha.py >/tmp/bsd32a2-oddsha.log 2>&1; then
  if grep -q "ODD-SHA-OK" /tmp/bsd32a2-oddsha.log && grep -q "#Cl_f(K) = 1" /tmp/bsd32a2-oddsha.log; then
    ok "odd-primary Sha(E/Q): psi_E verified (p<=400), #Cl_(2+2i)(Q(i))=1, E(K)[l^inf]=0, R_alg=1"
  else
    bad "odd_sha.py ran but did not report ODD-SHA-OK"
  fi
else
  bad "odd_sha.py failed"
  tail -5 /tmp/bsd32a2-oddsha.log | sed 's/^/       /'
fi

# --------------------------------------------------------------------------
head1 "change-of-variables regression (delta invariance + PARI on the additive branch)"
#
# The p >= 5 branch of Tate's algorithm translates the singular point of the
# reduced cubic to the origin.  If the transformed coefficients are wrong, the
# discriminant changes and the Tamagawa numbers come out wrong.  The control
# needs a model with a1 != 0: with a1 = 0 the erroneous term is invisible and
# the control passes on broken code.  tests/tate_translation_differential.py
# checks delta invariance (no PARI needed) and cross-checks c_p and f_p
# against PARI/GP's elllocalred (an independent oracle).
if "$PY" tests/tate_translation_differential.py >/tmp/bsd32a2-tatetrans.log 2>&1; then
  if grep -q "TATE-TRANSLATION-CONTROL-OK" /tmp/bsd32a2-tatetrans.log; then
    ok "change-of-variables formulas: delta invariance holds and the additive branch agrees with PARI"
  else
    bad "the change-of-variables control did not report OK (see /tmp/bsd32a2-tatetrans.log)"
  fi
else
  bad "the change-of-variables control FAILED (see /tmp/bsd32a2-tatetrans.log)"
  sed -n '1,20p' /tmp/bsd32a2-tatetrans.log
fi

# --------------------------------------------------------------------------
head1 "guard liveness: the INTERNAL controls must still be able to fail"
#
# A control that cannot fail is not a control.  The modules each contain
# their own tamper-detection (identity.mutation_control,
# period.mutation_control, and tate's Ogg consistency check).  Those are
# self-checks, so we do not rely on them alone -- but we MUST require them
# to still EXIST and still FIRE, otherwise a well-meaning edit could
# quietly delete a guard and this harness would never know.
#
# For each internal guard we therefore (a) require the guard to be present
# and (b) require the module to detect a deliberate corruption of it.
if "$PY" - <<'PYEOF'
import sys, re, os
sys.path.insert(0, "src")
bad = 0

# ---- 1. identity.mutation_control() must exist and must FIRE -------------
try:
    import identity
except Exception as e:
    print("    MISMATCH cannot import identity: %r" % (e,)); sys.exit(1)
if not hasattr(identity, "mutation_control"):
    print("    MISMATCH identity.mutation_control() has been REMOVED")
    bad += 1
else:
    try:
        identity.mutation_control()
    except RuntimeError as e:
        print("    MISMATCH identity's own mutation control FAILED to detect a "
              "tampered L-value: %r" % (e,))
        bad += 1
    except Exception as e:
        print("    MISMATCH identity.mutation_control() raised unexpectedly: %r" % (e,))
        bad += 1
    else:
        print("    identity.mutation_control() present and fires")

# ---- 2. period.mutation_control() must exist and must FIRE ---------------
try:
    import period
except Exception as e:
    print("    MISMATCH cannot import period: %r" % (e,)); sys.exit(1)
if not hasattr(period, "mutation_control"):
    print("    MISMATCH period.mutation_control() has been REMOVED")
    bad += 1
else:
    try:
        period.mutation_control()
    except RuntimeError as e:
        print("    MISMATCH period's own mutation control FAILED to detect a "
              "tampered route: %r" % (e,))
        bad += 1
    except Exception as e:
        print("    MISMATCH period.mutation_control() raised unexpectedly: %r" % (e,))
        bad += 1
    else:
        print("    period.mutation_control() present and fires")

# ---- 3. tate's Ogg consistency check must be present AND LIVE ----------
# Presence is not enough: the check must actually be able to FAIL.  We
# require it to REJECT a deliberately inconsistent set of invariants, and
# to ACCEPT the real ones.  A check that accepts everything is decoration.
try:
    import tate
except Exception as e:
    print("    MISMATCH cannot import tate: %r" % (e,)); sys.exit(1)
if not hasattr(tate, "ogg_consistency"):
    print("    MISMATCH tate.ogg_consistency() has been REMOVED")
    bad += 1
else:
    real = tate.tate_algorithm(-1, 0, 0, 2)
    if not tate.ogg_consistency(real, 2):
        print("    MISMATCH tate's Ogg check REJECTS the real curve's invariants")
        bad += 1
    else:
        # a tampered conductor exponent must be rejected
        tampered = dict(real)
        tampered["conductor_frob"] = real["conductor_frob"] + 1
        if tate.ogg_consistency(tampered, 2):
            print("    MISMATCH tate's Ogg check ACCEPTS tampered invariants "
                  "-- the control is vacuous")
            bad += 1
        else:
            print("    tate's Ogg consistency control present and LIVE "
                  "(accepts the real invariants, rejects tampered ones)")

# ---- 4. the lvalue.py a_n cross-check must be present AND LIVE ---------
# Again, presence is not enough.  We require lvalue.lvalue() to REJECT a
# pair of a_n tables that disagree.  We do that by monkey-patching
# a_n.build_table to return mismatched tables and requiring an error.
try:
    import a_n
    import lvalue
except Exception as e:
    print("    MISMATCH cannot import a_n/lvalue: %r" % (e,)); sys.exit(1)
if not hasattr(lvalue, "lvalue"):
    print("    MISMATCH lvalue.lvalue() has been REMOVED")
    bad += 1
else:
    real_build = a_n.build_table
    def fake_build(cutoff):
        counting, eta, ap = real_build(cutoff)
        eta = list(eta)
        eta[5] = eta[5] + 1        # corrupt ONE coefficient
        return counting, eta, ap
    a_n.build_table = fake_build
    lvalue.build_table = fake_build
    try:
        try:
            lvalue.lvalue(20)
        except AssertionError:
            print("    lvalue's a_n cross-check present and LIVE "
                  "(rejects mismatched a_n tables)")
        else:
            print("    MISMATCH lvalue ACCEPTED mismatched a_n tables "
                  "-- the control is vacuous")
            bad += 1
    finally:
        a_n.build_table = real_build
        lvalue.build_table = real_build

# ---- 5. the tolerances must not have been silently loosened --------------
# The identity check must be within 1e-40 of 1, and the period routes must
# agree to 1e-40.  We re-derive the expected tolerance INDEPENDENTLY of
# the modules (they must not be allowed to define their own standard of
# correctness).  In fixed-point units (S = 10**50), 1e-40 is 10**10.
import cert
EXPECTED_TOL = 10 ** 10
for modname in ("identity", "period"):
    mod = sys.modules[modname]
    tol = getattr(mod, "TOL_UNITS", None)
    if tol is None:
        print("    MISMATCH %s.TOL_UNITS has been removed" % modname)
        bad += 1
    elif tol > EXPECTED_TOL:
        print("    MISMATCH %s.TOL_UNITS = %r is LOOSER than the required 1e-40 (%r)"
              % (modname, tol, EXPECTED_TOL))
        bad += 1
    else:
        print("    %s.TOL_UNITS = %r (at least as strict as 1e-40)" % (modname, tol))

sys.exit(1 if bad else 0)
PYEOF
then ok "all internal guards are present, live, and still at least as strict as 1e-40"
else bad "an internal guard was removed, made vacuous, or loosened"
fi

# --------------------------------------------------------------------------
head1 "documentation hygiene (no overclaiming)"
# A docstring is a claim, not a control.  These greps make sure the
# documents do not contain the words that would overstate what was done.
#
# The pattern must not fire on the DISCLAIMERS this artefact is full of
# ("does NOT prove BSD", "NOT a solution of the Millennium Prize Problem",
# ...).  So a line is exempt if it contains a negating qualifier.
BADPAT='prove[sd]? (the |general )?BSD|solves? the Millennium|solution to the Millennium|BSD is (proved|true)|full proof of BSD|settles? (the )?BSD'
EXEMPT='not |never |open |no |cannot |does not |is not |nor |rather than |instead of |Not |Never |OPEN |No |NOT '
if grep -rniE "$BADPAT" README.md PROOF.md CLAIMS.md OPEN_REMAINDER.md src/*.py 2>/dev/null \
     | grep -viE "$EXEMPT"; then
  bad "an overclaiming phrase was found in the documentation"
else
  ok "no overclaiming phrases in README/PROOF/CLAIMS/OPEN_REMAINDER/src"
fi

# The specific overclaim that this artefact must NOT make: using PARI's `s`
# component as if it proved Sha[2] = 0.
if grep -rn "s = 0, i.e. the 2-part of Sha is trivial" *.md src/*.py 2>/dev/null; then
  bad "the known-bad 's = 0 proves Sha[2]=0' overclaim is still present"
else
  ok "the 's = 0 implies Sha[2] = 0' overclaim is absent"
fi

# All four status tags must be present in CLAIMS.md.
MISSING=0
for pat in 'PROVED' 'CITED' 'COMPUTED' 'OPEN'; do
  if ! grep -q "$pat" CLAIMS.md; then MISSING=$((MISSING+1)); fi
done
if [ "$MISSING" -ne 0 ]; then bad "CLAIMS.md is missing status tags"; else ok "CLAIMS.md carries all four status tags"; fi

# --------------------------------------------------------------------------
printf '\n=====================================================\n'
if [ "$FAIL" -eq 0 ]; then
  printf 'VERIFY: ALL CHECKS PASSED (%d steps)\n' "$STEP"
  printf '=====================================================\n'
  exit 0
else
  printf 'VERIFY: %d CHECK(S) FAILED\n' "$FAIL"
  printf '=====================================================\n'
  exit 1
fi
