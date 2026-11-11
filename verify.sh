#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1

echo "============================================================================"
echo "VERIFYING BSD RANK-0 FAMILY (CONDUCTOR N <= 100, 284 CURVES / 76 ISOGENIES)"
echo "============================================================================"

echo "[Step 1/7] Checking repository layout & required epistemic documents..."
for f in README.md PROOF.md CLAIMS.md OPEN_REMAINDER.md FAMILY_REPORT.md data/allbsd_upto_100.txt src/cert.py src/tate.py src/torsion.py src/period.py src/lval.py src/family_check.py; do
    if [ ! -s "$f" ]; then
        echo "FAIL: Missing or empty required file: $f"
        exit 1
    fi
done
for tag in "PROVED" "COMPUTED" "CITED" "| \`OPEN\` |"; do
    if ! grep -Fq "$tag" CLAIMS.md; then
        echo "FAIL: Missing required epistemic status tag $tag in CLAIMS.md"
        exit 1
    fi
done
echo "  [PASS] All required files and epistemic tags present."

echo "[Step 2/7] Auditing src/cert.py for banned floating-point or external imports..."
python -c "
import ast, sys
tree = ast.parse(open('src/cert.py', encoding='utf-8').read())
banned = {'math', 'cmath', 'decimal', 'fractions', 'numpy', 'scipy', 'mpmath', 'sympy', 'gmpy2'}
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for n in node.names:
            if n.name.split('.')[0] in banned:
                sys.exit(f'Banned import in cert.py: {n.name}')
    elif isinstance(node, ast.ImportFrom):
        if node.module and node.module.split('.')[0] in banned:
            sys.exit(f'Banned from-import in cert.py: {node.module}')
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'float':
        sys.exit('Banned float() call in cert.py')
    elif isinstance(node, ast.Constant) and isinstance(node.value, float):
        sys.exit(f'Banned float literal in cert.py: {node.value}')
print('  [PASS] src/cert.py AST audit passed (100% pure Python int).')
"

echo "[Step 3/7] Running fixed-point interval arithmetic self-tests (src/cert.py)..."
python src/cert.py

echo "[Step 4/7] Running full 284-curve BSD counterexample hunt & family verification (src/family_check.py)..."
python src/family_check.py

echo "[Step 5/7] Auditing FAMILY_REPORT.md completeness (all 284 rank-0 + 22 rank-1 curves listed)..."
python - <<'PY'
import sys
txt = open("FAMILY_REPORT.md", encoding="utf-8").read()
raw = [l.split() for l in open("data/allbsd_upto_100.txt", encoding="utf-8") if l.strip()]
for parts in raw:
    lbl = f"| `{parts[0]}{parts[1]}{parts[2]}` |"
    if lbl not in txt:
        sys.exit(f"Missing curve {lbl} in FAMILY_REPORT.md")
if "| `66b3` | `[1,1,1,-352,-2689]` | `2` | `1` |" not in txt or "**`4`**" not in txt:
    sys.exit("Missing 66b3 Sha=4 row in FAMILY_REPORT.md")
print("  [PASS] FAMILY_REPORT.md contains all 306 curves (284 rank-0 + 22 rank-1) and 66b3 Sha_an=4 spotlight.")
PY

echo "[Step 6/7] Checking epistemic boundary alignment between CLAIMS.md and OPEN_REMAINDER.md..."
if ! grep -q "Kolyvagin" OPEN_REMAINDER.md || ! grep -q "Millennium" OPEN_REMAINDER.md; then
    echo "FAIL: OPEN_REMAINDER.md missing required CITED/OPEN boundary disclosures"
    exit 1
fi
echo "  [PASS] Epistemic boundary disclosures verified."

echo "[Step 7/7] Checking documentation and code hygiene..."
if grep -rniE '\b(todo|fixme|tbd|coming soon|unimplemented)\b' README.md PROOF.md CLAIMS.md OPEN_REMAINDER.md FAMILY_REPORT.md src/*.py; then
    echo "FAIL: Found unfinished markers in repository"
    exit 1
fi
echo "  [PASS] Hygiene check passed."

echo "============================================================================"
echo "ALL 7 VERIFICATION STEPS PASSED (284 RANK-0 CURVES, CONDUCTOR N <= 100)"
echo "============================================================================"
