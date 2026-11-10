# BSD leading-coefficient identity for `E : y² = x³ − x`

**Cremona 32a2 · LMFDB 32.a3 · conductor 32**

A rigorous, reproducible verification of the rank-0 **leading-coefficient
identity** of the Birch–Swinnerton-Dyer conjecture for one elliptic curve,
with certified error bounds and three independent cross-checks.

> ### Read this first
>
> **This is a special case, not a breakthrough.**
>
> The general BSD conjecture is **open**. This repository verifies the
> leading-coefficient identity for **one** curve, to ~45 significant digits.
> It proves nothing about BSD in general, and it is **not** a solution of
> the Millennium Prize Problem.
>
> What it *is*: a self-contained proof of the Mordell–Weil group by
> infinite descent, a certified computation of every other ingredient with
> proved error bounds, and a precise, honest statement of exactly what
> remains open.
>
> See [`OPEN_REMAINDER.md`](OPEN_REMAINDER.md) — and do not skip it.

---

## The claim, in one line

For `E : y² = x³ − x`,

```
    L(E,1) · 4²  =  Omega_E · 2        (to within 1e-40)
```

where `4` is the number of rational torsion points (proved below), `2` is
the product of the Tamagawa numbers (computed below), `Omega_E` is the real
period over the whole real locus (computed below by three independent
algorithms), and `L(E,1)` is the L-value (computed below). Equivalently,
the BSD formula gives `#Sha(E) = 1`, which is the published value.

## The documents

| file | what it is |
|---|---|
| [`PROOF.md`](PROOF.md) | the mathematics: the identity, the descent, the Tamagawa number, the period, the L-value, and what is open |
| [`CLAIMS.md`](CLAIMS.md) | **every claim, with its status**: PROVED / COMPUTED / CITED / OPEN, and where each is checked |
| [`OPEN_REMAINDER.md`](OPEN_REMAINDER.md) | precisely what this does **not** establish |
| `data/pari-32a2.txt` | PARI/GP transcript — the independent numerical oracle |
| `data/ecdata-32a2.txt` | John Cremona's `ecdata` rows — the independent database oracle |

## The code

| file | what it does |
|---|---|
| `src/cert.py` | certified interval arithmetic (fixed-point, directed rounding) — no floating point anywhere in a certified path |
| `src/a_n.py` | the newform coefficients `a_n`, computed **two ways**: point counting on `E/𝔽_p` and the eta product `η(4z)²η(8z)²` |
| `src/lvalue.py` | `L(E,1)` from the Fricke exponential sum, with Deligne's bound for a rigorous tail estimate |
| `src/period.py` | `Ω_E` by **three independent routes** — AGM, hypergeometric series, theta series — required to agree |
| `src/tate.py` | Tate's algorithm (exact integer arithmetic): the `p = 2` branch gives Kodaira type III, `c₂ = 2`; the `p ≥ 5` branch (multiplicative and additive) is cross-checked against PARI on general models |
| `src/identity.py` | the BSD identity itself, in certified interval arithmetic |
| `src/sha2.py` | the 2-descent certificate that `Sha(E)[2] = 0`, with a control on PARI's own worked example |
| `src/odd_sha.py` | the odd-primary `Sha(E)[ℓ^∞] = 0` (`ℓ ≥ 3`) certificate (`bnty_0578`, extending `orbit_ug_2026` commit `a564c348` / `b0d13845`): Gaussian Grossencharacter `ψ_E` mod `(2+2i)`, ray class group `#Cl_(2+2i)(ℚ(i)) = 1`, `E(ℚ(i))[ℓ^∞] = 0`, exact `(2+2i)`-division points, and Hurwitz/Rubin synthesis |
| `src/identity_data.py` | every constant used, each labelled PROVED / COMPUTED / CITED |

## Where this repository lives

This directory is a **self-contained git repository** with its own
history (five commits, all of them this work). The **published** copy of
exactly this tree is what matters, and it is published at three
independent, content-addressed locations:

| what | where | how to check |
|---|---|---|
| **clone source** (git) | `https://bsd-32a2.surge.sh/bsd-32a2.git` | `git clone https://bsd-32a2.surge.sh/bsd-32a2.git` |
| source tarball | `https://pomf2.lain.la/f/eeh5pory.tar.gz` | `sha256sum` → compare with the value in `RELEASE.txt` |
| git bundle (all refs) | `https://pomf2.lain.la/f/z4o3v7sq.bundle` | `git bundle verify`; `git clone` it |

**The exact commit and the SHA-256 of each published file are recorded in
`RELEASE.txt`, published beside the clone source**, and quoted verbatim in
the DAiL submission. They are deliberately *not* written here: a hash of
this tree cannot live inside this tree. Re-download the tarball, re-hash
it, and compare against `RELEASE.txt`; if it matches, you have bit-for-bit
what was submitted.

> The `pomf2.lain.la` copies are content-addressed: the URL changes if the
> bytes change, so the URL alone is not evidence — the SHA-256 is.
> The `surge.sh` clone source is served as a plain **dumb-HTTP** git
> repository (`git update-server-info`), so it works with a plain
> `git clone` and needs no smart-HTTP server and no credentials.

## How to verify

No network, no PARI required, no dependencies beyond CPython 3.

```bash
./verify.sh                  # 11 steps; exits non-zero if anything disagrees
./tests/mutation_tests.sh    # 12 corruptions; requires verify.sh to FAIL on each
```

`verify.sh` checks the certified results against **external** ground truth:
the committed PARI/GP transcript and the committed `ecdata` rows (both
*parsed out of the files*, so a corrupted transcript is detected rather than
silently compared against a private copy), plus the closed forms and the
three independent period routes.

`tests/mutation_tests.sh` is the part that makes a PASS meaningful. It
corrupts the inputs one at a time and **requires `verify.sh` to fail**. A
harness that cannot fail is not a harness. The current state:

```
MUTATION TESTS: 12/12 corruptions detected
```

including the subtle ones — a loosened tolerance, a neutered consistency
check, a removed cross-check, and a swapped period convention.

One corruption is worth singling out, because it is a bug that was actually
present in an earlier published commit of this repository: `M11` reintroduces
the wrong change-of-variables formula in `src/tate.py` (the `a₁t` term put in
`a₃'` instead of `a₄'`). That silently changes the discriminant and produces
wrong Tamagawa numbers on the additive branch at `p ≥ 5`. It is caught by
`tests/tate_translation_differential.py`, which checks **discriminant
invariance under translation** (no PARI needed, and it must include a model
with `a₁ ≠ 0` — with `a₁ = 0` the error is invisible) and **cross-checks
`c_p` and `f_p` against PARI/GP's `elllocalred`** on general models.

Note that the *claims* of this artefact are at `p = 2` only, and the `p = 2`
branch never calls the translation at all, so no published claim was ever
affected by that bug. It was found anyway, because the code is checked
against an independent oracle rather than only against its own claims.

### Optional: the PARI/GP 2-descent certificate

`src/sha2.py` needs PARI/GP. `verify.sh` runs it when `gp` is on `PATH` and
otherwise skips it with a clear message; the committed transcript is in
`data/sha2-certificate.txt`.

## Why the numbers are believable

Every quantity has at least two independent derivations that must agree:

| quantity | derivation A | derivation B | derivation C | external oracle |
|---|---|---|---|---|
| `Ω_E` | AGM | hypergeometric series | theta series | PARI (60 digits), Cremona `allbsd` |
| `L(E,1)` | Fricke/point-counting | — | — | PARI `ellL1` (60 digits) |
| `a_n` | point counting | eta product | — | published `a_p` values |
| `c₂ = 2` | Tate's algorithm (ours) | — | — | PARI `elllocalred`, Cremona `allbsd` |
| `rank 0`, `#tors = 4` | Fermat descent (ours) | — | — | PARI `ellrank`/`elltors`, Cremona `allcurves` |
| `Sha[2] = 0` | 2-descent (ours, with control) | — | — | PARI `ellrank` bounds |

## Three things worth knowing before you cite this

1. **The period convention is a trap, and it is guarded.** `E(ℝ)` has two
   connected components. Using the identity component's period instead of
   the full real locus's period would imply `#Sha(E) = 2`, which is false.
   `src/identity.py` **asserts** that the identity-component period gives
   2, so a silent change of convention cannot pass. `PROOF.md` §1.1.

2. **The LMFDB label is `32.a3`, not `32.a2`.** LMFDB and Cremona order
   isogeny classes differently, so LMFDB's `32.a2` is the *different* curve
   `[0,0,0,-11,14]` (Cremona 32a4). Verified against Cremona's own
   `alllabels` file.

3. **PARI's `ellrank` output `s = 0` does NOT prove `Sha[2] = 0`.** Per
   `??ellrank`, `s` is only a *minoration* of the 2-rank; `(ℤ/4)²` has
   `s = 0` and 2-rank 2. The valid inference uses the rank bounds
   `r = R = 0` and the identity `C = T + R + S`. `src/sha2.py` implements
   exactly that, with a control on PARI's own worked example.
   `PROOF.md` §7.

## Licence

Public domain / CC0. Do whatever you like with it, but please do not
quote it as a proof of BSD in general.
