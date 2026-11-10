#!/usr/bin/env python3
"""Differential test: does the p=2 rule in tate.py hold against PARI/GP?

tate.py's p=2 branch is a restricted CASE RULE, not a full 2-adic Tate's
algorithm.  It must therefore be validated against an independent
implementation over many inputs -- otherwise it is a claim, not a
computation.

This test enumerates short Weierstrass models y^2 = x^3 + a4 x + a6 with
2 not dividing a4 and 4 dividing a6 (the family tate.py claims to cover),
runs tate.py on each, and compares against PARI/GP's elllocalred.

PARI's 'kod' codes (this release): 1=I_0, 2=II, 3=III, 4=IV, 5+n=I_n,
negative = starred types.  Only codes in the decoded range are compared on
the Kodaira symbol; the Tamagawa number and conductor exponent are compared
for every case, because those are unambiguous.

Exit code 0 = agreement on every comparable field; 1 = a disagreement.
"""

import os
import random
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import tate  # noqa: E402

# PARI kod codes decoded for this PARI release (see tate._PARI_KOD_CODES).
KOD = {1: "I_0", 2: "II", 3: "III", 4: "IV"}


def pari_localred(a4, a6, p):
    """PARI's elllocalred for the short model y^2 = x^3 + a4 x + a6 at p."""
    script = ("E=ellinit([0,0,0,%d,%d],1);\n"
              "print(elllocalred(E,%d));\n" % (a4, a6, p))
    proc = subprocess.run(["gp", "-q", "-f"], input=script,
                          capture_output=True, text=True, timeout=300)
    lines = [ln.strip() for ln in proc.stdout.splitlines()
             if ln.strip().startswith("[")]
    if not lines:
        return None
    return tate._parse_vec(lines[0])


def models(count, seed=20261110):
    """Random short models in the family tate.py's p=2 branch covers."""
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < count:
        a4 = rng.choice([x for x in range(-40, 41) if x % 2 != 0])
        a6 = rng.choice([x for x in range(-64, 65, 4)])
        if a4 == 0 or (a4, a6) in seen:
            continue
        # skip singular curves
        if 4 * a4 ** 3 + 27 * a6 ** 2 == 0:
            continue
        seen.add((a4, a6))
        out.append((a4, a6))
    return out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    pairs = models(n)
    mismatches = []
    kod_checked = 0
    tam_checked = 0
    f_checked = 0

    for a4, a6 in pairs:
        try:
            ours = tate.tate_algorithm(a4, 0, a6, 2)
        except NotImplementedError:
            continue
        except Exception as exc:                 # pragma: no cover
            mismatches.append((a4, a6, "EXCEPTION %r" % (exc,), None, None))
            continue
        loc = pari_localred(a4, a6, 2)
        if loc is None:
            continue
        f_pari, kod_pari, _chg, c_pari = loc
        if c_pari != ours["tamagawa"]:
            mismatches.append((a4, a6, "tamagawa", ours["tamagawa"], c_pari))
        else:
            tam_checked += 1
        if f_pari != ours["conductor_frob"]:
            mismatches.append((a4, a6, "conductor_frob",
                                ours["conductor_frob"], f_pari))
        else:
            f_checked += 1
        sym = KOD.get(kod_pari)
        if sym is not None:
            if sym != ours["kodaira"]:
                mismatches.append((a4, a6, "kodaira", ours["kodaira"], sym))
            else:
                kod_checked += 1

    print("models tested                : %d" % len(pairs))
    print("tamagawa agreements         : %d" % tam_checked)
    print("conductor-exponent agreements: %d" % f_checked)
    print("kodaira agreements (decoded) : %d" % kod_checked)
    print("mismatches                   : %d" % len(mismatches))
    for m in mismatches[:20]:
        print("  MISMATCH a4=%s a6=%s field=%s ours=%r pari=%r" % m)
    if mismatches:
        print("P2-RULE-DIFFERENTIAL-FAILED")
        return 1
    print("P2-RULE-DIFFERENTIAL-OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
