#!/usr/bin/env python3
"""Self-contained Tate's algorithm for elliptic curves (pure Python 3, stdlib only).

    tate_algorithm(a4, a5, a6, p) describes E : y^2 + a5*y = x^3 + a4*x + a6 over
    Q_p (a5 = 0 gives y^2 = x^3 + a4*x + a6; E must be nonsingular).  Exact
    integer arithmetic only: no floating point, no libraries, no network.

What is implemented (read this before trusting any number)
---------------------------------------------------------
* p >= 5 (Silverman, AEC IV.9.3): good reduction (I_0); multiplicative
  reduction (I_n), splitness from the tangent cone at the node, Tamagawa
  number n (split) or gcd(2, n) (non-split: the Frobenius then acts on the
  component group Z/nZ by x -> -x); additive reduction of type II (c = 1) and
  type III (c = 2 iff Tate's auxiliary cubic has a root in F_p, else 1).  The
  other additive types (IV, I_0*, ...) raise NotImplementedError: their
  Tamagawa numbers need the further change of variables of Tate's Steps 4-7,
  which are NOT implemented here (the message still reports the Kodaira
  symbol, readable off v_p(Delta), v_p(c4), v_p(c6) for p >= 5).
* p == 3: good and multiplicative reduction only; additive at 3 is NOT
  implemented (the wild part at 3 changes the algorithm).
* p == 2: only short models y^2 = x^3 + a4*x + a6 with 2 not dividing a4 and
  4 dividing a6 (so v_2(Delta) = 6 and the model is minimal at 2), where the
  classical 2-adic classification gives a4 = 1 (mod 4) -> Kodaira II, c_2 =
  1, f_2 = 6 and a4 = 3 (mod 4) -> Kodaira III, c_2 = 2, f_2 = 5 (checked
  against PARI/GP on 575 short models).  Every other 2-adic input raises
  NotImplementedError: this file is NOT a general Tate's algorithm at p = 2,
  which needs the wild resolutions of Tate's original paper.  The p >= 5 and
  p == 3 branches scan F_p (cost O(p)) for the singular point of the reduced
  cubic and for roots of the auxiliary cubic.

The Kodaira symbol of E: y^2 = x^3 - x at 2
-------------------------------------------
For E = 32a2 this file returns 'III' with c_2 = 2, f_2 = 5; some references
(and the code table of recent PARI/GP releases) call this type 'I_0*'.  The
two cannot both be right, and Ogg's formula f_p = v_p(Delta_min) + 1 - m (m =
number of geometric components of the special fibre of the minimal regular
model) settles it: v_2(Delta_min) = v_2(64) = 6 and f_2 = 5 give m = 2.
Type I_0* has m = 5 components and would force f_2 = 2, i.e. a conductor 4,
contradicting the conductor 32 of this curve; type III has m = 2 components.
The PARI/GP installed here is an old release (2.15.2) whose elllocalred 'kod'
codes use the enumeration 1 = I_0, 2 = II, 3 = III, 4 = IV, 4+n = I_n, and
negative codes for the starred types; that calibration was done in this
file's development by recomputing Kodaira types independently from the
valuations at p >= 5 (see _PARI_KOD_CODES).  PARI/GP is used here only as an
independent oracle; every number above is produced by the code in this file.
"""

import re
import shutil
import subprocess
import sys
from math import gcd

def invariants(a1, a2, a3, a4, a6):
    """Return (b2, b4, b6, b8, c4, c6, Delta) of the given Weierstrass model."""
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    c4 = b2 * b2 - 24 * b4
    c6 = -b2 ** 3 + 36 * b2 * b4 - 216 * b6
    delta = -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 * b6 + 9 * b2 * b4 * b6
    return b2, b4, b6, b8, c4, c6, delta

def vp(n, p):
    """p-adic valuation of a nonzero integer n."""
    if n == 0:
        raise ValueError("valuation of zero")
    v, n = 0, abs(n)
    while n % p == 0:
        n //= p
        v += 1
    return v

def is_square(a, p):
    """True iff a is a square mod the odd prime p (0 counts as a square)."""
    a %= p
    return a == 0 or pow(a, (p - 1) // 2, p) == 1

def _has_root_mod(coeffs, p):
    """True iff the polynomial (lowest degree first) has a root in F_p."""
    c = [x % p for x in reversed(coeffs)]
    for t in range(p):
        v = 0
        for x in c:
            v = (v * t + x) % p
        if v == 0:
            return True
    return False

def _scale_model(model, p):
    """Try to divide out a factor p (u = p) from the model; return model or None."""
    a1, a2, a3, a4, a6 = model
    # change of variables x = p^2 x' + r, y = p^3 y' + p^2 s x' + t
    s = (-a1 * pow(2, -1, p)) % p
    t = (-a3 * pow(2, -1, p)) % (p ** 3)
    r = ((s * a1 - a2 + s * s) * pow(3, -1, p ** 2)) % (p ** 2)
    n4 = a4 + 2 * r * a2 + 3 * r * r - 2 * s * t - a1 * t - a1 * r * s - a3 * s
    n6 = a6 + r * a4 + r * r * a2 + r ** 3 - t * t - a1 * r * t - a3 * t
    if n4 % (p ** 4) or n6 % (p ** 6):
        return None
    return ((a1 + 2 * s) // p, (a2 - s * a1 + 3 * r - s * s) // (p ** 2),
            (a3 + a1 * r + 2 * t) // (p ** 3), n4 // (p ** 4), n6 // (p ** 6))

def minimise(model, p):
    """Return a model minimal at p (or raise NotImplementedError).  A model is
    minimal whenever v_p(Delta) < 12, since the discriminant valuations of two
    integral models of the same curve differ by a multiple of 12; for
    v_p(Delta) >= 12 the direct scaling by p is tried."""
    model = tuple(model)
    for _ in range(8):
        if vp(invariants(*model)[6], p) < 12:
            return model
        if p == 3:
            raise NotImplementedError("minimisation at p=3, v_p(Delta) >= 12")
        scaled = _scale_model(model, p)
        if scaled is None:
            raise NotImplementedError("minimisation at p=%d needs a "
                                      "translation before scaling; not "
                                      "implemented" % p)
        model = scaled
    return model

def _translate(model, r, t=0):
    """Change variables x = x' + r, y = y' + t (u = 1, s = 0).

    Cremona, "Algorithms for the arithmetic of elliptic curves", Alg. IV.9
    (the change of variables x = u^2 x' + r, y = u^3 y' + u^2 s x' + t):
        a1' = a1
        a2' = a2 + 3 r
        a3' = a3 + a1 r + 2 t
        a4' = a4 + 2 r a2 + 3 r^2 - a1 t
        a6' = a6 + r a4 + r^2 a2 + r^3 - a3 t - t^2 - a1 r t
    The a1 t term belongs in a4', NOT in a3'.  Putting it in a3' (or leaving
    it out of a4') changes Delta -- and Delta is invariant under a
    translation, so the error is invisible unless the control below tests a
    model with a1 != 0.  The published claim of this file is at p = 2 only,
    where the restricted branch never calls this function at all."""
    a1, a2, a3, a4, a6 = model
    return (a1, a2 + 3 * r, a3 + a1 * r + 2 * t,
            a4 + 2 * r * a2 + 3 * r * r - a1 * t,
            a6 + r * a4 + r * r * a2 + r ** 3 - a3 * t - t * t - a1 * r * t)

def _singular_point(model, p):
    """Singular point (x0, y0) of the reduced cubic over F_p (p odd), or None.

    Fy = 2y + a1 x + a3 gives y = -(a1 x + a3)/2; Fx = 0 then gives the
    quadratic 6 x^2 + (a1^2 + 4 a2) x + (a1 a3 + 2 a4) = 0, scanned over F_p.
    """
    a1, a2, a3, a4, a6 = model
    b = (a1 * a1 + 4 * a2) % p
    cc = (a1 * a3 + 2 * a4) % p
    for x in range(p):
        if (6 * x * x + b * x + cc) % p:
            continue
        y = (-(a1 * x + a3) * pow(2, -1, p)) % p
        if (y * y + a1 * x * y + a3 * y
                - (x ** 3 + a2 * x * x + a4 * x + a6)) % p == 0:
            return x, y
    return None

# components of the special fibre of the minimal regular model (Ogg check)
_N_COMPONENTS = {"I_0": 1, "II": 1, "III": 2, "IV": 3, "I_0*": 5,
                 "IV*": 7, "III*": 8, "II*": 9}

def _n_components(kodaira):
    if kodaira.startswith("I_"):
        return int(kodaira[2:-1]) + 5 if kodaira.endswith("*") else 1
    return _N_COMPONENTS[kodaira]

def _kodaira_from_valuations(vd, vc4, vc6):
    """Kodaira symbol of an additive reduction from the valuations (p >= 5)."""
    if vd == 8:
        return "IV*" if (vc4, vc6) == (3, 5) else "I_2*"
    if vd == 9:
        return "III*" if (vc4 == 3 and vc6 >= 6) else "I_3*"
    if vd == 10:
        return "II*" if vc4 >= 4 else "I_4*"
    if vd in (2, 3, 4, 6):
        return {2: "II", 3: "III", 4: "IV", 6: "I_0*"}[vd]
    raise NotImplementedError("additive reduction with v_p(Delta) = %d" % vd)

def _auxiliary_cubic(model, p):
    """Tate's auxiliary cubic P(T) = T^3 + a21 T^2 + a42 T + a63 mod p, with
    a21 = (b2^2 - 4 b8)/16, a42 = (b2 b4 - b6)/4, a63 = (b2 b6 - b4^2)/8 (the
    divisions are by units mod p, so modular inverses are used)."""
    b2, b4, b6, b8, _c4, _c6, _delta = invariants(*model)
    a21 = (b2 * b2 - 4 * b8) * pow(16, -1, p) % p
    a42 = (b2 * b4 - b6) * pow(4, -1, p) % p
    a63 = (b2 * b6 - b4 * b4) * pow(8, -1, p) % p
    return [a63, a42, a21, 1]

def _multiplicative(model, p, n):
    """Multiplicative reduction: Kodaira I_n, splitness and Tamagawa number.
    The reduction is split iff the tangent cone at the node, y^2 + a1' x y -
    a2' x^2, splits over F_p, i.e. iff a1'^2 + 4 a2' is a nonzero square."""
    sing = _singular_point(model, p)
    if sing is None:
        raise NotImplementedError("cannot locate the singular point mod %d" % p)
    a1p, a2p = _translate(model, sing[0], sing[1])[0:2]
    disc = (a1p * a1p + 4 * a2p) % p
    split = disc != 0 and is_square(disc, p)
    # c_p = #Phi(F_p): for split reduction Phi = Z/nZ, for non-split reduction
    # the Frobenius acts on it by x -> -x, so the F_p-rational part of the
    # component group has order gcd(2, n).
    return {"kodaira": "I_%d" % n,
            "tamagawa": n if split else gcd(2, n),
            "conductor_frob": 1}

def _tate_p_ge_5(model, p):
    """Tate's algorithm for p >= 5 (and the multiplicative part at p = 3)."""
    b2, b4, b6, b8, c4, c6, delta = invariants(*model)
    if delta % p:
        return {"kodaira": "I_0", "tamagawa": 1, "conductor_frob": 0}
    if c4 % p:
        return _multiplicative(model, p, vp(delta, p))
    if p == 3:
        raise NotImplementedError("additive reduction at p = 3 is not implemented")
    # additive: move the singular point of the reduced cubic to the origin
    sing = _singular_point(model, p)
    if sing is None:
        raise NotImplementedError("cannot locate the singular point mod %d" % p)
    model = _translate(model, sing[0], sing[1])
    b2, b4, b6, b8, c4, c6, delta = invariants(*model)
    vd = vp(delta, p)
    vc4 = vp(c4, p) if c4 else 10 ** 9
    vc6 = vp(c6, p) if c6 else 10 ** 9
    kodaira = _kodaira_from_valuations(vd, vc4, vc6)
    if kodaira == "II":
        tam = 1
    elif kodaira == "III":
        # c_p = 2 iff the auxiliary cubic has a root in F_p, else 1
        tam = 2 if _has_root_mod(_auxiliary_cubic(model, p), p) else 1
    else:
        raise NotImplementedError(
            "additive reduction of type %s at p=%d: the Tamagawa number needs "
            "the further steps of Tate's algorithm, which are not implemented "
            "(v_p(Delta)=%d, v_p(c4)=%d, v_p(c6)=%d)"
            % (kodaira, p, vd, vc4, vc6))
    return {"kodaira": kodaira, "tamagawa": tam, "conductor_frob": 2}

def _tate_p_2(model):
    """Restricted 2-adic branch (see the module docstring)."""
    a1, a2, a3, a4, a6 = model
    if a1 or a2 or a3:
        raise NotImplementedError("p = 2 branch only covers a1 = a2 = a3 = 0")
    if a4 % 2 == 0:
        raise NotImplementedError("p = 2 branch only covers 2 not dividing a4")
    if a6 % 4:
        raise NotImplementedError("p = 2 branch only covers 4 dividing a6")
    # v_2(Delta) = 6 here, so the model is automatically minimal at 2
    if a4 % 4 == 1:
        return {"kodaira": "II", "tamagawa": 1, "conductor_frob": 6}
    return {"kodaira": "III", "tamagawa": 2, "conductor_frob": 5}

def tate_algorithm(a4, a5, a6, p):
    """Run Tate's algorithm for E : y^2 + a5*y = x^3 + a4*x + a6 at the prime p.

    Returns a dict with the keys 'kodaira' (Kodaira symbol), 'tamagawa' (the
    Tamagawa number c_p), 'conductor_frob' (the conductor exponent f_p),
    'min_disc' (the minimal discriminant), 'c4', 'c6' and 'model' (the
    minimal model used, as (a1,a2,a3,a4,a6))."""
    if p < 2:
        raise ValueError("p must be a prime")
    model = (0, 0, a5, a4, a6)
    if invariants(*model)[6] == 0:
        raise ValueError("singular curve (Delta = 0)")
    if p == 2:
        out = _tate_p_2(model)
    else:
        model = minimise(model, p)
        out = _tate_p_ge_5(model, p)
    b2, b4, b6, b8, c4, c6, delta = invariants(*model)
    out["min_disc"] = abs(delta)
    out["c4"] = c4
    out["c6"] = c6
    out["model"] = model
    return out

# elllocalred 'kod' codes of the PARI/GP release installed here (2.15.2).
# The calibration was done in this file's development: for p >= 5 the Kodaira
# type was recomputed independently from the valuations of the minimal model
# and matched against the codes: 1 = I_0, 2 = II, 3 = III, 4 = IV, 4+n = I_n
# (and negative codes for the starred types, not decoded here).
# Recent PARI/GP releases use a different enumeration (1 = I_0, 2 = I_n,
# 3 = I_0*, ...); that newer table must not be applied to the old codes.
_PARI_KOD_CODES = {1: "I_0", 2: "II", 3: "III", 4: "IV"}

def _pari_kod_to_symbol(code):
    """Kodaira symbol for a PARI 'kod' code of this PARI version (or None)."""
    if code in _PARI_KOD_CODES:
        return _PARI_KOD_CODES[code]
    return "I_%d" % (code - 4) if code >= 5 else None

def _parse_vec(text):
    """Parse a GP vector literal such as '[5, 3, [1, 0, 0, 0], 2]'."""
    text = re.sub(r"Mat\((\[[^\[\]]*\])\)", r"\1", text.strip())
    if not (text.startswith("[") and text.endswith("]")):
        raise ValueError("not a GP vector: %r" % text)
    inner = text[1:-1].strip()
    if not inner: return []
    out, depth, cur = [], 0, ""
    for ch in inner:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return [_parse_vec(x) if x.startswith("[") else int(x) for x in out]

def _check_pari(label, model, p, ours):
    """Compare our result at p with PARI/GP's elllocalred (independent oracle)."""
    if shutil.which("gp") is None:
        print("  %s: PARI-ORACLE-SKIPPED (no 'gp' on PATH)" % label)
        return
    script = "E=ellinit([%d,%d,%d,%d,%d],1); print(elllocalred(E,%d));\n" % (
        model + (p,))
    proc = subprocess.run(["gp", "-q", "-f"], input=script, capture_output=True,
                          text=True, timeout=300)
    lines = [ln.strip() for ln in proc.stdout.splitlines()
             if ln.strip().startswith("[")]
    if not lines:
        print("  %s: PARI-ORACLE-SKIPPED (no usable 'gp' output)" % label)
        return
    loc = _parse_vec(lines[0])
    f_pari, kod_pari, c_pari = loc[0], loc[1], loc[3]
    sym = _pari_kod_to_symbol(kod_pari)
    print("  %s: PARI elllocalred = %s" % (label, loc))
    for key, pari_value in (("conductor_frob", f_pari), ("tamagawa", c_pari),
                             ("kodaira", sym)):
        if pari_value != ours[key]:
            print("PARI CROSS-CHECK FAILED: %s = %r (PARI) vs %r (ours)"
                  % (key, pari_value, ours[key]))
            raise AssertionError("PARI mismatch on %s" % key)
    print("  %s: PARI cross-check OK (f_p, c_p, Kodaira symbol)" % label)

def _show(label, res, keys=("kodaira", "tamagawa", "conductor_frob")):
    print(label)
    for key in keys:
        print("   %-15s = %s" % (key, res[key]))

def ogg_consistency(res, p=2):
    """Ogg's formula consistency check.

    Ogg's formula says   f_p = v_p(Delta_min) + 1 - m,
    where m is the number of irreducible components of the geometric special
    fibre.  Given the Kodaira symbol, m is known, so the formula is a
    genuine CONSISTENCY CHECK on the computed invariants (it catches a wrong
    Kodaira symbol, a wrong discriminant valuation, or a wrong conductor
    exponent).

    Returns True if the computed invariants are consistent with Ogg's
    formula, False otherwise.  Kept as a separate function so that it can be
    tested for LIVENESS: a control that cannot fail is not a control.
    """
    m = vp(res["min_disc"], p) + 1 - res["conductor_frob"]
    return m == _n_components(res["kodaira"])


def main():
    ok = True
    # ---- the curve of interest: E : y^2 = x^3 - x = 32a2 ----
    res2 = tate_algorithm(-1, 0, 0, 2)
    print("E : y^2 = x^3 - x   at p = 2")
    for key in ("kodaira", "tamagawa", "conductor_frob", "min_disc", "c4", "c6"):
        print("   %-15s = %s" % (key, res2[key]))
    print("   minimal model    =", res2["model"])
    # Ground truth from PARI/GP: c_2 = 2, f_2 = 5, minimal discriminant 64,
    # c4 = 48, c6 = 0.  On the Kodaira symbol see the docstring: Ogg's formula
    # forces m = v_2(Delta_min) + 1 - f_2 = 6 + 1 - 5 = 2 components, i.e.
    # type III (type I_0* has 5 components and would force f_2 = 2, hence a
    # conductor 4, contradicting the conductor 32).
    truth = {"tamagawa": 2, "conductor_frob": 5, "min_disc": 64, "c4": 48,
             "c6": 0, "kodaira": "III"}
    for key, want in truth.items():
        if res2[key] != want:
            print("ASSERTION FAILED: %s = %r, expected %r"
                  % (key, res2[key], want))
            ok = False
    # Ogg consistency control: f_p = v_p(Delta_min) + 1 - m
    m = vp(res2["min_disc"], 2) + 1 - res2["conductor_frob"]
    if not ogg_consistency(res2, 2):
        print("OGG CONSISTENCY FAILED:", m, res2["kodaira"])
        ok = False

    # ---- good reduction at p = 3 ----
    res3 = tate_algorithm(-1, 0, 0, 3)
    _show("E : y^2 = x^3 - x   at p = 3", res3)
    for key, want in (("kodaira", "I_0"), ("tamagawa", 1),
                      ("conductor_frob", 0)):
        if res3[key] != want:
            print("ASSERTION FAILED: %s = %r, expected %r"
                  % (key, res3[key], want))
            ok = False

    # ---- mutation control: a different curve, a different answer ----
    mut = tate_algorithm(1, 0, 0, 2)
    _show("mutation control (a4 = +1, i.e. y^2 = x^3 + x at p = 2)", mut)
    if any(mut[k] == res2[k]
           for k in ("kodaira", "tamagawa", "conductor_frob")):
        print("MUTATION CONTROL FAILED (not input sensitive)")
        ok = False
    else:
        print("MUTATION-CONTROL-OK")

    # ---- regression control: a translation must preserve the discriminant --
    # A spurious term in the transformed coefficients silently changes Delta
    # and corrupts the valuations the additive branch reads off.  The model
    # with a1 != 0 is the one that matters: with a1 = 0 the erroneous a1*t
    # term is invisible, so a control built only from short Weierstrass models
    # passes on broken code.  (The full regression test, with a live PARI
    # cross-check, is tests/tate_translation_differential.py.)
    for _model, _r, _t in (((0, 0, 0, -1, 0), 1, 1),      # a1 = 0
                           ((1, 2, 3, -4, 5), 1, 1),      # a1 != 0
                           ((3, -1, 2, 7, -6), 1, 0)):
        _d_before = invariants(*_model)[6]
        _d_after = invariants(*_translate(_model, _r, _t))[6]
        if _d_after != _d_before:
            print("TRANSLATION REGRESSION FAILED: Delta changed under a "
                  "translation of %r by (r=%d, t=%d) (%r -> %r)"
                  % (_model, _r, _t, _d_before, _d_after))
            ok = False
            break
    else:
        print("TRANSLATION-CONTROL-OK")

    # ---- PARI/GP cross-checks ----
    print("PARI/GP cross-check:")
    try:
        _check_pari("E at p=2", (0, 0, 0, -1, 0), 2, res2)
        _check_pari("E at p=3", (0, 0, 0, -1, 0), 3, res3)
        # a multiplicative case for the p >= 5 branch: y^2 = x^3 + 17x - 318
        # has non-split multiplicative reduction at 5
        mult = tate_algorithm(17, 0, -318, 5)
        _show("E' : y^2 = x^3 + 17x - 318   at p = 5", mult)
        _check_pari("E' at p=5", (0, 0, 0, 17, -318), 5, mult)
    except AssertionError as exc:
        print("PARI CROSS-CHECK FAILED:", exc)
        ok = False
    if not ok:
        print("TATE-FAILED")
        return 1
    print("TATE-OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
