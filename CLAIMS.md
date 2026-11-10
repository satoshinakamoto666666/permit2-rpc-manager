# CLAIMS.md — Epistemic Ledger for BSD Rung 1 (`37a1`)

Every claim in this repository is listed below with its status (**PROVED**,
**COMPUTED**, **CITED**, or **OPEN**) and the exact script or document that
verifies it.

| # | Claim | Status | Where established / checked |
|---|---|---|---|
| 1 | `E : y² + y = x³ − x` (`[0,0,1,-1,0]`) has `c₄ = 48`, `c₆ = -216`, `Δ = 37`, `j = 110592/37`, and is globally minimal | **PROVED** | `src/invariants.py` (`weierstrass_invariants`), `PROOF.md` §2–3 |
| 2 | `E` has non-split multiplicative reduction at `p = 37` (Kodaira `I₁`, node `(5, 18) mod 37`, `a_37 = -1`, `c_37 = 1`, `∏_p c_p = 1`, conductor `N = 37`) | **PROVED** | `src/invariants.py` (`local_reduction_37`), `PROOF.md` §3 |
| 3 | `#E(𝔽₂) = 5` and `#E(𝔽₃) = 7`, hence `#E(ℚ)_tors = gcd(5, 7) = 1` | **PROVED** | `src/invariants.py` (`prove_trivial_torsion`), `PROOF.md` §2.1 |
| 4 | `P = (0, 0) ∈ E(ℚ)` has infinite order, with `2P = (1,0)`, `3P = (-1,-1)`, `4P = (2,-3)`, `5P = (1/4,-5/8)`, `6P = (6,14)`, and `P` is not divisible by `2` or `3` in `E(ℚ)` | **PROVED / COMPUTED** | `src/invariants.py` (`verify_generator_multiples`), `PROOF.md` §2.2 |
| 5 | `rank E(ℚ) = 1`, so `P = (0, 0)` generates `E(ℚ) ≅ ℤ` | **CITED** | Gross–Zagier (1986), Kolyvagin (1988), Cremona `ecdata/allgens` (`data/ecdata-37a1.txt`) |
| 6 | Regulator `Reg_E = ĥ(P) = 0.051111408239968840235886099756942021609538202…` certified to `< 10⁻⁴⁸` across 3 independent orbits (`P`, `2P`, `3P`) | **COMPUTED** | `src/height.py` (`reg_certified`), `PROOF.md` §4 |
| 7 | Real period `Ω_E = 5.986917292463919259664019958905016355595167582…` certified to `< 2 × 10⁻⁴⁸` across 3 independent routes (AGM, Landen-hypergeometric, Jacobi theta) | **COMPUTED** | `src/period.py` (`omega_certified`), `PROOF.md` §5 |
| 8 | Newform coefficients `a_n` (`1 ≤ n ≤ 160`) agree between projective Weierstrass point counting and short-model Legendre character sums | **COMPUTED** | `src/a_n.py` (`build_table`), `PROOF.md` §6 |
| 9 | `L'(E, 1) = 0.305999773834052301820483683321676474452637774…` certified to `< 2 × 10⁻⁴⁸` with Deligne tail bound and Stieltjes CF overlap check | **COMPUTED** | `src/lprime.py` (`lprime_certified`), `PROOF.md` §6 |
| 10 | BSD ratio `R = L'(E, 1) / (Ω_E · Reg_E)` contains `1` within `< 10⁻⁴⁰` (actual width `< 10⁻⁴⁷`), and identity-component period `Ω_E/2` gives `2` | **COMPUTED** | `src/identity.py` (`verify_identity`), `PROOF.md` §7 |
| 11 | `#Sha(E/ℚ) = 1` for `37a1` | **CITED** | Gross–Zagier (1986), Kolyvagin (1988), Cremona `ecdata` (`data/ecdata-37a1.txt`) |
| 12 | The general Birch–Swinnerton-Dyer conjecture for all elliptic curves over `ℚ` | **OPEN** | `OPEN_REMAINDER.md` |
