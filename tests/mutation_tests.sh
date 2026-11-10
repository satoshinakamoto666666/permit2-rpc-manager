#!/usr/bin/env bash
# Negative / mutation tests for verify.sh (BSD Rung 1: curve 37a1).
#
# Each test copies the repo to a scratch directory, corrupts ONE specific fact,
# script, or transcript, and asserts that verify.sh FAILS.

set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if python -c "import sys; assert sys.version_info >= (3, 6)" >/dev/null 2>&1; then
    PY=python
else
    PY=python3
fi

pass=0
total=0

expect_fail() {
    local name="$1"; shift
    total=$((total + 1))
    rm -rf "$TMP/work"
    cp -r "$HERE" "$TMP/work"
    ( cd "$TMP/work" && "$@" )
    if ( cd "$TMP/work" && bash ./verify.sh >/dev/null 2>&1 ); then
        echo "MUTATION TEST FAILED (verify.sh unexpectedly passed): $name" >&2
        exit 1
    else
        echo "  [caught] $name"
        pass=$((pass + 1))
    fi
}

echo "Running mutation tests against verify.sh (37a1)..."

# M1: wrong torsion order (2 instead of 1) in identity_data.py
expect_fail "M1: TORS_ORDER = 2 instead of 1" \
    $PY -c '
p = "src/identity_data.py"
s = open(p).read().replace("TORS_ORDER = 1", "TORS_ORDER = 2")
open(p, "w").write(s)
'

# M2: wrong Tamagawa product (2 instead of 1) in identity_data.py
expect_fail "M2: TAMAGAWA_PRODUCT = 2 instead of 1" \
    $PY -c '
p = "src/identity_data.py"
s = open(p).read().replace("TAMAGAWA_PRODUCT = 1", "TAMAGAWA_PRODUCT = 2")
open(p, "w").write(s)
'

# M3: identity-component period (missing factor of 2 in AGM route)
expect_fail "M3: identity-component period in period.py (scale(PI, 1) instead of 2)" \
    $PY -c '
p = "src/period.py"
s = open(p).read().replace("div(scale(PI, 2), agm)", "div(scale(PI, 1), agm)", 1)
open(p, "w").write(s)
'

# M4: wrong duplication polynomial coefficient in height.py
expect_fail "M4: corrupted duplication polynomial Phi in height.py" \
    $PY -c '
p = "src/height.py"
s = open(p).read().replace("_scale_hi(_mul_hi(u, v3), 2)", "_scale_hi(_mul_hi(u, v3), 4)", 1)
open(p, "w").write(s)
'

# M5: wrong quadraticity divisor for 2P in height.py (mult_sq=3 instead of 4)
expect_fail "M5: wrong quadraticity divisor mult_sq=3 for 2P in height.py" \
    $PY -c '
p = "src/height.py"
s = open(p).read().replace("mult_sq=4", "mult_sq=3", 1)
open(p, "w").write(s)
'

# M6: wrong sign for a_37 (+1 instead of -1) in a_n.py
expect_fail "M6: wrong Euler factor a_37 = +1 in a_n.py" \
    $PY -c '
p = "src/a_n.py"
s = open(p).read().replace("return p + 1 - total", "return (1 if p == 37 else p + 1 - total)", 1)
open(p, "w").write(s)
'

# M7: corrupted Cremona ecdata Omega_E in data/ecdata-37a1.txt
expect_fail "M7: corrupted Omega_E in data/ecdata-37a1.txt" \
    $PY -c '
p = "data/ecdata-37a1.txt"
s = open(p).read().replace("ecdata_omega = 5.98691729", "ecdata_omega = 5.98691728")
open(p, "w").write(s)
'

# M8: corrupted Cremona ecdata Reg_E in data/ecdata-37a1.txt
expect_fail "M8: corrupted Reg_E in data/ecdata-37a1.txt" \
    $PY -c '
p = "data/ecdata-37a1.txt"
s = open(p).read().replace("ecdata_reg   = 0.0511114082", "ecdata_reg   = 0.0511114089")
open(p, "w").write(s)
'

# M9: remove OPEN disclosure from OPEN_REMAINDER.md
expect_fail "M9: OPEN disclosure removed from OPEN_REMAINDER.md" \
    $PY -c '
p = "OPEN_REMAINDER.md"
s = open(p).read().replace("OPEN", "SETTLED")
open(p, "w").write(s)
'

# M10: break convention control in identity.py
expect_fail "M10: broken convention control in identity.py" \
    $PY -c '
p = "src/identity.py"
s = open(p).read().replace("ratio_conn[0] <= 2 * S <= ratio_conn[1]", "ratio_conn[0] <= 1 * S <= ratio_conn[1]")
open(p, "w").write(s)
'

echo "MUTATION TESTS: $pass/$total corruptions detected"
