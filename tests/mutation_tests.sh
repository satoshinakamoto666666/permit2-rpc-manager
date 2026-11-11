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
echo "MUTATION TEST SUITE: BSD MILLENNIUM SUITE (N <= 100, 12 ADVERSARIAL CHECKS)"
echo "============================================================================"

PASSED=0
TOTAL=12

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
run_mutation "M08" "src/euler_kato_sha.py" "assert sel_phi == [1, -1]" "assert sel_phi == [1, 2]" "Corrupt 2-isogeny Selmer group Sel^(phi)(32a2) in src/euler_kato_sha.py"
run_mutation "M09" "src/euler_kato_sha.py" "if ord_p_sha != 0:" "if ord_p_sha == 0:" "Invert odd-primary Kolyvagin/Kato Sha valuation check in src/euler_kato_sha.py"
run_mutation "M10" "src/rank1_37a1.py" "assert n_lo == n_hi == 1" "assert n_lo == n_hi == 4" "Corrupt rank-1 37a1 implied Sha_an = 1 check in src/rank1_37a1.py"
run_mutation "M11" "src/family_check.py" "num_sha = l_iv * (tors_ord * tors_ord)" "num_sha = l_iv * tors_ord" "Replace (#E(Q)_tors)^2 with #E(Q)_tors in BSD Sha_an formula"
run_mutation "M12" "CLAIMS.md" "| \`OPEN\` |" "| \`CLOSED_ALL\` |" "Remove OPEN epistemic tag row from CLAIMS.md"

echo "----------------------------------------------------------------------------"
echo "Re-running verify.sh on restored clean working tree..."
bash ./verify.sh >/dev/null
echo "MUTATION TESTS: ${PASSED}/${TOTAL} corruptions detected"
echo "============================================================================"
