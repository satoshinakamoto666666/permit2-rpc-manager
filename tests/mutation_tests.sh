#!/usr/bin/env bash
# tests/mutation_tests.sh -- prove that the verification harness can FAIL.
#
# WHY THIS FILE EXISTS
#   A verification suite that cannot fail is not a verification suite: it is
#   decoration.  This script takes a COPY of the repository, corrupts one
#   input at a time, and REQUIRES that ./verify.sh on the corrupted copy
#   exits NON-ZERO.  If a corruption is not detected, this script exits
#   non-zero and says so.
#
#   Each mutation targets a different kind of ground truth:
#     M1  the recorded PARI transcript (a corrupted oracle)
#     M2  the recorded Cremona transcript (a corrupted oracle)
#     M3  the certified L-value (a corrupted computation)
#     M4  the Tamagawa number (a corrupted local invariant)
#     M5  the period convention (the classic subtle error)
#
#   M5 is the important one: it changes the code in the way a well-meaning
#   contributor might, and requires the guard in src/identity.py to fire.
#
# USAGE:  ./tests/mutation_tests.sh
# EXIT:   0 = every mutation was detected; non-zero = a mutation slipped through.

set -u
if python -c "import sys; assert sys.version_info >= (3, 6)" >/dev/null 2>&1; then
  PY=python
else
  PY=python3
fi
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/bsd32a2-mut.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0
CASES=0

say()  { printf '%s\n' "$*"; }
ok()   { PASS=$((PASS+1)); printf '    OK   %s\n' "$*"; }
bad()  { FAIL=$((FAIL+1)); printf '    FAIL %s\n' "$*"; }

# fresh_copy <name> -> path to a pristine copy of the repo
fresh_copy() {
  local dest="$WORK/$1"
  mkdir -p "$dest"
  # copy everything except .git and __pycache__
  (cd "$REPO" && tar cf - --exclude=.git --exclude=__pycache__ .) | (cd "$dest" && tar xf -)
  printf '%s' "$dest"
}

# run_verify <dir> -> exit status of ./verify.sh in <dir>
run_verify() {
  (cd "$1" && ./verify.sh >"$WORK/out.log" 2>&1)
  printf '%s' "$?"
}

# expect_detected <name> <mutator-command...>
expect_detected() {
  local name="$1"; shift
  CASES=$((CASES+1))
  local dir; dir="$(fresh_copy "case$CASES")"
  ( cd "$dir" && eval "$@" ) >/dev/null 2>&1
  local rc; rc="$(run_verify "$dir")"
  if [ "$rc" -ne 0 ]; then
    ok "$name -> verify.sh exited $rc (detected)"
  else
    bad "$name -> verify.sh exited 0; the corruption was NOT detected"
    printf '       (last lines of the corrupted run)\n'
    tail -5 "$WORK/out.log" | sed 's/^/       /'
  fi
}

say "mutation tests: each corruption MUST make verify.sh fail"
say ""

# --------------------------------------------------------------------------
# M1: corrupt the recorded PARI L-value transcript IN A DIGIT THE CERTIFIED
#      COMPUTATION RESOLVES (digit ~21 of 60).  The certified interval is
#      only ~4e-48 wide, so corrupting one of the LAST digits of PARI's
#      60-digit value would change nothing the check can see -- such a
#      mutation would prove nothing.  Corrupting an early digit is the
#      honest version of this test.
expect_detected "M1 corrupted PARI ellL1 transcript (resolved digit)" \
  "$PY -c \"
import re
p='data/pari-32a2.txt'
s=open(p).read()
s2=re.sub(r'(ellL1\\s*=\\s*0\\.655514388573029952616209)8974', r'\\g<1>8975', s)
assert s2!=s, 'M1 mutation did not apply'
open(p,'w').write(s2)
\""

# --------------------------------------------------------------------------
# M2: corrupt the recorded Cremona allbsd row (change the real period).
expect_detected "M2 corrupted Cremona allbsd real period" \
  "sed -i 's/5.24411510858424/5.24411510858425/' data/ecdata-32a2.txt"

# --------------------------------------------------------------------------
# M3: corrupt the certified L-value inside src/lvalue.py, in a way that
#      keeps the code syntactically valid and the arithmetic self-consistent:
#      the factor 2 in front of the sum becomes 3.
expect_detected "M3 certified L-value corrupted (the factor 2 becomes 3)" \
  "sed -i 's/    L_sum = cert.scale(total, 2)/    L_sum = cert.scale(total, 3)/' src/lvalue.py"

# --------------------------------------------------------------------------
# M3b: corrupt the certified PERIOD inside src/period.py the same way --
#      change the AGM route's numerator.  This must break the three-route
#      agreement check.
expect_detected "M3b certified period corrupted (AGM numerator 2*pi -> 3*pi)" \
  "sed -i 's/    return cert.div(cert.scale(cert.PI, 2), agm)/    return cert.div(cert.scale(cert.PI, 3), agm)/' src/period.py"

# --------------------------------------------------------------------------
# M4: corrupt the Tamagawa number in src/identity_data.py.
expect_detected "M4 corrupted Tamagawa number c_2 = 2 -> 4" \
  "sed -i 's/^TAMAGAWA_C2 = 2/TAMAGAWA_C2 = 4/' src/identity_data.py"

# --------------------------------------------------------------------------
# M5: THE CONVENTION MUTATION.  Change the period from the full real locus
#     to the identity component alone -- the classic subtle error -- and
#     require the guard in src/identity.py to fire.
expect_detected "M5 period convention switched to identity component" \
  "$PY - <<'PY'
import re, io
p = 'src/period.py'
s = open(p).read()
# make the main period computation return the identity-component period
s = s.replace('    return (lo, hi), diag', '    return (lo // 2, hi // 2), diag')
open(p,'w').write(s)
PY"

# --------------------------------------------------------------------------
# M6: a syntax-level corruption, to prove the harness does not silently
#     'pass' when a module cannot even be imported.
expect_detected "M6 broken import in src/period.py" \
  "printf 'this is not python(\n' >> src/period.py"

# --------------------------------------------------------------------------
# M7: WEAKEN the identity check by loosening its tolerance from 1e-40 to
#     1e-20.  This is the dangerous kind of edit: it does not break any
#     import, and it does not change the printed numbers, but it makes the
#     check much weaker.  The harness's own tamper test must catch it.
expect_detected "M7 identity tolerance loosened (1e-40 -> 1e-20)" \
  "sed -i 's/^TOL_UNITS = 10 \*\* 10$/TOL_UNITS = 10 ** 30/' src/identity.py"

# --------------------------------------------------------------------------
# M8: WEAKEN the three-route agreement check by loosening its tolerance.
expect_detected "M8 period route-agreement tolerance loosened (1e-40 -> 1e-20)" \
  "sed -i 's/^TOL_UNITS = 10 \*\* 10$/TOL_UNITS = 10 ** 30/' src/period.py"

# --------------------------------------------------------------------------
# M9: make the Ogg consistency control VACUOUS -- it always accepts.
#     This is the classic "a control that cannot fail is not a control"
#     corruption: the code still runs, still prints, and the numbers on
#     screen are unchanged.  The harness must notice that the guard has
#     been neutered, which it does by requiring the guard to REJECT
#     tampered invariants.
expect_detected "M9 Ogg consistency control made vacuous in src/tate.py" \
  "sed -i 's/^    return m == _n_components(res\[\"kodaira\"\])$/    return True/' src/tate.py"

# --------------------------------------------------------------------------
# M10: remove the a_n cross-check, so that point counting and the eta
#      product no longer have to agree.
expect_detected "M10 a_n cross-check removed from src/lvalue.py" \
  "sed -i 's/^    mismatches = \[n for n in range(1, cutoff + 1) if counting\[n\] != eta\[n\]\]/    mismatches = []/' src/lvalue.py"

# --------------------------------------------------------------------------
# M11: REINTRODUCE THE EXACT BUG THAT WAS PUBLISHED IN COMMIT a564c34.
#      The change-of-variables formula put the a1*t term in a3' instead of
#      a4', and carried a spurious "- 2 t".  That silently changes the
#      discriminant and produces WRONG Tamagawa numbers on the additive
#      branch at p >= 5.  This mutation must be caught by the regression
#      control added in verify.sh (delta invariance + the PARI oracle).
expect_detected "M11 the published a564c34 change-of-variables bug reintroduced" \
  "$PY - <<'PY'
p = 'src/tate.py'
s = open(p).read()
old = '''    return (a1, a2 + 3 * r, a3 + a1 * r + 2 * t,
            a4 + 2 * r * a2 + 3 * r * r - a1 * t,
            a6 + r * a4 + r * r * a2 + r ** 3 - a3 * t - t * t - a1 * r * t)'''
new = '''    return (a1, a2 + 3 * r, a3 + 2 * t, a4 - 2 * r * a2 + 3 * r * r - 2 * t,
            a6 + r * a4 + r * r * a2 + r ** 3 - t * a3 - t * t)'''
assert old in s, 'M11 mutation did not apply'
open(p, 'w').write(s.replace(old, new))
PY"

# --------------------------------------------------------------------------
# M12: corrupt the Gaussian Grossencharacter trace in src/odd_sha.py.
expect_detected "M12 corrupted Gaussian Grossencharacter trace in src/odd_sha.py" \
  "sed -i 's/trace_psi = 2 \* pi\[0\]/trace_psi = -2 * pi[0]/' src/odd_sha.py"

# --------------------------------------------------------------------------
# M13: corrupt the Hurwitz algebraic BSD ratio in src/odd_sha.py.
expect_detected "M13 corrupted Hurwitz ratio L(E,1)/Omega_1 in src/odd_sha.py" \
  "sed -i 's/l_over_omega_1 = Fraction(1, 4)/l_over_omega_1 = Fraction(1, 2)/' src/odd_sha.py"

# --------------------------------------------------------------------------
printf '\n=====================================================\n'
printf 'MUTATION TESTS: %d/%d corruptions detected\n' "$PASS" "$CASES"
if [ "$FAIL" -ne 0 ]; then
  printf 'MUTATION TESTS: %d corruption(s) SLIPPED THROUGH -- the harness is not trustworthy\n' "$FAIL"
  printf '=====================================================\n'
  exit 1
fi
printf '=====================================================\n'
exit 0
