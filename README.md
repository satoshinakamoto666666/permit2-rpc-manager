# BSD Counterexample Hunt: Generalized Rank-0 Verifier for Conductor $N \le 100$ (`bsd-rank0-100`)

Self-contained, zero-dependency verification repository generalizing the certified rank-0 BSD pipeline to **every rank-0 elliptic curve over $\mathbb{Q}$ of conductor $N \le 100$** (**284 rank-0 curves across 76 isogeny classes**, plus 22 rank-1 curves across 17 isogeny classes, totaling **306 curves across 93 isogeny classes** for $1 \le N \le 100$).

## Quick Start (One-Command Verification)

Requires only Python 3 (standard library) and `bash`:

```bash
./verify.sh                  # Runs all 7 verification steps across all 284 curves; exits 0
./tests/mutation_tests.sh    # Runs 10 planted corruptions; requires verify.sh to FAIL on each
```

## Summary of Family Results (`FAMILY_REPORT.md`)

- **Curves Checked**: All **284 rank-0 elliptic curves over $\mathbb{Q}$ of conductor $1 \le N \le 100$** (plus audit of the 22 rank-1 curves for $N \le 100$, totaling 306 curves).
- **Tamagawa Products $\prod_{p \mid \Delta} c_p$ (`src/tate.py`)**: Independently computed from $[a_1, a_2, a_3, a_4, a_6]$ via the complete 10-step Tate local reduction algorithm (`I_n`, `II`, `III`, `IV`, `I_0^*`, `I_m^*`, `IV^*`, `III^*`, `II^*`) — **284/284 exact matches** with Cremona's `allbsd` table.
- **Torsion Subgroups `#E(Q)_tors` (`src/torsion.py`)**: Independently proved via Lutz–Nagell depressed-cubic integer bisection ($T^3 - 3c_4 T - (2c_6 + 432 W^2) = 0$ over all $W \in \{0\} \cup \{d \ge 1 : d^2 \mid 16|\Delta|\}$) and $\mathbb{F}_p$-reduction divisibility — **284/284 exact matches**.
- **Real Periods $\Omega_E$ (`src/period.py`, `src/cert.py`)**: Certified in pure fixed-point integer interval arithmetic at scale $S = 10^{40}$ (`float`/`math` banned in `src/cert.py`) via 1-ULP root bisection of $T^3 - 3c_4 T - 2c_6 = 0$ and Gauss's AGM ($\Delta > 0$ and $\Delta < 0$ cases) — **284/284 certified matches**.
- **Central $L$-Values $L(E, 1)$ (`src/lval.py`)**: Certified across all 76 rank-0 isogeny classes via uniform minimal-model $\mathbb{F}_p$ point counting, Legendre character sum cross-checks, Hecke recursion ($n \le 115$), and the functional-equation series with Deligne tail bound $< 10^{-29}$ — **76/76 certified matches**.
- **Counterexample Hunt Outcome (`src/family_check.py`, `FAMILY_REPORT.md`)**:
  - **0 counterexamples / 0 mismatches** across all 284 rank-0 curves of conductor $N \le 100$.
  - **283 curves** have certified analytic Shafarevich–Tate order $\operatorname{Sha}_{\text{an}}(E/\mathbb{Q}) = 1 = 1^2$ (interval width $< 10^{-25}$).
  - **1 curve (`66b3`, $[1,1,1,-352,-2689]$, conductor $N = 66$)** has certified $\operatorname{Sha}_{\text{an}}(66\text{b}3/\mathbb{Q}) = 4 = 2^2$, verified alongside Cassels–Tate isogeny invariance across `66b1`–`66b4`.

## Repository Layout

- `src/cert.py`: Pure integer interval arithmetic (`S = 10^40`, `S_HI = 10^80`, `float`/`math` banned).
- `src/tate.py`: Complete 10-step Tate local reduction algorithm for Kodaira symbols and $c_p$.
- `src/torsion.py`: Exact Lutz–Nagell depressed-cubic bisection torsion prover.
- `src/period.py`: Certified real period $\Omega_E$ for both $\Delta > 0$ and $\Delta < 0$.
- `src/lval.py`: Certified $a_n(E)$ and $L(E, 1)$ with Deligne tail bound.
- `src/family_check.py`: End-to-end 284-curve verifier and `FAMILY_REPORT.md` generator.
- `data/allbsd_upto_100.txt`: Verbatim Cremona `allbsd` rows for all 306 curves of conductor $N \le 100$.
- `FAMILY_REPORT.md`: Complete 284-curve certified table + 22-curve rank-1 table.
- `PROOF.md`, `CLAIMS.md`, `OPEN_REMAINDER.md`: Mathematical proof and epistemic ledger.
- `verify.sh` & `tests/mutation_tests.sh`: Automated verification and 10-mutation test suite.
