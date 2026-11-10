#!/usr/bin/env python3
"""Regression test for the change-of-variables formulas in src/tate.py.

Background.  The p >= 5 branch of Tate's algorithm moves the singular point of
the reduced cubic to the origin with a translation
(x = x' + r, y = y' + t).  If the coefficients after that translation are
wrong, the discriminant changes, and the valuations the additive branch reads
off are wrong -- so c_p and f_p come out wrong.

Two independent controls:

  A. DELTA INVARIANCE (no PARI needed).  The discriminant is invariant under a
     translation (u = 1, s = 0), so for ANY model and ANY (r, t):
         Delta(model) == Delta(translate(model, r, t))
     A model with a1 != 0 is essential: with a1 = 0 the erroneous a1*t term
     does not show up, and a control built only from short Weierstrass models
     passes on broken code.

  B. PARI CROSS-CHECK (live oracle).  For a fixed list of models whose
     reduction at the stated prime is ADDITIVE (the only branch that calls
     the translation), compare c_p and f_p against PARI/GP's elllocalred.
     PARI is an implementation that shares no code with this file, so this is
     ground truth, not a self-check.

Control A is the one that must not depend on PARI being installed.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TATE = os.path.join(HERE, os.pardir, "src", "tate.py")

spec = importlib.util.spec_from_file_location("tate", TATE)
tate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tate)

failures = []

# ---------------------------------------------------------------- control A
# (model, r, t).  Models with a1 != 0 are the point of this control.
TRANSLATION_CASES = [
    ((0, 0, 0, -1, 0), 1, 1),      # our own curve: a1 = 0
    ((1, 0, 0, -1, 0), 1, 1),      # a1 != 0
    ((1, 2, 3, -4, 5), 1, 1),
    ((1, 2, 3, -4, 5), 2, 3),
    ((3, -1, 2, 7, -6), 1, 0),
    ((2, 1, 4, -3, 9), 4, 2),
    ((-1, 2, 4, -11, -1), 5, 7),
    ((3, 3, -1, 10, 7), 2, 2),
]

for model, r, t in TRANSLATION_CASES:
    d_before = tate.invariants(*model)[6]
    d_after = tate.invariants(*tate._translate(model, r, t))[6]
    if d_before != d_after:
        failures.append(
            "A: Delta changed under translation for model=%s r=%d t=%d "
            "(%d -> %d) -- the change-of-variables formula is wrong"
            % (model, r, t, d_before, d_after))
print("A: delta-invariance under translation: %d cases checked"
      % len(TRANSLATION_CASES))

# ---------------------------------------------------------------- control B
# Models with ADDITIVE reduction at p >= 5 (c4 == 0 mod p, Delta == 0 mod p).
# The first three are cases where the previously published formula produced a
# WRONG Tamagawa number; the rest are cases it could not attempt at all.
ADDITIVE_CASES = [
    ((-1, 0, -4, 5, 3), 5),
    ((1, -1, 3, -11, 15), 5),
    ((1, -2, -2, -6, -12), 5),
    ((2, -1, 0, 5, 0), 5),
    ((3, 2, -4, 4, -8), 5),
    ((1, 0, 4, 5, 13), 5),
    ((-1, 4, 0, 9, -4), 11),
    ((0, -2, -3, -10, -9), 17),
    ((0, 2, 3, 11, 1), 29),
    ((1, -1, -3, 8, -7), 101),
]

if shutil.which("gp") is None:
    print("B: PARI cross-check SKIPPED (no 'gp' on PATH) -- "
          "control A still ran")
else:
    script = "".join(
        "print(elllocalred(ellinit([%d,%d,%d,%d,%d]),%d));" % (m + (p,))
        for m, p in ADDITIVE_CASES) + "\n"
    proc = subprocess.run(["gp", "-q", "-f"], input=script, capture_output=True,
                          text=True, timeout=600)
    lines = [ln.strip() for ln in proc.stdout.splitlines()
             if ln.strip().startswith("[")]
    if len(lines) != len(ADDITIVE_CASES):
        failures.append("B: PARI returned %d lines for %d cases -- the oracle "
                        "failed, so this control could not run"
                        % (len(lines), len(ADDITIVE_CASES)))
    else:
        checked = 0
        for (m, p), line in zip(ADDITIVE_CASES, lines):
            loc = json.loads(line)
            f_pari, c_pari = loc[0], loc[3]
            try:
                res = tate._tate_p_ge_5(tate.minimise(m, p), p)
            except NotImplementedError:
                continue
            checked += 1
            if res["tamagawa"] != c_pari:
                failures.append("B: c_p wrong for model=%s p=%d: ours=%s PARI=%s"
                                % (m, p, res["tamagawa"], c_pari))
            if res["conductor_frob"] != f_pari:
                failures.append("B: f_p wrong for model=%s p=%d: ours=%s PARI=%s"
                                % (m, p, res["conductor_frob"], f_pari))
        print("B: PARI cross-check on the additive branch: %d/%d cases ran"
              % (checked, len(ADDITIVE_CASES)))

# ---------------------------------------------------------------- verdict
if failures:
    for f in failures:
        print("FAIL:", f)
    print("TATE-TRANSLATION-CONTROL: %d FAILURE(S)" % len(failures))
    sys.exit(1)
print("TATE-TRANSLATION-CONTROL-OK")
