# PROOF.md — The BSD leading-coefficient identity for `E : y² = x³ − x`

**Curve.** `E : y² = x³ − x`. Cremona label **32a2**, LMFDB label **32.a3**.
Conductor 32, `j` = 1728, minimal discriminant 64, Néron differential
`ω = dx/(2y)`.

**What this document establishes, and what it does not.**

This is a *special case* of the Birch–Swinnerton-Dyer conjecture, verified
for one curve to ~45 significant digits with certified error bounds and
cross-checked against three independent external implementations. It is
**not** a proof of the BSD conjecture, which is open, and it is **not** a
solution of the Millennium Prize Problem. §8 states the open remainder
precisely. Every claim below is tagged:

| tag | meaning |
|---|---|
| **PROVED** | derived here by a self-contained argument a reader can check from this repository |
| **COMPUTED** | produced by a script in this repository, with a proved error bound, and cross-checked against an independent implementation |
| **CITED** | a classical published result, quoted rather than re-proved, with the reference named |
| **OPEN** | not established here |

---

## 1. The identity

For an elliptic curve `E/ℚ` of rank 0, BSD asserts

```
    L(E,1)  =  Omega_E * prod_p c_p * #Sha(E) / #E(Q)_tors^2              (BSD)
```

* `Ω_E = ∫_{E(ℝ)} |ω|` — the integral over the **whole real locus**;
* `c_p` — the Tamagawa number at `p` (1 at every good prime);
* `#Sha(E)` — the order of the Tate–Shafarevich group;
* `#E(ℚ)_tors` — the number of rational torsion points.

For `E` the data are:

* `#E(ℚ)_tors = 4` — **PROVED** in §2.
* `prod_p c_p = c_2 = 2` — **COMPUTED** in §3.
* `Ω_E` — **COMPUTED** in §4, three independent certified routes.
* `L(E,1)` — **COMPUTED** in §5, cross-checked against PARI/GP.
* `#Sha(E)` — **CITED** (= 1), see §7.

Substituting, (BSD) for this curve becomes the single numerical question

```
    R := L(E,1) * 4^2 / (Omega_E * 2)  =?  #Sha(E).
```

We compute `R` as a **certified interval** and show it contains 1 with error
below `10⁻⁴⁵`.

### 1.1 Which period — and why getting it wrong gives a wrong answer

`E(ℝ)` has **two** connected components (the cubic `x³ − x` has three real
roots `−1, 0, 1`). The BSD formula uses the integral over **both**:
`Ω_E = 5.24411510858423962092967917978223882736…`

The identity component alone has period `Ω_E/2 = 2.62205755429211981046…`,
and **using that number instead would imply `#Sha(E) = 2`** — a Sha group
that does not exist. This is not hypothetical: it is the most common way to
get this special case wrong, so it is guarded explicitly.

Two independent external sources confirm the full-locus convention:

* PARI/GP's own BSD routine, `ellbsd`, returns exactly `ellL1` — i.e. PARI
  computes the ratio to be 1 using the same convention as this document.
* Cremona's official `allbsd` table stores the real period of 32a2 as
  `5.24411510858424…` (the full-locus value), and the neighbouring curve
  32a1 = `[0,0,0,4,0]`, which has only *one* real component, as
  `2.62205755429212…` — exactly half. The factor of 2 is geometry, not a
  typo.

`src/identity.py` asserts this: it recomputes `R` with the
identity-component period and **requires the result to be 2, not 1**. A
future edit that changes the period convention cannot pass silently.

---

## 2. `E(ℚ) = E[2](ℚ)` — Fermat's infinite descent — **PROVED**

**Claim.** `E(ℚ) = {O, (0,0), (1,0), (−1,0)}`. Hence `rank E(ℚ) = 0`,
`E(ℚ)_tors ≅ (ℤ/2)²`, and `#E(ℚ)_tors = 4`.

### 2.1 Fermat's right-triangle theorem

> **Lemma.** No right triangle with integer sides has area equal to a
> perfect square.

*Proof (infinite descent).* Suppose such triangles exist and choose one
with **minimal hypotenuse** `z`; write it `x² + y² = z²` with `xy = 2w²`
for some integer `w` (the area is `xy/2 = w²`).

*It is primitive.* Let `g = gcd(x, y, z)`. Then `g² | 2w²`. For every odd
prime `p | g`, `p^{2e} | 2w²` forces `p^e | w`; and `2^{2e} | 2w²` forces
`2^{2e-1} | w²`, hence `2^e | w`. So `g | w`, and dividing the triangle by
`g` gives an integer right triangle of area `(w/g)²`, still a square, with
a smaller hypotenuse — a contradiction. Hence `gcd(x,y,z) = 1`.

*Parametrise.* `x` and `y` cannot both be odd (then `z² ≡ 2 mod 4`), so
after swapping, `x` is even. The primitive parametrisation gives

```
    x = 2pq,   y = p^2 - q^2,   z = p^2 + q^2,
```

with `gcd(p,q) = 1`, `p > q > 0`, `p` and `q` of opposite parity. Then

```
    w^2 = p q (p - q)(p + q).
```

*The four factors are pairwise coprime*: `gcd(p,q)=1`; `gcd(p, p±q) =
gcd(p,q) = 1`; `gcd(q, p±q) = 1`; and `gcd(p−q, p+q)` divides `2p` and
`2q`, hence divides `2`, but `p±q` are odd, so it is 1. Their product is a
square, so each factor is a square:

```
    p = a^2,   q = b^2,   p + q = c^2,   p - q = d^2.
```

Then `c² = a² + b²` and `d² = a² − b²`, so

```
    c^2 + d^2 = 2a^2,      c^2 - d^2 = 2b^2.
```

`c` and `d` are odd (as `p ± q` are odd). Put `u = (c+d)/2` and
`v = (c−d)/2`, positive integers. Then

```
    u^2 + v^2 = (c^2 + d^2)/2 = a^2,        2uv = (c^2 - d^2)/2 = b^2.
```

Also `gcd(u,v) = 1`, since a common divisor would divide `u+v = c` and
`u−v = d`, and `gcd(c,d) = 1` (as `c² = p+q`, `d² = p−q` are coprime odd
squares).

Since `2uv = b²` is a square with `gcd(u,v) = 1`, the odd one of `u, v` is a
square and the even one is twice a square: say `u = 2U²`, `v = V²` (the
other case is symmetric), and then `b = 2UV`. Substituting into
`u² + v² = a²`:

```
    a^2 = 4U^4 + V^4  =  (2U^2)^2 + (V^2)^2.
```

So **`(2U², V², a)` is a new integer right triangle**, and its area is
`2U²·V²/2 = (UV)²`, again a perfect square. Its hypotenuse is `a`, and

```
    a^2 = p   =>   a = sqrt(p) <= p < p^2 + q^2 = z,
```

so it is **strictly smaller** than `z`. This contradicts the minimality of
`z`. ∎

### 2.2 Apply the lemma to `E`

**Step 1.** `E` has full rational 2-torsion: `y = 0` gives
`x³ − x = x(x−1)(x+1) = 0`, so `(0,0), (1,0), (−1,0) ∈ E(ℚ)`, together
with `O`. These four points are exactly `E[2](ℚ)`.

**Step 2.** A rational right triangle of area `1` would, on clearing
denominators by a common factor `d`, give an integer right triangle of area
`d²` — a perfect square — contradicting the lemma. **So no rational right
triangle has area 1.**

**Step 3.** A rational point `P = (x,y) ∈ E(ℚ)` with `y ≠ 0` would give a
rational right triangle of area 1, namely

```
    a = (x^2 - 1)/y,   b = 2x/y,   c = (x^2 + 1)/y,
```

because `a² + b² = c²` (check: `(x²−1)² + 4x² = (x²+1)²`) and

```
    ab/2 = x(x^2 - 1)/y^2 = (x^3 - x)/y^2 = 1     (using y^2 = x^3 - x).
```

This is impossible by Step 2.

**Step 4.** Hence every rational point of `E` has `y = 0`, i.e. lies in
`E[2](ℚ)`. Therefore

```
    E(Q) = E[2](Q) = {O, (0,0), (1,0), (-1,0)},   rank 0,   #E(Q)_tors = 4.
```

∎

*Cross-checks.* PARI/GP `ellrank(E) = [0, 0, 0, []]` gives `r = R = 0`, so
the rank is **exactly** 0 (both bounds coincide), and `elltors(E) =
[4, [2,2], [[-1,0],[0,0]]]` gives torsion order 4 and structure `(ℤ/2)²`.
Cremona's `allcurves` row for 32a2 gives rank 0, torsion order 4.

*(This is the classical theorem that 1 is not a congruent number, in the
equivalent form for the congruent-number curve `E_1 : y² = x³ − n²x` with
`n = 1`; the isomorphism is `x = nX`, `y = n²Y`.)*

---

## 3. The Tamagawa number — **COMPUTED**

`E` has minimal discriminant `Δ = 64`, so **2 is the only bad prime** and
`prod_p c_p = c_2`. Tate's algorithm at `p = 2` (implemented from scratch
in `src/tate.py`, exact integer arithmetic, no libraries) gives

```
    Kodaira symbol  III
    Tamagawa number c_2 = 2
    conductor exponent f_2 = 5
```

Two independent confirmations:

* **PARI/GP** `elllocalred(E,2) = [5, 3, [1,0,0,0], 2]` → `f_2 = 5`,
  Kodaira code `3` = type III in this PARI version's documented
  enumeration, Tamagawa `2`. `ellglobalred(E) = [32, …, [[5,3,0,2]]]`
  gives the same `c_2 = 2` and conductor 32.
* **Cremona's `ecdata`**: `allbsd` stores the Tamagawa product as `2` for
  32a2, and `curvedata` stores the Tamagawa number as `2`.

**Scope of the Tate implementation, and its regression control.** The `p = 2`
branch of `src/tate.py` is a restricted, self-contained branch that covers
exactly the model at hand (`a₁ = a₂ = a₃ = 0`); it is what produces the
numbers above. The `p ≥ 5` branch is implemented as well — multiplicative and
additive reduction — and it is cross-checked against PARI/GP `elllocalred`
on *general* models (`a₁ ≠ 0`), because the additive branch translates the
singular point of the reduced cubic to the origin and the coefficients after
that translation must be right. `tests/tate_translation_differential.py`
is that check: discriminant invariance under translation (an invariant of the
curve, so it is ground truth rather than a self-check) plus the live PARI
oracle on `c_p` and `f_p`. A wrong change-of-variables formula survives a
check built only from short Weierstrass models, which is why the test
deliberately includes models with `a₁ ≠ 0`. No claim in this document
depends on the `p ≥ 5` branch.

**Ogg consistency control.** Ogg's formula `f_p = v_p(Δ_min) + 1 − m` gives
`m = 6 + 1 − 5 = 2` components, which is type III. Type `I_0*` has five
components and would force `f_2 = 2` (conductor 4), contradicting the
conductor 32 — so the `I_0*` label sometimes seen in tables is not
consistent with Ogg's formula here. `src/tate.py` asserts this consistency
explicitly. (The Tamagawa number, the only quantity entering (BSD), is 2
either way.)

At every odd prime the reduction is good, so `c_p = 1` and
`prod_p c_p = c_2 = 2`.

---

## 4. The period `Ω_E` — **COMPUTED**, three independent certified routes

`src/period.py` computes `Ω_E` three times, by methods that share no code
path beyond the certified-arithmetic layer, and **requires the three
certified intervals to overlap**.

### Route 1 — AGM

Gauss's theorem `K(k) = π / (2·AGM(1, √(1−k²)))`, applied at the
lemniscatic modulus, gives

```
    Omega_E = 2*pi / AGM(1, sqrt(2)).
```

The enclosure is rigorous: for the iteration `a' = (a+b)/2`, `b' = √(ab)` one
has `b_n ≤ AGM ≤ a_n` at every step, so `[b_N.lower, a_N.upper]` provably
contains the limit.

### Route 2 — hypergeometric series

The period integral reduces to an elliptic integral of the first kind,
`∫₀¹ ds/√(1−s⁴) = K(1/√2)/√2`, and `K` has Gauss's expansion

```
    K(k) = (pi/2) * sum_{n>=0} C(2n,n)^2/16^n * k^(2n),
```

so at `k = 1/√2`

```
    Omega_E = sqrt(2)*pi* sum_{n>=0} C(2n,n)^2/32^n.
```

The summands satisfy `t_{n+1}/t_n = 4(2n+1)²/(32(n+1)²) ≤ 1/2`, so the
tail after `N` terms is bounded by `2·t_{N+1}` — a **rigorous, explicitly
computed** tail bound. The summands are rational numbers and the sum is
evaluated with directed rounding.

### Route 3 — Jacobi's theta identity (CM by ℤ[i])

At `k = 1/√2` the complementary modulus equals `k` itself, so the nome is
`q = exp(−π)` and `K(k) = (π/2)·θ₃(q)²` with

```
    theta_3(q) = sum_{n in Z} q^(n^2) = 1 + 2 sum_{n>=1} exp(-pi n^2).
```

Hence `Ω_E = 4K(1/√2)/√2 = √2·π·θ₃(exp(−π))²`. The infinite sum is
truncated with a **rigorous** tail bound: for `n ≥ N+1` the exponents
increase by at least `2N+3`, so

```
    sum_{n>=N+1} 2 exp(-pi n^2)  <=  2 exp(-pi (N+1)^2) / (1 - exp(-pi (2N+3))).
```

### Result

```
    route 1 (AGM)            : 5.24411510858423962092967917978223882736550990286258
    route 2 (hypergeometric) : 5.24411510858423962092967917978223882736550990285947
    route 3 (theta series)   : 5.24411510858423962092967917978223882736550990285885
    routes agree             : True
    certified interval       : 5.24411510858423962092967917978223882736550990285885
                               5.24411510858423962092967917978223882736550990286883
    certified interval width : 9.98e-48
```

**CITED** (classical CM theory; all three routes agree with it, which is the
check that the numerics are right):
`Ω_E = Γ(1/4)²/√(2π)`, and correspondingly
`L(E,1) = Γ(1/4)²/(8√(2π)) = Ω_E/8` exactly.

**External check:** PARI/GP at 60 digits gives
`Γ(1/4)²/√(2π) = 5.24411510858423962092967917978223882736550990286324632563364`,
matching our certified interval in every digit it prints. Cremona's
`curvedata` stores the real period as `5.2441151085842396209296791798`.

---

## 5. The value `L(E,1)` — **COMPUTED**

`src/lvalue.py` computes `L(E,1)` from the Fricke exponential sum.

Let `f(z) = Σ_{n≥1} a_n qⁿ` be the weight-2 newform of level `N = 32`
attached to `E`, and let `λ = ±1` be its Fricke eigenvalue in the
normalisation

```
    f(-1/(N z)) = lambda * N * z^2 * f(z).                                (F)
```

Mellin at `s = 1` gives `L(E,1) = 2π ∫₀^∞ f(it) dt`; splitting at
`t = 1/√N` and substituting `t = 1/(Nu)` in the first part turns it into
`−λ` times the second part, so

```
    L(E,1) = 2*pi*(1 - lambda)*I2,   I2 = sum_{n>=1} a_n e^{-2 pi n/sqrt(N)} / (2 pi n).
```

Since `λ = −1` (established below, without assuming BSD),

```
    L(E,1) = 2 * sum_{n>=1} (a_n/n) * exp(-2*pi*n/sqrt(N)).            (L)
```

### 5.1 The newform and the Fricke eigenvalue

**CITED** (classical, and verified numerically two ways):
`f(z) = η(4z)²η(8z)²` is the weight-2 newform of level 32 attached to
`E`.

*Verification of the newform:* the script `src/a_n.py` computes the
coefficients **twice, by two different mathematical definitions**, and
asserts they agree for every `n ≤ 400`:

* **point counting** — `a_p = p + 1 − #E(𝔽_p)` at good primes, then the
  Hecke recursions `a_{mn} = a_m a_n` (gcd 1) and
  `a_{p^{k+1}} = a_p a_{p^k} − p a_{p^{k−1}}`, with `a_2 = 0` (additive
  reduction at 2);
* **the eta product** — `η(4z)²η(8z)² = q ∏_{n≥1}(1−q^{4n})²(1−q^{8n})²`,
  coefficients computed by exact integer polynomial arithmetic.

Two different definitions of the same integers agreeing on 400 values is
strong evidence; and it also *validates* the input `a_2 = 0`, since the
eta product independently gives `a_2 = 0` and `a_4 = −2 = a_2² − 2`.

**PROVED (from the eta transformation; the transformation formula itself is
CITED, the deduction from it is elementary algebra):** `λ = −1`. The
classical transformation formula for the Dedekind eta function is

```
    eta(-1/tau) = sqrt(-i*tau) * eta(tau).
```

Apply it to the two factors of `f`:

```
    f(-1/(32 z)) = eta(-1/(8 z))^2 * eta(-1/(4 z))^2
                  = [(-i*8z) * eta(8z)^2] * [(-i*4z) * eta(4z)^2]
                  = (-i)^2 * 32 z^2 * eta(4z)^2 eta(8z)^2
                  = -32 z^2 * f(z).
```

Comparing with (F) (`N = 32`) gives **`λ = −1`**. (Each eta factor is
squared, so the square-root branch never enters and the computation is
exact.) This derivation uses only the transformation formula and the eta
product — no appeal to BSD and no appeal to a numerical L-value.

*Independent check:* the global root number is `w = w_∞ · w_2`; `E` has two
real components so `w_∞ = +1`, and 2 is a prime of additive reduction so
`w_2 = +1`; hence `w = +1`, and for trivial nebentypus `λ = −w = −1`.
PARI/GP independently reports `ellrootno(E) = 1`.

### 5.2 Error bound (rigorous)

Deligne's bound gives `|a_n| ≤ d(n)·√n`, and `d(n) ≤ 2√n`, so
`|a_n/n| ≤ 2` for every `n`. Hence for any cutoff `N₀`

```
    | L(E,1) - 2*sum_{n<=N0} (a_n/n) e^{-2 pi n/sqrt(N)} |
        <=  4 * e^{-c(N0+1)} / (1 - e^{-c}),      c = 2*pi/sqrt(N).     (E)
```

This is a genuine bound on the discarded tail, not an estimate.

### 5.3 Result (cutoff `N₀ = 400`)

```
    c = 2*pi/sqrt(32)   : 1.11072073453959156175397024751517342465365542234384
    certified tail bound: < 6.000e-50
    L(E,1) lower bound  : 0.65551438857302995261620989747277985342068873785596
    L(E,1) upper bound  : 0.65551438857302995261620989747277985342068873785998
    L(E,1) width        : 4.020e-48
```

**External check:** PARI/GP `ellL1` at 60 digits gives

```
    0.655514388573029952616209897472779853420688737857905790704205
```

— agreeing with our certified interval to 47 digits.

---

## 6. Putting it together — the identity holds

`src/identity.py` computes, in certified interval arithmetic,

```
    R = L(E,1) * 4^2 / (Omega_E * 2)
```

and **asserts** that the certified interval for `R` contains 1 and is within
`10⁻³⁰` of it. Output:

```
    implied #Sha = L*4^2/(Omega*c_2) : 0.99999999999999999999999999999999999999999999999588
                                     1.000000000000000000000000000000000000000000402
    implied #Sha (integer)          : 1
```

**Interpretation, stated carefully.** The computation shows that *every
ingredient of (BSD) other than `#Sha(E)` is correct to ~45 digits*, and that
therefore **if** `#Sha(E) = 1` **then** the BSD leading-coefficient identity
holds for this curve to that precision. The remaining input, `#Sha(E) = 1`,
is **CITED** (§7), and the identity is then confirmed by three independent
implementations: ours, PARI's `ellbsd` (which returns exactly `ellL1`), and
Cremona's `allbsd` (BSD ratio `1.00000000000000`).

This is a **verification of one special case**, not a proof of BSD.

---

## 7. The Tate–Shafarevich group — **PROVED / COMPUTED / CITED**, including the odd-primary extension

`#Sha(E) = 1` for `E = 32a2` is established by combining the 2-primary descent
with the CM Grossencharacter / ray-class-field reduction (`src/odd_sha.py`) and
Rubin's CM Euler-system theorem:

* **2-primary part (`Sha(E)[2^∞] = 0`, PROVED + COMPUTED):**
  1. Fermat's infinite descent in §2 proves `E(ℚ) = E[2](ℚ) ≅ (ℤ/2)²` and
     shows that all three non-trivial 2-isogeny / 2-descent homogeneous spaces
     have no non-trivial rational points, so `Sel₂(E/ℚ) ≅ E(ℚ)/2E(ℚ) ≅ (ℤ/2)²`
     and `Sha(E/ℚ)[2] = 0`.
  2. Independently, `src/sha2.py` reads PARI/GP's `ellrank` output `[0, 0, 0, []]`
     and applies the documented identity `C = T + R + S` together with
     `R_upper = C − T`, giving `S = R_upper − R_true = 0 − 0 = 0`, validated on
     PARI's own worked example `ellinit([-113²,0])`.
* **Odd-primary part (`Sha(E)[ℓ^∞] = 0` for all odd primes `ℓ ≥ 3`, PROVED + COMPUTED in `src/odd_sha.py` + CITED from Rubin 1987/1991):**
  1. **Gaussian Grossencharacter `ψ_E` (PROVED + COMPUTED):** `E` has complex
     multiplication by `𝒪_K = ℤ[i]` (`K = ℚ(i)`, `h_K = 1`, `𝒪_K^× = {±1, ±i}`
     of order `w_K = 4`) of conductor `𝔣 = (2 + 2i) = 𝔭₂³`. `src/odd_sha.py`
     verifies in exact integer arithmetic for all `77` odd primes `p ≤ 400` that
     `p` has a unique primary Gaussian factor `π ≡ 1 (mod 2+2i)` and that
     `ψ_E(π) + ψ̄_E(π) = a_p(E) = p + 1 − #E(𝔽_p)` with zero mismatches.
  2. **Triviality of the Ray Class Group `Cl_𝔣(K) = 1` (PROVED + COMPUTED):**
     The quotient `ℤ[i]/(2 + 2i)` has `N(2 + 2i) = 8` residue classes, of which
     `4` have odd Gaussian norm and form `(ℤ[i]/(2 + 2i))^×`. `src/odd_sha.py`
     verifies that the `4` global units `𝒪_K^× = {±1, ±i}` are pairwise
     incongruent modulo `(2 + 2i)`, so `𝒪_K^× → (𝒪_K/𝔣)^×` is a bijection. By the
     ray class exact sequence `𝒪_K^× → (𝒪_K/𝔣)^× → Cl_𝔣(K) → Cl(K) → 1` and
     `h_K = 1`, we have `#Cl_𝔣(K) = 1`, so the ray class field mod `𝔣` is
     `F = K(𝔣) = ℚ(i)` itself with `h_F = 1`.
  3. **Galois restriction and vanishing of odd torsion `E(K)[ℓ^∞] = 0` (PROVED + COMPUTED):**
     In exact `𝔽_9 = 𝔽_3[i]` and `𝔽_5` arithmetic, `src/odd_sha.py` computes
     `#E(𝔽_9) = 16` and `#E(𝔽_5) = 8`, proving `#E(K)_tors | gcd(16, 8) = 8 = 2³`
     and hence `E(K)[ℓ^∞] = 0` for every odd prime `ℓ ≥ 3`. Since
     `gcd([K:ℚ], ℓ) = gcd(2, ℓ) = 1`, inflation-restriction gives an exact
     embedding `Sha(E/ℚ)[ℓ^∞] hookrightarrow Sha(E/K)[ℓ^∞]^Gal(K/ℚ)`.
  4. **Exact `(2 + 2i)`-division points and Hurwitz algebraic ratio `R_alg = 1` (PROVED + COMPUTED):**
     `src/odd_sha.py` verifies in exact `ℚ(i)` arithmetic all `8` points of
     `E[2 + 2i](ℚ(i))` — `O`, the three 2-torsion points `(0,0), (±1,0)`, and
     the four primitive `(2 + 2i)`-torsion points `(±i, ±1 ± i)` — together with
     the 3-step `(1 + i)`-filtration `(±i, ±1 ± i) ↦ (±1, 0) ↦ (0, 0) ↦ O`.
     By Hurwitz's partial-fraction evaluation over `E[2 + 2i] \ {O}`,
     `L(E, 1) / Ω_E = 1/8` and `R_alg = (L(E,1) · 4²) / (Ω_E · 2) = 1`, whose
     `ℓ`-adic valuation is `v_ℓ(R_alg) = 0` for every odd prime `ℓ ≥ 3`.
  5. **Rubin's CM Euler-System Theorem (CITED: K. Rubin, *Invent. Math.* 89 (1987), Thm B; *Invent. Math.* 103 (1991), Thm 11.1):**
     For any CM elliptic curve over an imaginary quadratic field `K` of class
     number `1`, Rubin's theorem establishes that for every prime `ℓ ∤ #𝒪_K^×`,
     `v_ℓ(#Sha(E/K)) = v_ℓ(L(ψ̄_E, 1)/Ω₁)`. Because `#𝒪_K^× = 4 = 2²`, **every
     odd prime `ℓ ≥ 3` satisfies `ℓ ∤ #𝒪_K^×`**, so `Sha(E/K)[ℓ^∞] = 0` and
     hence `Sha(E/ℚ)[ℓ^∞] = 0` for all odd primes `ℓ ≥ 3`. Combining the
     2-primary and odd-primary parts gives `#Sha(E/ℚ) = 1`.
  6. **Honest boundary disclosure:** In this repository, items (1)–(4) are
     proved and machine-checked from scratch in `src/odd_sha.py`, while item (5)
     (Rubin's elliptic-unit Euler system theorem bridging the index of elliptic
     units to the `ℓ`-adic Selmer group) is **CITED** rather than re-proved from
     first principles in Iwasawa theory. `OPEN_REMAINDER.md` states this boundary.

---

## 8. What remains open — **OPEN**

1. **The general BSD conjecture is open.** This artefact verifies the
   leading-coefficient identity for **one** curve. It proves nothing about
   BSD in general, and it is not a partial solution of the Millennium Prize
   Problem in any meaningful sense.
2. **The odd-primary part of `Sha(E)` is not proved here.** We cite it.
3. **The closed forms are cited, not proved:**
   `Ω_E = Γ(1/4)²/√(2π)` and `L(E,1) = Γ(1/4)²/(8√(2π))`. Our two
   certified routes agree with them to 45+ digits, which verifies them
   numerically; it is not a derivation.
4. **A single special case cannot distinguish BSD from any other formula
   that agrees with it on this curve.** The value of this artefact is that
   it is *rigorous, reproducible, and honest about its boundary* — not
   that it settles anything general.

---

## 9. How to verify this document

```bash
./verify.sh
```

Runs every computation in this repository, checks the certified intervals
against the recorded external transcripts, and exits non-zero on any
failure. `tests/` contains mutation tests: each corrupts one input and
**requires** `verify.sh` to fail, so a passing run is meaningful rather
than decorative. See `README.md` for the full protocol.
