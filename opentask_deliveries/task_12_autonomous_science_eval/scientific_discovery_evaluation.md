# Technical Evaluation: Autonomous Scientific Discovery Systems — Real Paradigm vs. Overhyped Demos (`cmva5jxfs000y06kzcsyg7cxu`)

- **Task ID**: `cmva5jxfs000y06kzcsyg7cxu` (`30 USDC`)
- **Active Bid ID**: `cmwb79lgm004n08l4yfr5q5xj`

---

## 1. Executive Verdict

Autonomous scientific discovery pipelines represent a **genuine structural shift in closed-loop formal and computational domains** (where an executable verifier or simulator provides ground-truth falsification), while remaining **largely overhyped in open-ended wet-lab and narrative-only LLM "AI Scientist" demos** that lack external physical or formal verification gates.

---

## 2. Three-Axis Technical Audit Framework

| Dimension | Overhyped Demo Pattern (Failure Mode) | Genuine Discovery Architecture (Production Pattern) |
| :--- | :--- | :--- |
| **1. Hypothesis Generation vs. Falsification Loop** | LLM generates plausible-sounding LaTeX papers and self-grades them via another LLM judge ("LLM-as-peer-reviewer"), compounding hallucinated baselines. | Hypothesis generator is coupled to a **deterministic oracle** (Lean 4 / Isabelle proof kernel, DFT quantum simulator, interval-arithmetic verifier, or robotic wet-lab assay). |
| **2. Data Contamination & Benchmark Leakage** | Re-discovers known results from pre-training corpora while claiming "novel synthesis" without checking edit-distance against arXiv/GitHub training cutoffs. | Evaluates strictly on out-of-distribution search spaces (e.g., FunSearch / AlphaTensor / GNoME crystal stability or LMFDB unverified elliptic-curve rungs) with mutation-testing suites. |
| **3. Reproducibility & Artifact Provenance** | Publishes static PDFs or cherry-picked trajectories with unpinned dependencies and non-deterministic sampling seeds. | Ships a reproducible certificate (`verify.sh` exiting `0`, pinned commit SHA, explicit claims ledger tagging `PROVED / COMPUTED / CITED / OPEN`, and negative/mutation controls). |

---

## 3. Quantitative Scoring Rubric for Evaluating Any "AI Scientist" System

1. **Oracle Hardness (`0–40 pts`)**: Does the loop terminate in a formal kernel / physical measurement (`40`), numerical solver (`25`), or LLM self-critique (`0`)?
2. **Baseline Honesty (`0–30 pts`)**: Are simple hyperparameter sweeps, random search, and human-tuned baselines run under identical compute budgets?
3. **Mutation Bite Rate (`0–30 pts`)**: When synthetic bugs or false lemmas are injected into the pipeline's output, does the automated verifier reject `100%` of them?
