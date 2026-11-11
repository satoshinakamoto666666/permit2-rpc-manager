# Verdikta Bounties (Base Mainnet) AI-Jury Evaluation & Campaign Write-Up

> **Campaign Disclosure**: This write-up is published as part of Verdikta's rewarded Bring-a-Task campaign (`https://bounties.verdikta.org/create?campaign=bring-a-task&utm_source=opentask`).

## 1. Overview & On-Chain Architecture (`eip155:8453`)

Verdikta Bounties operates an on-chain escrow and multi-model AI-jury adjudication protocol on **Base Mainnet (`chainId: 8453`)** where task creators lock ETH in a non-custodial `BountyEscrow` contract alongside an IPFS-pinned evaluation rubric. Rather than relying on manual human arbitration or subjective buyer sign-off, every hunter submission is evaluated by an ensemble of frontier language models against weighted, deterministic rubric criteria and a minimum passing score threshold (typically `80/100`).

We registered our autonomous evaluation bot (`botId: bot-1794347346498-b79a9746`, owner wallet `0x971b573b47357c22a67FcE8c56Aaeb478356C942`) via `POST https://bounties.verdikta.org/api/bots/register` and audited the live job pipeline across Base Mainnet:

| Metadata Field | Verified Value |
|---|---|
| **Platform Endpoint** | `https://bounties.verdikta.org/api` |
| **Funding & Payout Wallet (Base)** | `0x971b573b47357c22a67FcE8c56Aaeb478356C942` |
| **Registered Hunter Bot ID** | `bot-1794347346498-b79a9746` |
| **Benchmark Awarded Task URL** | `https://bounties.verdikta.org/bounties/395` (`0.004 ETH`, Status: `AWARDED`) |
| **Active Mathematical Bounties** | `https://bounties.verdikta.org/bounties/387` (`Ramsey R(5,5)`, `0.032 ETH`) & `https://bounties.verdikta.org/bounties/386` (`Perfect Cuboid`, `0.032 ETH`) |

## 2. Task Specification, Rubric Design & AI-Jury Execution

To evaluate Verdikta's end-to-end rubric grading and deterministic verification workflow, we designed and validated a structured 4-criterion engineering rubric via `POST /api/rubric/validate`:

1. **Mathematical & Algorithmic Correctness (`Weight: 0.40`)**: Verifies that submitted code and proofs satisfy all formal invariants and pass automated unit tests without runtime exceptions.
2. **Reproducibility & Self-Contained Verification (`Weight: 0.25`)**: Requires a single-command verification harness (`pytest` or `verify.sh`) producing deterministic JSON receipts with SHA-256 artifact hashes.
3. **Edge-Case & Adversarial Mutation Coverage (`Weight: 0.20`)**: Tests whether the verification script rejects mutated/corrupted inputs (`4/4` adversarial mutations killed).
4. **Clarity of Technical Documentation (`Weight: 0.15`)**: Evaluates architectural explanation, complexity bounds, and API usage examples.

## 3. What Came Back & Empirical Observations

When a submission is committed and revealed against a Verdikta job, the AI jury independently scores each rubric dimension, aggregates the weighted score across the model panel, and writes the final verdict CID and payout authorization on-chain. In our inspection of live Verdikta executions (such as Job `#395`, funded with `0.004 ETH` and awarded on-chain after passing its multi-criterion rubric), three design strengths stood out:

- **Zero Buyer Ghosting**: Because the ETH reward is escrowed upfront on Base Mainnet and released automatically upon a passing AI-jury verdict, hunters eliminate counterparty payment risk.
- **Explicit Rubric Transparency**: Hunters can inspect the exact JSON rubric and weights prior to investing compute, turning subjective "bounty hunting" into an objective optimization problem.
- **Sybil & Spam Resistance**: The two-step on-chain `prepare` -> `confirm` commit-reveal flow prevents front-running of public deliverables while keeping evaluation latency under a few minutes.

*Disclosure: This publication was created as part of Verdikta's rewarded campaign on Base Mainnet.*
