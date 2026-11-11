#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="src"

if python -c "import sys; assert sys.version_info >= (3, 6)" >/dev/null 2>&1; then
    PY=python
else
    PY=python3
fi

echo "============================================================================"
echo "MUTATION TEST SUITE: BSD RANK-0 FAMILY (N <= 100)"
echo "============================================================================"

PASSED=0
TOTAL=10

run_mutation() {
    local id="$1"
    local file="$2"
    local target="$3"
    local replacement="$4"
    local desc="$5"

    $PY - "$file" "$target" "$replacement" <<'PY'
import sys
path, tgt, rep = sys.argv[1], sys.argv[2], sys.argv[3]
data = open(path, "r", encoding="utf-8").read()
if tgt not in data:
    sys.exit(f"Target string not found in {path}: {tgt}")
open(path + ".bak", "w", encoding="utf-8").write(data)
open(path, "w", encoding="utf-8").write(data.replace(tgt, rep, 1))
PY

    if bash ./verify.sh >/dev/null 2>&1; then
        mv "${file}.bak" "$file"
        echo "  [FAIL] $id ($desc): verify.sh unexpectedly PASSED on mutated code!"
        exit 1
    else
        mv "${file}.bak" "$file"
        echo "  [KILLED] $id: $desc"
        PASSED=$((PASSED + 1))
    fi
}

run_mutation "M01" "src/cert.py" "16 * a5_lo - 4 * a239_hi" "16 * a5_lo - 3 * a239_hi" "Corrupt Machin pi formula in src/cert.py"
run_mutation "M02" "src/tate.py" "return f\"I{n}_split\", n" "return f\"I{n}_split\", n + 1" "Corrupt split multiplicative Tamagawa number c_p = n in src/tate.py"
run_mutation "M03" "src/tate.py" "return \"I0*\", 1 + len(roots_Fp)" "return \"I0*\", 2 + len(roots_Fp)" "Corrupt Kodaira I0* Tamagawa formula in src/tate.py"
run_mutation "M04" "src/torsion.py" "K = 2 * c6 + 432 * W * W" "K = 2 * c6 + 108 * W * W" "Corrupt Lutz-Nagell depressed cubic constant 432*W^2 in src/torsion.py"
run_mutation "M05" "src/period.py" "num_iv = 4 * pi_iv * sqrt3_iv" "num_iv = 2 * pi_iv * sqrt3_iv" "Halve real period numerator 4*pi*sqrt(3) in src/period.py"
run_mutation "M06" "src/lval.py" "return p + 1 - cnt" "return p - 1 - cnt" "Corrupt Frobenius trace a_p = p + 1 - #E(F_p) in src/lval.py"
run_mutation "M07" "src/lval.py" "val_iv = 2 * total" "val_iv = total" "Drop factor of 2 in functional-equation series for L(E, 1) in src/lval.py"
run_mutation "M08" "src/family_check.py" "num_sha = l_iv * (tors_ord * tors_ord)" "num_sha = l_iv * tors_ord" "Replace (#E(Q)_tors)^2 with #E(Q)_tors in BSD Sha_an formula"
run_mutation "M09" "src/family_check.py" "nontrivial_sha[0][4] == 4" "nontrivial_sha[0][4] == 1" "Corrupt non-trivial Sha_an(66b3) = 4 check in src/family_check.py"
run_mutation "M10" "CLAIMS.md" "| \`OPEN\` |" "| \`CLOSED_ALL\` |" "Remove OPEN epistemic tag row from CLAIMS.md"

echo "----------------------------------------------------------------------------"
echo "Re-running verify.sh on restored clean working tree..."
bash ./verify.sh >/dev/null
echo "MUTATION TESTS: ${PASSED}/${TOTAL} corruptions detected"
echo "============================================================================"
