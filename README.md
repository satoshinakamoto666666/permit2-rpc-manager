# BSD Ladder Rung 1: Certified Verification of the BSD Identity for `37a1`

**Curve:** `E : y² + y = x³ − x` · **Cremona `37a1`** · **LMFDB `37.a1`** · **Conductor `37`**

A self-contained, zero-dependency, pure-integer fixed-point interval certificate
for the rank-1 Birch–Swinnerton-Dyer leading-coefficient identity on `37a1`:

```
    L'(E, 1) * (#E(Q)_tors)^2  =  Omega_E * Reg_E * (prod_p c_p) * #Sha(E)
```

verified to ~48 significant digits with proved error bounds, three independent
certified routes for both `Ω_E` and `Reg_E = ĥ(P)`, two independent methods for
`a_n` and `E₁(x)`, and a 10-corruption mutation test suite.

> **Scope note:** This is a certified verification of **one** rank-1 curve
> (`37a1`), not a proof of the general BSD conjecture. See [`CLAIMS.md`](CLAIMS.md)
> and [`OPEN_REMAINDER.md`](OPEN_REMAINDER.md).

## How to verify

Requires only Python 3 (standard library only; `float` and `math` are not even
imported in `src/cert.py`) and `bash`:

```bash
./verify.sh                  # Runs all 9 verification steps; exits 0
./tests/mutation_tests.sh    # Injects 10 corruptions; requires verify.sh to FAIL on each
```

## Summary of Certified Quantities

| Quantity | Value (45 digits) | Status | How verified |
|---|---|---|---|
| `#E(ℚ)_tors` | `1` | **PROVED** | `gcd(#E(𝔽₂), #E(𝔽₃)) = gcd(5, 7) = 1` (`src/invariants.py`) |
| `∏_p c_p = c_37` | `1` | **PROVED** | `Δ = 37` prime ⇒ Kodaira `I₁` (`src/invariants.py`) |
| Generator `P` | `(0, 0)` | **PROVED / CITED** | Exact rational multiples `1P..6P` + non-divisibility (`src/invariants.py`); rank 1 cited |
| `Reg_E = ĥ(P)` | `0.051111408239968840235886099756942021609538202` | **COMPUTED** | 3 certified orbits (`P`, `2P/4`, `3P/9`) in `src/height.py` |
| `Ω_E` | `5.986917292463919259664019958905016355595167582` | **COMPUTED** | 3 certified routes (AGM, Landen-hypergeometric, Jacobi theta) in `src/period.py` |
| `L'(E, 1)` | `0.305999773834052301820483683321676474452637774` | **COMPUTED** | Certified `E₁` series + Stieltjes CF control + Deligne tail (`src/lprime.py`) |
| `R = L'/(Ω_E·Reg_E)` | `1.000000000000000000000000000000000000000000000` | **COMPUTED** | Certified interval width `< 10⁻⁴⁷` (`src/identity.py`) |
| `#Sha(E/ℚ)` | `1` | **CITED** | Gross–Zagier (1986), Kolyvagin (1988), Cremona `ecdata` |
