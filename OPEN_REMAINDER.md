# OPEN_REMAINDER.md — What This Repository Does Not Establish

1. **The general Birch–Swinnerton-Dyer conjecture is OPEN.**
   This repository certifies the rank-1 BSD leading-coefficient identity for
   **one** elliptic curve (`37a1 : y² + y = x³ − x`) to ~48 decimal digits in
   directed-rounding fixed-point interval arithmetic. It proves nothing about
   elliptic curves of rank `r ≥ 2` or general conductors.

2. **`rank E(ℚ) = 1` (upper bound) and `#Sha(E/ℚ) = 1` are CITED, not proved from scratch here.**
   * We prove in `src/invariants.py` that `#E(ℚ)_tors = 1`, that `P = (0, 0)` has
     infinite order (giving `rank E(ℚ) ≥ 1`), and that `P` is not divisible by
     `2` or `3` in `E(ℚ)`.
   * That `rank E(ℚ) ≤ 1` and `#Sha(E/ℚ) = 1` are **CITED** from the classical
     2-descent on `37a1` (Cremona, *Algorithms for Modular Elliptic Curves*,
     `ecdata/allgens` and `ecdata/allbsd`) and the Gross–Zagier / Kolyvagin
     Heegner-point Euler system theorem for analytic rank 1.

3. **Numerical verification of `L'(E, 1) / (Ω_E · Reg_E) = 1` to `10⁻⁴⁷` does not by itself prove an exact transcendental identity.**
   By Gross–Zagier (1986), the ratio `L'(E, 1) / (Ω_E · Reg_E)` is known to be
   a rational number (related to the index of a Heegner point). Our certified
   interval of width `< 10⁻⁴⁷` centered at `1` pins down that rational number
   numerically and confirms complete consistency with `#Sha(E/ℚ) = 1` and
   Cremona's `ecdata` tables.
