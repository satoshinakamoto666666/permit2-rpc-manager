#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
echo "VERIFYING BSD MILLENNIUM SUITE (CONDUCTOR N <= 100, 306 CURVES: 284 R0 + R1)"
echo "============================================================================"

echo "[Step 1/8] Checking repository layout & required epistemic documents..."
for f in README.md THEOREM_AND_PROOF.md PROOF.md CLAIMS.md OPEN_REMAINDER.md FAMILY_REPORT.md \
         data/allbsd_upto_100.txt src/cert.py src/tate.py src/torsion.py src/period.py \
         src/lval.py src/euler_kato_sha.py src/rank1_37a1.py src/family_check.py; do
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

echo "[Step 2/8] Auditing core modules for banned floating-point or external imports..."
$PY - <<'PY'
import ast, sys
banned = {'math', 'cmath', 'decimal', 'fractions', 'numpy', 'scipy', 'mpmath', 'sympy', 'gmpy2'}
for fname in ('src/cert.py', 'src/tate.py', 'src/period.py', 'src/lval.py', 'src/euler_kato_sha.py', 'src/rank1_37a1.py', 'src/family_check.py'):
    tree = ast.parse(open(fname, encoding='utf-8').read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split('.')[0] in banned:
                    sys.exit(f'Banned import in {fname}: {n.name}')
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in banned:
                sys.exit(f'Banned from-import in {fname}: {node.module}')
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'float':
            sys.exit(f'Banned float() call in {fname}')
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            sys.exit(f'Banned float literal in {fname}: {node.value}')
print('  [PASS] AST audit passed (100% pure Python int across 7 core verification modules).')
PY

echo "[Step 3/8] Running per-module self-tests (cert.py, tate.py, torsion.py, period.py, lval.py)..."
$PY src/cert.py
$PY src/tate.py
$PY src/torsion.py
$PY src/period.py
$PY src/lval.py

echo "[Step 4/8] Running 2-isogeny descent (32a2), 66b redistribution & 284-curve Kolyvagin/Kato Euler system audit..."
$PY src/euler_kato_sha.py

echo "[Step 5/8] Running certified rank-1 BSD regulator & L'(E,1) verification for curve 37a1..."
$PY src/rank1_37a1.py

echo "[Step 6/8] Running full 284-curve BSD counterexample hunt & family verification (src/family_check.py)..."
$PY src/family_check.py

echo "[Step 7/8] Auditing FAMILY_REPORT.md completeness (all 284 rank-0 + 22 rank-1 curves listed)..."
$PY - <<'PY'
import sys
txt = open("FAMILY_REPORT.md", encoding="utf-8").read()
raw = [l.split() for l in open("data/allbsd_upto_100.txt", encoding="utf-8") if l.strip()]
for parts in raw:
    lbl = f"| `{parts[0]}{parts[1]}{parts[2]}` |"
    if lbl not in txt:
        sys.exit(f"Missing curve {lbl} in FAMILY_REPORT.md")
if "| `66b3` | `[1,1,1,-352,-2689]` | `2` | `1` |" not in txt or "**`4`**" not in txt:
    sys.exit("Missing 66b3 Sha=4 row in FAMILY_REPORT.md")
for req in ("**306** (93 isogeny classes)", "**284** (76 isogeny classes)", "**22** (17 isogeny classes)", "1.102192530121609"):
    if req not in txt:
        sys.exit(f"Missing required corrected figure in FAMILY_REPORT.md: {req}")
for bad in ("84 isogeny", "96 isogeny", "8 isogeny", "20 isogeny", "0.453121417471989"):
    if bad in txt:
        sys.exit(f"Stale incorrect figure found in FAMILY_REPORT.md: {bad}")
print("  [PASS] FAMILY_REPORT.md contains all 306 curves (93 isogeny classes: 284 rank-0 / 76 classes + 22 rank-1 / 17 classes) and 66b3 spotlight (L(66b,1)=1.102192530121609, Sha_an=4).")
PY

echo "[Step 8/8] Checking epistemic boundary alignment and repository hygiene..."
if ! grep -q "Kolyvagin" OPEN_REMAINDER.md || ! grep -q "Millennium" OPEN_REMAINDER.md; then
    echo "FAIL: OPEN_REMAINDER.md missing required CITED/OPEN boundary disclosures"
    exit 1
fi
if grep -rniE '\b(todo|fixme|tbd|coming soon|unimplemented)\b' README.md THEOREM_AND_PROOF.md PROOF.md CLAIMS.md OPEN_REMAINDER.md FAMILY_REPORT.md src/*.py; then
    echo "FAIL: Found unfinished markers in repository"
    exit 1
fi
echo "  [PASS] Epistemic boundary and hygiene checks passed."

echo "============================================================================"
echo "ALL 8 VERIFICATION STEPS PASSED (BSD MILLENNIUM SUITE: N <= 100, 306 CURVES)"
echo "============================================================================"
