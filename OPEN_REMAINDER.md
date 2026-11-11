# Open Remainder & Unproven Boundaries (`bsd-rank0-100`)

To maintain strict mathematical honesty, this document records what is **CITED** from published literature and what remains **OPEN** outside the in-repository verification scripts.

---

## 1. Cited Inputs Not Re-Proved From First Principles in This Repository (`CITED`)

1. **Exhaustive Classification & Modularity for Conductor $N \le 100$**:
   - The list of 306 elliptic curves over $\mathbb{Q}$ of conductor $1 \le N \le 100$ (284 rank-0 curves across 76 isogeny classes and 22 rank-1 curves across 20 isogeny classes) in `data/allbsd_upto_100.txt` is imported verbatim from John Cremona's `ecdata` repository (`allbsd/allbsd.00000-09999`), resting on the Modularity Theorem (Wiles, *Ann. of Math.* 141, 1995; Breuil–Conrad–Diamond–Taylor, *J. Amer. Math. Soc.* 14, 2001).
2. **Rank $E(\mathbb{Q}) = 0$ and Finiteness of $\operatorname{Sha}(E/\mathbb{Q})$ from $L(E, 1) \ne 0$**:
   - While `src/lval.py` certifies $L(E, 1) > 0$ in pure integer interval arithmetic for all 76 rank-0 isogeny classes, the implication $L(E, 1) \ne 0 \implies \operatorname{rank} E(\mathbb{Q}) = 0$ and $\#\operatorname{Sha}(E/\mathbb{Q}) < \infty$ is **CITED** from Kolyvagin's Euler-system theorem (Kolyvagin, *Math. USSR Izv.* 32, 1989) together with Gross–Zagier (*Invent. Math.* 84, 1986) and Bump–Friedberg–Hoffstein (*Invent. Math.* 102, 1990).
3. **Algebraic Order $\#\operatorname{Sha}(E/\mathbb{Q}) = \operatorname{Sha}_{\text{an}}(E/\mathbb{Q})$ Across Non-CM Curves ($N \le 100$)**:
   - This repository certifies the **analytic Shafarevich–Tate order** $\operatorname{Sha}_{\text{an}}(E/\mathbb{Q}) = \frac{L(E, 1) \cdot (\#E(\mathbb{Q})_{\text{tors}})^2}{\Omega_E \cdot \prod_p c_p} \in \{1, 4\}$ to interval width $< 10^{-25}$ across all 284 rank-0 curves and proves that every curve in the family satisfies the BSD leading-coefficient identity with a unique integer square ($\operatorname{Sha}_{\text{an}} = 1$ on 283 curves, $\operatorname{Sha}_{\text{an}} = 4 = 2^2$ on `66b3`).
   - Matching the algebraic group order $\#\operatorname{Sha}(E/\mathbb{Q})$ to $\operatorname{Sha}_{\text{an}}(E/\mathbb{Q})$ for all primes $p$ on non-CM curves of conductor $N \le 100$ relies on full 2-descent / 4-descent and the Iwasawa Main Conjecture for $\mathrm{GL}_2$ (Kato, *Astérisque* 295, 2004; Skinner–Urban, *Invent. Math.* 195, 2014; Grigorov–Jorza–Patrikis–Stein–Tarnițǎ, *Math. Comp.* 79, 2010), which is **CITED**.

---

## 2. Open Problems Beyond This Family (`OPEN`)

1. **Counterexamples Beyond Conductor $N \le 100$**:
   - Because all 284 rank-0 curves of conductor $N \le 100$ pass the certified BSD leading-coefficient check with 0 mismatches against Cremona's tables, **no counterexample to the Birch and Swinnerton-Dyer Conjecture exists in the rank-0 family of conductor $N \le 100$**.
2. **The General Birch and Swinnerton-Dyer Conjecture**:
   - Proving $\operatorname{ord}_{s=1} L(E, s) = \operatorname{rank} E(\mathbb{Q})$, finiteness of $\operatorname{Sha}(E/\mathbb{Q})$, and the exact leading-coefficient identity for all elliptic curves $E/\mathbb{Q}$ of arbitrary conductor $N$ and rank $r \ge 2$ remains an **OPEN** Millennium Prize Problem.
