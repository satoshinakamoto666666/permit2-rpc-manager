#!/usr/bin/env bash
# End-to-end verification harness for the BSD Rung 1 (37a1) certificate.
# Exits non-zero on the first failed check.

set -euo pipefail
cd "$(dirname "$0")"

if python -c "import sys; assert sys.version_info >= (3, 6)" >/dev/null 2>&1; then
    PY=python
else
    PY=python3
fi

fail() { echo "VERIFY FAILED: $*" >&2; exit 1; }
step() { printf '\n==> %s\n' "$*"; }

# ---- 1. Required files and honesty disclosures -------------------------------
step "1/9  Required files and honesty disclosures"
for f in README.md PROOF.md CLAIMS.md OPEN_REMAINDER.md \
         src/cert.py src/invariants.py src/height.py src/period.py \
         src/a_n.py src/lprime.py src/identity.py src/identity_data.py \
         data/ecdata-37a1.txt; do
    [ -s "$f" ] || fail "missing or empty file: $f"
done

grep -q "OPEN" OPEN_REMAINDER.md || fail "OPEN_REMAINDER.md does not state what is OPEN"
grep -q "CITED" CLAIMS.md        || fail "CLAIMS.md does not mark CITED claims"
grep -q "PROVED" CLAIMS.md       || fail "CLAIMS.md does not mark PROVED claims"
grep -q "COMPUTED" CLAIMS.md     || fail "CLAIMS.md does not mark COMPUTED claims"
echo "ok"

# ---- 2. Invariants, local reduction at 37, torsion = 1, generator P=(0,0) ----
step "2/9  Invariants, local reduction at p=37, torsion = 1, generator multiples"
out="$($PY src/invariants.py)"
echo "$out"
echo "$out" | grep -q "INVARIANTS-OK" || fail "invariants.py did not report INVARIANTS-OK"

# ---- 3. Regulator Reg_E = h_hat(P) (three independent routes) ----------------
step "3/9  Regulator Reg_E = h_hat(P) (three certified routes)"
out="$($PY src/height.py)"
echo "$out"
echo "$out" | grep -q "routes agree                  : True" || fail "height routes disagree"
echo "$out" | grep -q "HEIGHT-OK" || fail "height.py did not report HEIGHT-OK"

# ---- 4. Real period Omega_E (three independent routes) -----------------------
step "4/9  Real period Omega_E (AGM, Landen-hypergeometric, Jacobi theta)"
out="$($PY src/period.py)"
echo "$out"
echo "$out" | grep -q "routes agree             : True" || fail "period routes disagree"
echo "$out" | grep -q "PERIOD-OK" || fail "period.py did not report PERIOD-OK"

# ---- 5. Fourier coefficients a_n (two independent methods) -------------------
step "5/9  Fourier coefficients a_n (Weierstrass counting vs Legendre sum, n <= 160)"
out="$($PY src/a_n.py 160)"
echo "$out"
echo "$out" | grep -q "method A vs method B mismatches: NONE" || fail "a_n methods disagree"
echo "$out" | grep -q "AN-OK" || fail "a_n.py did not report AN-OK"

# ---- 6. Derivative L'(E, 1) (certified interval + Stieltjes CF overlap) ------
step "6/9  L'(E, 1) (certified E_1 series + Stieltjes CF overlap + Deligne tail)"
out="$($PY src/lprime.py 135)"
echo "$out"
echo "$out" | grep -q "LPRIME-OK" || fail "lprime.py did not report LPRIME-OK"

# ---- 7. External cross-check against Cremona's ecdata transcript -------------
step "7/9  External cross-check against recorded Cremona ecdata (data/ecdata-37a1.txt)"
$PY - <<'PYEOF'
import re, sys
sys.path.insert(0, "src")
from cert import to_decimal
from period import omega_certified
from height import reg_certified
from lprime import lprime_certified

with open("data/ecdata-37a1.txt") as fh:
    ec_txt = fh.read()

def grab(pattern):
    m = re.search(pattern, ec_txt)
    assert m, "could not parse %r from data/ecdata-37a1.txt" % pattern
    return m.group(1)

ec_omega = grab(r"ecdata_omega\s*=\s*([0-9.]+)")
ec_reg   = grab(r"ecdata_reg\s*=\s*([0-9.]+)")
ec_l1p   = grab(r"ecdata_l1p\s*=\s*([0-9.]+)")

# Also verify the verbatim curvedata and allbsd lines are intact in the file
assert "37 a 1 [0,0,1,-1,0] 1 1 1 5.98691729246392 0.305999773834052 0.0511114082399688 1.00000000000000" in ec_txt
assert ec_omega in ec_txt and ec_reg in ec_txt and ec_l1p in ec_txt

om_iv, _, _, _ = omega_certified()
rg_iv, _, _, _ = reg_certified()
lp_iv, _, _    = lprime_certified(135)

om_lo, om_hi = to_decimal(om_iv, 45)
rg_lo, rg_hi = to_decimal(rg_iv, 45)
lp_lo, lp_hi = to_decimal(lp_iv, 45)

assert om_lo[:28] == om_hi[:28] == ec_omega[:28], (
    "Omega_E mismatch vs ecdata: %s vs %s" % (om_lo[:30], ec_omega[:30]))
assert rg_lo[:30] == rg_hi[:30] == ec_reg[:30], (
    "Reg_E mismatch vs ecdata: %s vs %s" % (rg_lo[:32], ec_reg[:32]))
assert lp_lo[:30] == lp_hi[:30] == ec_l1p[:30], (
    "L'(E,1) mismatch vs ecdata: %s vs %s" % (lp_lo[:32], ec_l1p[:32]))

print("  Omega_E agrees with ecdata to 28 digits :", om_lo[:30])
print("  Reg_E   agrees with ecdata to 30 digits :", rg_lo[:32])
print("  L'(E,1) agrees with ecdata to 30 digits :", lp_lo[:32])
PYEOF

# ---- 8. The full rank-1 BSD identity + convention control --------------------
step "8/9  The full rank-1 BSD leading-coefficient identity (src/identity.py)"
out="$($PY src/identity.py)"
echo "$out"
echo "$out" | grep -q "implied #Sha (integer)         : 1" || fail "implied #Sha is not 1"
echo "$out" | grep -q "IDENTITY-OK" || fail "identity.py did not report IDENTITY-OK"

# ---- 9. Liveness of all internal mutation controls ---------------------------
step "9/9  Liveness of internal mutation controls"
$PY - <<'PYEOF'
import sys
sys.path.insert(0, "src")
import invariants, height, period, lprime

assert invariants.mutation_control(), "invariants.mutation_control failed"
assert height.mutation_control(), "height.mutation_control failed"
assert period.mutation_control(), "period.mutation_control failed"
assert lprime.mutation_control(), "lprime.mutation_control failed"
print("  all 4 module mutation controls alive and passing")
PYEOF

printf '\nALL 9 VERIFICATION STEPS PASSED (BSD RUNG 1: 37a1)\n'
