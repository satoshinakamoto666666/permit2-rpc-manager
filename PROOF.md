# PROOF.md — The Rank-1 BSD Leading-Coefficient Identity for `E : y² + y = x³ − x`

**Curve.** `E : y² + y = x³ − x`. Cremona label **37a1**, LMFDB label **37.a1**.
Minimal model `[0, 0, 1, -1, 0]`, conductor `N = 37`, minimal discriminant
`Δ = 37`, `c₄ = 48`, `c₆ = -216`, `j = 110592/37`, Néron differential
`ω = dx/(2y + 1)`.

**What this document establishes, and what it does not.**

This is **BSD Ladder Rung 1**: a certified verification of the rank-1
Birch–Swinnerton-Dyer leading-coefficient identity for the smallest-conductor
elliptic curve of rank 1 (`37a1`), verified to ~48 significant digits with
certified fixed-point interval error bounds and cross-checked against independent
routes and John Cremona's `ecdata` reference tables. It is **not** a proof of
the general BSD conjecture, which is open. Every claim below is tagged:

| tag | meaning |
|---|---|
| **PROVED** | derived here by a self-contained argument checkable from this repository alone |
| **COMPUTED** | produced by a script in this repository with a proved error bound and cross-checked against an independent route or external implementation |
| **CITED** | a published theorem or reference database table, quoted with the exact reference named |
| **OPEN** | not established here |

---

## 1. The rank-1 BSD identity

For an elliptic curve `E/ℚ` of rank `r = 1`, the Birch–Swinnerton-Dyer
leading-coefficient formula asserts

```
    L'(E, 1)  =  Omega_E * Reg_E * (prod_p c_p) * #Sha(E) / (#E(Q)_tors)^2.    (BSD-1)
```

For `E = 37a1` the ingredients are:

* `#E(ℚ)_tors = 1` — **PROVED** in §2 (`src/invariants.py`).
* `prod_p c_p = c_37 = 1` — **PROVED** in §3 (`src/invariants.py`).
* `P = (0, 0) ∈ E(ℚ)` of infinite order, not divisible by `2` or `3` in `E(ℚ)` — **PROVED / COMPUTED** in §2 (`src/invariants.py`), and `E(ℚ) = ℤ·P` (rank 1) — **CITED** (Gross–Zagier 1986; Kolyvagin 1988; Cremona `ecdata/allgens`).
* `Reg_E = ĥ(P)` — **COMPUTED** in §4 (`src/height.py`), three independent certified routes.
* `Ω_E` — **COMPUTED** in §5 (`src/period.py`), three independent certified routes.
* `L'(E, 1)` — **COMPUTED** in §6 (`src/lprime.py`), with two independent `E₁(x)` certifications and Deligne tail bound.
* `#Sha(E/ℚ) = 1` — **CITED** in §8 (Gross–Zagier 1986; Kolyvagin 1988; Cremona `ecdata`).

Substituting `#E(ℚ)_tors = 1` and `prod_p c_p = 1`, (BSD-1) reduces to

```
    R := L'(E, 1) / (Omega_E * Reg_E)  =?  #Sha(E/Q) = 1.
```

We compute `R` in certified fixed-point interval arithmetic (`src/identity.py`)
and prove that `1` lies inside the certified interval for `R` with width below
`10⁻⁴⁷`.

### 1.1 Period convention and the 2-component guard

Completing the square `(2y + 1)² = 4x³ − 4x + 1` shows that `E(ℝ)` has **two**
connected components because `disc(x³ − x + 1/4) = 37/16 > 0`, so `4x³ − 4x + 1`
has three distinct real roots `e₃ < e₂ < e₁`. The BSD formula uses the integral
over the **full real locus**:

```
    Omega_E = 5.98691729246391925966401995890501635559516758274...
```

Using the identity component alone (`Ω_conn = Ω_E / 2 = 2.9934586462319596...`)
gives `R_conn = 2`, which would falsely imply `#Sha(E) = 2` (impossible for a
group equipped with the alternating Cassels–Tate pairing). `src/identity.py`
explicitly recomputes the ratio with `Ω_E / 2` and requires the result to
contain `2`.

---

## 2. Torsion subgroup `#E(ℚ)_tors = 1` and generator `P = (0, 0)` — **PROVED / COMPUTED / CITED**

### 2.1 Proof that `#E(ℚ)_tors = 1` (**PROVED**)

`E : y² + y = x³ − x` has integer invariants (`src/invariants.py`)

```
    b2 = 0,  b4 = -2,  b6 = 1,  b8 = -1,  c4 = 48,  c6 = -216,  Delta = 37.
```

Since `Δ = 37` is prime, `E` has good reduction at every prime `p ≠ 37`, in
particular at `p = 2` and `p = 3`:

* Over `𝔽₂`, `y² + y ≡ 0` and `x³ − x ≡ 0` for all `x, y ∈ 𝔽₂`, so all `4`
  affine points of `𝔽₂²` lie on `E`, giving `#E(𝔽₂) = 1 + 4 = 5`.
* Over `𝔽₃`, direct enumeration gives `6` affine points `(0,0), (0,2), (1,0),
  (1,2), (2,0), (2,2)` plus `O`, so `#E(𝔽₃) = 7`.

For any prime `p` of good reduction, the kernel of reduction `E(ℚ)_tors → E(𝔽_p)`
is a `p`-group (trivial for unramified `p ≥ 3`, and of order dividing `2` at
`p = 2`). Therefore `#E(ℚ)_tors` divides `5 · 2^a` (from `p = 2`) and divides
`7` (from `p = 3`). Since `gcd(5 · 2^a, 7) = 1`, we conclude

```
    #E(Q)_tors = 1.
```

### 2.2 Multiples and non-divisibility of `P = (0, 0)` (**PROVED / COMPUTED**)

In exact rational arithmetic (`src/invariants.py`), `P = (0, 0)` satisfies
`0² + 0 = 0³ − 0`, and its multiples under the group law `(x, y) ↦ −(x, y) = (x, −y − 1)`
are

```
    1P = (0, 0),    2P = (1, 0),    3P = (-1, -1),
    4P = (2, -3),   5P = (1/4, -5/8),   6P = (6, 14).
```

Since `#E(ℚ)_tors = 1` and `P ≠ O`, `P` has **infinite order**. Moreover, if
`P = mQ` for some `Q ∈ E(ℚ)` and `m ∈ {2, 3}`, then `ĥ(Q) = ĥ(P)/m² ≤ 0.0128`,
which forces `x(Q) = u/v²` with `v ≤ 8, |u| ≤ 64`. `src/invariants.py` scans
all such rational points and verifies that no `Q ∈ E(ℚ)` satisfies `2Q = P` or
`3Q = P`. That `rank E(ℚ) = 1` (so `P` generates the full Mordell–Weil group
`E(ℚ) ≅ ℤ`) is **CITED** from Gross–Zagier (1986), Kolyvagin (1988), and
Cremona's 2-descent (`ecdata/allgens`).

---

## 3. Local reduction at `p = 37` and Tamagawa product `∏ c_p = 1` — **PROVED**

Since `Δ = 37` is prime, `v_37(Δ) = 1 < 12` and `v_p(Δ) = 0` for all `p ≠ 37`.
Thus `[0, 0, 1, -1, 0]` is the unique globally minimal Weierstrass model.

At `p = 37`:

1. `v_37(Δ) = 1` and `37 ∤ c₄ = 48`, so `E` has **multiplicative reduction of
   Kodaira type `I₁`** and conductor `N = 37¹ = 37`.
2. Partial derivatives of `F(x, y) = y² + y − x³ + x` mod `37` vanish at
   `2y₀ + 1 ≡ 0 ⇒ y₀ ≡ 18 (mod 37)` and `3x₀² − 1 ≡ 0 ⇒ x₀ ≡ 5 (mod 37)`
   (where `5³ − 5 = 120 ≡ 9 ≡ 18² + 18 (mod 37)`), so `(5, 18)` is the unique
   singular node over `𝔽_37`.
3. Translating `(5, 18)` to the origin gives the tangent cone `y'² − 15x'² ≡ 0 (mod 37)`.
   Since `15¹⁸ ≡ −1 (mod 37)`, the tangent slopes are quadratic over `𝔽_37`, so
   the reduction is **non-split multiplicative** (`a_37 = −1`, local root
   number `w_37 = −a_37 = +1`, global root number `w = w_∞ · w_37 = −1`).
4. Because `v_37(Δ) = 1`, the component group `Φ_37 ≅ ℤ/1ℤ` is trivial, so
   `c_37 = 1` and `∏_p c_p = 1`.

---

## 4. The regulator `Reg_E = ĥ(P)` — **COMPUTED**, three independent certified routes

For a minimal model of prime discriminant `Δ = 37` with `c_37 = 1`, every point
 lies on the identity component `E₀(ℚ_p)` at every prime `p`. Consequently the
homogeneous duplication polynomials on `x = A/D`,

```
    Phi(A, D)   = A^4 + 2 A^2 D^2 - 2 A D^3 + D^4,
    Psi^2(A, D) = 4 A^3 D - 4 A D^3 + D^4,
```

satisfy `gcd(Phi(A, D), Psi²(A, D)) = 1` whenever `gcd(A, D) = 1` (verified
explicitly across the integer duplication orbits in `src/height.py`). There is
therefore **zero non-Archimedean cancellation**, and Tate's telescoping series
gives

```
    h_hat(Q) = ln max(|A_0|, |D_0|) + sum_{n>=0} 4^{-(n+1)} ln(mu_n),
```

where `(u_0, v_0) = (A_0, D_0) / max(|A_0|, |D_0|)` and
`μ_n = max(|Phi(u_n, v_n)|, |Psi²(u_n, v_n)|)`, `(u_{n+1}, v_{n+1}) = (Phi, Psi²)/μ_n`.
Since `1/37 ≤ μ_n ≤ 9`, `|ln μ_n| < 4`, so the tail after `N = 90` steps is
strictly bounded by `2 / 4⁹⁰ < 10⁻⁵³`.

`src/height.py` computes `Reg_E = ĥ(P)` at internal scale `10¹³⁰` along **three
disjoint duplication orbits**:

* **Route 1**: from `P = (0, 0)` (`x = 0/1`), `Reg_E = ĥ(P)`.
* **Route 2**: from `2P = (1, 0)` (`x = 1/1`), `Reg_E = ĥ(2P) / 4`.
* **Route 3**: from `3P = (−1, −1)` (`x = −1/1`), `Reg_E = ĥ(3P) / 9`.

All three routes agree to 50 decimal places:

```
    route 1 (from P=(0,0))        : 0.051111408239968840235886099756942021609538202
    route 2 (from 2P=(1,0) / 4)   : 0.051111408239968840235886099756942021609538202
    route 3 (from 3P=(-1,-1) / 9) : 0.051111408239968840235886099756942021609538202
    certified interval width      : 1.000e-50
```

---

## 5. The real period `Ω_E` — **COMPUTED**, three independent certified routes

In `src/cert.py`, `cubic_roots_37a1()` encloses the three real roots `e₁ > e₂ > e₃`
of `4x³ − 4x + 1 = 0` to `1 ULP` (`10⁻⁵⁰`) by verifying opposite signs of the
exact integer polynomial `4X³ − 4S²X + S³` at consecutive fixed-point integers.

`src/period.py` then computes `Ω_E` by **three independent routes**:

1. **Route 1 (Gauss AGM)**: `Ω_E = 2π / AGM(√(e₁ − e₃), √(e₁ − e₂))`.
2. **Route 2 (Landen-reduced Gauss hypergeometric series)**: applies three
   descending Landen transformations `k_{j+1} = k_j² / (1 + k_j')²` from
   `k₀ = √((e₂ − e₃)/(e₁ − e₃))` and sums the Gauss hypergeometric series with
   an explicit geometric tail bound.
3. **Route 3 (Jacobi theta series)**: computes the elliptic nome
   `q = exp(−π · AGM(1, k') / AGM(1, k))` and evaluates
   `Ω_E = 2π · θ₃(q)² / √(e₁ − e₃)` with an explicit tail bound.

Result:

```
    route 1 (AGM)            : 5.986917292463919259664019958905016355595167582
    route 2 (hypergeometric) : 5.986917292463919259664019958905016355595167582
    route 3 (theta series)   : 5.986917292463919259664019958905016355595167582
    certified interval width : 1.340e-48
```

---

## 6. The derivative `L'(E, 1)` — **COMPUTED**

1. **Fourier coefficients `a_n` (`src/a_n.py`)**: computed for `1 ≤ n ≤ 160` by
   two independent methods — projective point counting on `y² + y = x³ − x` and
   the Legendre character sum on the isomorphic short model `Y² = X³ − 16X + 16`
   — extended by the Hecke recursion and verified to have zero mismatches.
2. **Functional equation and `L'(E, 1)` (`src/lprime.py`)**: since the global
   root number is `w = −1` (Fricke eigenvalue `λ = +1`), `L(E, 1) = 0` and

   ```
       L'(E, 1) = 2 * sum_{n>=1} (a_n / n) * E_1(2 * pi * n / sqrt(37)).
   ```

3. **Certified `E₁(x)` and internal control (`src/cert.py`, `src/lprime.py`)**:
   * Euler's constant `γ` is enclosed at scale `10¹³⁰` from the identity
     `γ = ∑_{k≥1} (−1)^{k−1} a^k/(k·k!) − ln(a) − E₁(a)` at the integer `a = 28`,
     where `e²⁸ E₁(28)` is bracketed between consecutive exact rational
     convergents `C_{2m}(28) < e²⁸ E₁(28) < C_{2m+1}(28)` of Stieltjes's
     positive continued fraction.
   * For every `1 ≤ n ≤ 135`, `E₁(n c)` is enclosed by monotone endpoint
     evaluation at scale `10¹³⁰`, and on the overlap window `18 ≤ n ≤ 26` it is
     cross-checked against the `γ`-free Stieltjes continued fraction.
   * By Deligne's bound `|a_n/n| ≤ 2` and `E₁(x) < e^{−x}` for `x ≥ 1`, the tail
     beyond `N₀ = 135` is bounded by `4 e^{−136c}/(1 − e^{−c}) < 9 × 10⁻⁵⁰`.

Result:

```
    L'(E, 1) lower bound: 0.305999773834052301820483683321676474452637774
    L'(E, 1) upper bound: 0.305999773834052301820483683321676474452637774
    L'(E, 1) width      : 1.680e-48
```

---

## 7. Putting it together — the BSD Rung 1 identity holds

`src/identity.py` combines the certified intervals for `Ω_E`, `Reg_E`, and
`L'(E, 1)` with `#E(ℚ)_tors = 1` and `∏ c_p = 1`:

```
    Omega_E * Reg_E                : 0.305999773834052301820483683321676474452637774
    L'(E, 1)                       : 0.305999773834052301820483683321676474452637774
    implied #Sha = L'/(Omega*Reg)  : [0.999999999999999999999999999999999999999999999,
                                      1.000000000000000000000000000000000000000000000]
    implied #Sha (integer)         : 1
```

---

## 8. What is CITED and what remains OPEN

* **CITED**: `rank E(ℚ) = 1` and `#Sha(E/ℚ) < ∞` follow from the theorems of
  Gross–Zagier (*Invent. Math.* 84, 1986) and Kolyvagin (*Math. USSR Izv.* 32,
  1989); `#Sha(E/ℚ) = 1` is recorded in Cremona's `ecdata` (`allbsd`, `curvedata`)
  and verified by Mazur–Swinnerton-Dyer / Zagier (`L'(E,1)/(Ω_E Reg_E) = 1`).
* **OPEN**: The general BSD conjecture across all elliptic curves over `ℚ`
  (especially rank `r ≥ 2` and non-trivial `p`-primary `#Sha` without Euler
  systems) remains open. See `OPEN_REMAINDER.md`.
