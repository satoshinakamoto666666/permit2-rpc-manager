#!/usr/bin/env python3
"""
Unit & Integration Test Suite for `desci_mcp/intent_solver_mcp.py` (`test_intent_solver_mcp.py`)
================================================================================================
Tests:
1. ERC-8004 Trustless Agent Registration Card (`/.well-known/erc8004-agent.json`) with EIP-712
   signed Identity, Reputation, and Validation Registry manifests + Solana Ed25519 binding.
2. HTTP `402 Payment Required` & `PAYMENT-REQUIRED` headers across all 4 gated endpoints.
3. Base Mainnet USDC EIP-3009 `TransferWithAuthorization` (`0xe3ee160e`) payment verification & replay guard.
4. Solana Mainnet USDC Circle x402 Facilitator (`2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4`) payment & replay guard.
5. `solve_erc7683_cross_chain_intent` (Across V3, UniswapX, Relay.link, CoW `HooksTrampoline`).
6. `verify_bsd_elliptic_curve_invariants` (`66b3` Sha=4, `32a2` L/Omega=1/8, `37a1` rank-1, 306-curve catalog).
7. `audit_pr_bounty_compliance` (PR diff secret scan, unit test check, Algora/Polar claim metadata).
8. `generate_eas_offchain_attestation_pack` & MCP JSON-RPC 2.0 (`initialize`, `tools/list`, `tools/call`).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from eth_account import Account
from eth_account.messages import encode_typed_data
import nacl.signing

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from intent_solver_mcp import (
    BASE_CAIP2_NETWORK,
    BASE_CHAIN_ID,
    BASE_USDC_ADDRESS,
    CIRCLE_SOLANA_X402_FEE_PAYER,
    DeSciIntentSolverMCPCore,
    DeSciMCPRequestHandler,
    EIP3009_TRANSFER_WITH_AUTH_SELECTOR,
    ERC4337_CAIP10,
    EVM_AGENT_ADDRESS,
    EVM_CAIP10,
    SOLANA_AGENT_ADDRESS,
    SOLANA_CAIP10,
    SOLANA_CAIP2_NETWORK,
    SOLANA_USDC_MINT,
    ThreadedDeSciMCPHTTPServer,
    build_eip3009_typed_data,
)


def _make_eip3009_payment(
    payer_acct: Any,
    amount_atomic: int = 50000,
    to_addr: str = EVM_AGENT_ADDRESS,
    nonce_hex: Optional[str] = None,
) -> Dict[str, Any]:
    now = int(time.time())
    nonce = nonce_hex or ("0x" + os.urandom(32).hex())
    auth = {
        "from": payer_acct.address,
        "to": to_addr,
        "value": int(amount_atomic),
        "validAfter": now - 60,
        "validBefore": now + 600,
        "nonce": nonce,
    }
    typed_data = build_eip3009_typed_data(authorization=auth, chain_id=BASE_CHAIN_ID)
    signable = encode_typed_data(full_message=typed_data)
    signed = payer_acct.sign_message(signable)
    return {
        "x402Version": 2,
        "scheme": "exact",
        "network": BASE_CAIP2_NETWORK,
        "asset": BASE_USDC_ADDRESS,
        "payload": {
            "authorization": auth,
            "signature": "0x" + signed.signature.hex(),
        },
    }


def _make_solana_x402_payment(
    signing_key: nacl.signing.SigningKey,
    amount_atomic: int = 50000,
    pay_to: str = SOLANA_AGENT_ADDRESS,
    fee_payer: str = CIRCLE_SOLANA_X402_FEE_PAYER,
    nonce: Optional[str] = None,
) -> Dict[str, Any]:
    pubkey_hex = signing_key.verify_key.encode().hex()
    payer_id = f"SolBuyer_{pubkey_hex[:16]}"
    nonce_val = nonce or os.urandom(16).hex()
    msg = (
        f"x402-v2|solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp|"
        f"mint={SOLANA_USDC_MINT}|from={payer_id}|payTo={pay_to}|amount={amount_atomic}|"
        f"feePayer={fee_payer}|nonce={nonce_val}"
    ).encode("utf-8")
    sig_hex = signing_key.sign(msg).signature.hex()
    return {
        "x402Version": 2,
        "scheme": "exact",
        "network": SOLANA_CAIP2_NETWORK,
        "asset": SOLANA_USDC_MINT,
        "payload": {
            "transfer": {
                "from": payer_id,
                "payTo": pay_to,
                "asset": SOLANA_USDC_MINT,
                "amount": int(amount_atomic),
                "feePayer": fee_payer,
                "nonce": nonce_val,
                "publicKeyHex": pubkey_hex,
            },
            "signature": sig_hex,
            "publicKeyHex": pubkey_hex,
        },
    }


class TestDeSciIntentSolverMCP(unittest.TestCase):
    server: ThreadedDeSciMCPHTTPServer
    server_thread: threading.Thread
    base_url: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadedDeSciMCPHTTPServer(("127.0.0.1", 0), DeSciMCPRequestHandler)
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"
        cls.server.mcp_core = DeSciIntentSolverMCPCore(base_url=cls.base_url)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def _http_call(
        self,
        path: str,
        method: str = "GET",
        body: Any = None,
        headers: Any = None,
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        url = f"{self.base_url}{path}"
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)
        data_bytes = None
        if body is not None:
            data_bytes = json.dumps(body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, dict(resp.headers.items()), json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return err.code, dict(err.headers.items()), json.loads(err.read().decode("utf-8"))

    def test_01_erc8004_agent_registration_card_and_manifests(self) -> None:
        status, _, card = self._http_call("/.well-known/erc8004-agent.json")
        self.assertEqual(status, 200)
        self.assertTrue(card["allManifestsVerified"])
        self.assertIn(EVM_CAIP10, card["caip10Registrations"])
        self.assertIn(ERC4337_CAIP10, card["caip10Registrations"])
        self.assertIn(SOLANA_CAIP10, card["caip10Registrations"])

        manifests = card["erc8004Manifests"]
        self.assertTrue(manifests["identityManifest"]["proof"]["verified"])
        self.assertEqual(manifests["identityManifest"]["proof"]["signer"], EVM_AGENT_ADDRESS)
        self.assertTrue(manifests["reputationManifest"]["proof"]["verified"])
        self.assertTrue(manifests["validationManifest"]["proof"]["verified"])
        self.assertTrue(manifests["solanaCrossChainBinding"]["verified"])
        self.assertEqual(manifests["solanaCrossChainBinding"]["solana_address"], SOLANA_AGENT_ADDRESS)

    def test_02_http_402_payment_required_gates(self) -> None:
        for path, expected_atomic in [
            ("/v1/intents/erc7683-solve", "50000"),
            ("/v1/desci/bsd-verify", "50000"),
            ("/v1/bounties/audit-pr", "20000"),
            ("/v1/eas/offchain-attest", "20000"),
            ("/v1/desci/bsd-millennium-verify", "100000"),
            ("/v1/bounties/pr-merge-readiness", "50000"),
            ("/v1/erc4337/verify-paymaster-userop", "50000"),
            ("/v1/defi/liquidation-flash-arb-bundle", "80000"),
            ("/v1/solana/audit-jito-bundle-mtu", "50000"),
            ("/v1/identity/verify-w3c-vc-did", "50000"),
        ]:
            status, hdrs, body = self._http_call(path, method="POST", body={})
            self.assertEqual(status, 402)
            self.assertEqual(body["x402Version"], 2)
            self.assertIn("PAYMENT-REQUIRED", hdrs)
            accepts = body["accepts"]
            self.assertEqual(len(accepts), 2)
            self.assertEqual(accepts[0]["amount"], expected_atomic)
            self.assertEqual(accepts[0]["payTo"], EVM_AGENT_ADDRESS)
            self.assertEqual(accepts[1]["payTo"], SOLANA_AGENT_ADDRESS)

    def test_03_base_eip3009_payment_unlocks_erc7683_solver_and_blocks_replay(self) -> None:
        buyer = Account.create()
        payment = _make_eip3009_payment(buyer, amount_atomic=50000)
        b64_pay = base64.b64encode(json.dumps(payment).encode("utf-8")).decode("ascii")

        status, hdrs, body = self._http_call(
            "/v1/intents/erc7683-solve",
            method="POST",
            body={"origin_chain_id": 8453, "destination_chain_id": 42161, "amount_in_atomic": 500_000_000},
            headers={"PAYMENT-SIGNATURE": b64_pay},
        )
        self.assertEqual(status, 200)
        self.assertIn("PAYMENT-RESPONSE", hdrs)
        self.assertTrue(body["x402Receipt"]["valid"])
        self.assertTrue(body["x402Receipt"]["settlement_calldata"].startswith(EIP3009_TRANSFER_WITH_AUTH_SELECTOR))

        data = body["data"]
        self.assertEqual(data["tool"], "solve_erc7683_cross_chain_intent")
        self.assertEqual(len(data["solver_quotes_ranked"]), 3)
        self.assertTrue(data["erc7683_gasless_order"]["eip712_signature"]["verified"])
        self.assertIn("cow_hooks_trampoline_settlement", data)
        self.assertEqual(
            data["cow_hooks_trampoline_settlement"]["hooks_trampoline"],
            "0x60Bf78233f48e422eE3F101B9a0E0C8d68E68110",
        )

        # Replay with same nonce must fail with 402
        r_status, _, r_body = self._http_call(
            "/v1/intents/erc7683-solve",
            method="POST",
            body={},
            headers={"PAYMENT-SIGNATURE": b64_pay},
        )
        self.assertEqual(r_status, 402)
        self.assertIn("Replay detected", r_body.get("verificationError", ""))

    def test_04_solana_x402_payment_unlocks_bsd_verifier_and_blocks_replay(self) -> None:
        sol_buyer = nacl.signing.SigningKey.generate()
        payment = _make_solana_x402_payment(sol_buyer, amount_atomic=50000)
        b64_pay = base64.b64encode(json.dumps(payment).encode("utf-8")).decode("ascii")

        status, hdrs, body = self._http_call(
            "/v1/desci/bsd-verify",
            method="POST",
            body={"curve_label": "66b3"},
            headers={"X-PAYMENT": b64_pay},
        )
        self.assertEqual(status, 200)
        self.assertIn("PAYMENT-RESPONSE", hdrs)
        data = body["data"]
        self.assertEqual(data["curve_label"], "66b3")
        self.assertEqual(data["certified_intervals_scale_10_40"]["certified_analytic_sha_integer"], 4)
        self.assertTrue(data["certified_intervals_scale_10_40"]["cassels_tate_positive_square"])
        self.assertTrue(data["eip712_proof_certificate"]["verified"])
        self.assertEqual(data["family_database_summary"]["total_curves_in_database"], 306)
        self.assertEqual(data["family_database_summary"]["rank_0_curves_certified"], 284)
        self.assertEqual(data["family_database_summary"]["rank_1_curves_certified"], 22)

        # Replay must fail with 402
        r_status, _, _ = self._http_call(
            "/v1/desci/bsd-verify",
            method="POST",
            body={"curve_label": "66b3"},
            headers={"X-PAYMENT": b64_pay},
        )
        self.assertEqual(r_status, 402)

    def test_05_bsd_verifier_32a2_and_rank1_37a1(self) -> None:
        core = self.server.mcp_core
        res_32a2 = core.verify_bsd_elliptic_curve_invariants(curve_label="32a2", include_family_summary=False)
        self.assertEqual(res_32a2["curve_label"], "32a2")
        self.assertEqual(res_32a2["rational_torsion_lutz_nagell"]["torsion_order"], 4)
        self.assertEqual(res_32a2["tate_local_reduction"]["tamagawa_product_prod_cp"], 2)
        self.assertEqual(res_32a2["certified_intervals_scale_10_40"]["certified_analytic_sha_integer"], 1)
        self.assertAlmostEqual(
            float(res_32a2["certified_intervals_scale_10_40"]["l_over_omega_ratio"]),
            0.125,
            places=12,
        )

        res_37a1 = core.verify_bsd_elliptic_curve_invariants(curve_label="37a1", include_family_summary=False)
        self.assertEqual(res_37a1["curve_label"], "37a1")
        self.assertEqual(res_37a1["analytic_rank"], 1)
        self.assertEqual(res_37a1["rational_torsion_lutz_nagell"]["torsion_order"], 1)
        self.assertEqual(res_37a1["tate_local_reduction"]["tamagawa_product_prod_cp"], 1)
        self.assertTrue(res_37a1["eip712_proof_certificate"]["verified"])

    def test_06_audit_pr_bounty_compliance(self) -> None:
        core = self.server.mcp_core
        res = core.audit_pr_bounty_compliance(repository="rohitdash08/FinMind", issue_number=144)
        self.assertEqual(res["compliance_score"], 100)
        self.assertTrue(res["compliant"])
        self.assertTrue(res["eip712_audit_receipt"]["verified"])
        self.assertGreater(res["workspace_bounty_portfolio_summary"]["total_live_prs_indexed"], 20)

        # Verify secret leak detection lowers compliance score
        synthetic_tok = "gh" + "p_" + ("a1b2" * 6)
        bad_res = core.audit_pr_bounty_compliance(
            repository="custom/repo",
            issue_number=99,
            claim_command="/claim #99",
            files_changed=["src/app.py", "tests/test_app.py"],
            tests_passed=3,
            diff_snippet=f"token = '{synthetic_tok}'",
        )
        self.assertFalse(bad_res["compliance_checks"]["zero_secret_leaks"])
        self.assertLess(bad_res["compliance_score"], 100)

    def test_07_generate_eas_offchain_attestation_pack(self) -> None:
        core = self.server.mcp_core
        pack = core.generate_eas_offchain_attestation_pack(chains=["base", "optimism", "arbitrum"])
        self.assertEqual(pack["total_attestations"], 3)
        self.assertTrue(pack["all_signatures_verified"])
        chains_seen = {a["chain"] for a in pack["attestations"]}
        self.assertEqual(chains_seen, {"base", "optimism", "arbitrum"})
        for att in pack["attestations"]:
            self.assertTrue(att["uid"].startswith("0x"))
            self.assertEqual(len(att["uid"]), 66)
            self.assertIn("offchain/url/#attestation=", att["easscan_verification_url"])

    def test_08_mcp_jsonrpc_20_protocol_all_ten_tools(self) -> None:
        init_status, _, init_resp = self._http_call(
            "/mcp",
            method="POST",
            body={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        self.assertEqual(init_status, 200)
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "desci-mcp-monetizer")
        self.assertEqual(init_resp["result"]["serverInfo"]["version"], "2.2.0")

        list_status, _, list_resp = self._http_call(
            "/mcp",
            method="POST",
            body={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        self.assertEqual(list_status, 200)
        tool_names = [t["name"] for t in list_resp["result"]["tools"]]
        self.assertEqual(
            tool_names,
            [
                "solve_erc7683_cross_chain_intent",
                "verify_bsd_elliptic_curve_invariants",
                "audit_pr_bounty_compliance",
                "generate_eas_offchain_attestation_pack",
                "verify_bsd_millennium_proof_bundle",
                "audit_github_bounty_pr_merge_readiness",
                "verify_erc4337_paymaster_userop_bundle",
                "scan_multichain_liquidation_and_flash_arb_bundle",
                "audit_solana_jito_flash_bundle_mtu",
                "verify_cross_chain_w3c_vc_did_proof",
            ],
        )

        for idx, (t_name, t_args) in enumerate(
            [
                ("solve_erc7683_cross_chain_intent", {"origin_chain_id": 8453, "destination_chain_id": 10}),
                ("verify_bsd_elliptic_curve_invariants", {"curve_label": "66b3"}),
                ("audit_pr_bounty_compliance", {"repository": "rohitdash08/FinMind", "issue_number": 144}),
                ("generate_eas_offchain_attestation_pack", {"chains": ["base"]}),
                ("verify_bsd_millennium_proof_bundle", {"bounty_id": "bnty_0573", "include_featured_curves": False}),
                ("audit_github_bounty_pr_merge_readiness", {"repository": "rohitdash08/FinMind"}),
                ("verify_erc4337_paymaster_userop_bundle", {"chain_id": 8453}),
                ("scan_multichain_liquidation_and_flash_arb_bundle", {"min_profit_usd": 0.5}),
                ("audit_solana_jito_flash_bundle_mtu", {"max_mtu_bytes": 1232}),
                ("verify_cross_chain_w3c_vc_did_proof", {}),
            ],
            start=10,
        ):
            c_status, _, c_resp = self._http_call(
                "/mcp",
                method="POST",
                body={
                    "jsonrpc": "2.0",
                    "id": idx,
                    "method": "tools/call",
                    "params": {"name": t_name, "arguments": t_args},
                },
            )
            self.assertEqual(c_status, 200)
            self.assertFalse(c_resp["result"]["isError"])
            self.assertEqual(c_resp["result"]["structuredContent"]["tool"], t_name)

    def test_09_verify_bsd_millennium_proof_bundle(self) -> None:
        core = self.server.mcp_core
        res = core.verify_bsd_millennium_proof_bundle(bounty_id="bnty_0573", include_featured_curves=True)
        self.assertEqual(res["tool"], "verify_bsd_millennium_proof_bundle")
        self.assertEqual(res["certified_census_summary"]["total_curves_certified"], 306)
        self.assertEqual(res["certified_census_summary"]["rank_0_curves_certified"], 284)
        self.assertEqual(res["certified_census_summary"]["rank_1_curves_certified"], 22)
        self.assertEqual(res["certified_census_summary"]["rank_0_isogeny_classes"], 76)
        self.assertEqual(res["certified_census_summary"]["sha_order_1_rank0_curves"], 283)
        self.assertIn("66b3", res["certified_census_summary"]["sha_order_4_rank0_curves"])
        self.assertTrue(res["eip712_millennium_certificate"]["verified"])

    def test_10_audit_github_bounty_pr_merge_readiness(self) -> None:
        core = self.server.mcp_core
        res = core.audit_github_bounty_pr_merge_readiness()
        self.assertEqual(res["tool"], "audit_github_bounty_pr_merge_readiness")
        self.assertGreater(res["portfolio_summary"]["total_live_prs_indexed"], 20)
        self.assertGreater(res["portfolio_summary"]["merge_ready_prs_count"], 10)
        self.assertTrue(res["eip712_merge_readiness_certificate"]["verified"])

    def test_11_verify_erc4337_paymaster_userop_bundle(self) -> None:
        core = self.server.mcp_core
        res = core.verify_erc4337_paymaster_userop_bundle(chain_id=8453)
        self.assertEqual(res["tool"], "verify_erc4337_paymaster_userop_bundle")
        self.assertEqual(res["entry_point_v07"], "0x0000000071727De22E5E9d8BAf0edAc6f37da032")
        self.assertEqual(len(res["packed_user_operation"]["accountGasLimits"]), 66)
        self.assertEqual(len(res["packed_user_operation"]["gasFees"]), 66)
        self.assertTrue(res["eip712_paymaster_certificate"]["verified"])

    def test_12_scan_multichain_liquidation_and_flash_arb_bundle(self) -> None:
        core = self.server.mcp_core
        res = core.scan_multichain_liquidation_and_flash_arb_bundle(min_profit_usd=0.5)
        self.assertEqual(res["tool"], "scan_multichain_liquidation_and_flash_arb_bundle")
        self.assertGreaterEqual(res["summary"]["profitable_flash_arbs_count"], 1)
        self.assertTrue(res["eip712_bundle_certificate"]["verified"])

    def test_13_audit_solana_jito_flash_bundle_mtu(self) -> None:
        core = self.server.mcp_core
        res = core.audit_solana_jito_flash_bundle_mtu(max_mtu_bytes=1232)
        self.assertEqual(res["tool"], "audit_solana_jito_flash_bundle_mtu")
        self.assertTrue(res["mtu_audit_summary"]["all_bundles_within_1232_mtu"])
        self.assertGreaterEqual(res["mtu_audit_summary"]["total_2leg_spreads_audited"], 1)
        self.assertTrue(res["eip712_mtu_audit_certificate"]["verified"])

    def test_14_verify_cross_chain_w3c_vc_did_proof(self) -> None:
        core = self.server.mcp_core
        res = core.verify_cross_chain_w3c_vc_did_proof()
        self.assertEqual(res["tool"], "verify_cross_chain_w3c_vc_did_proof")
        self.assertTrue(res["verified_credential_counts"]["all_proofs_valid"])
        self.assertGreaterEqual(res["verified_credential_counts"]["eas_offchain_v2_attestations"], 12)
        self.assertTrue(res["eip712_w3c_did_certificate"]["verified"])


if __name__ == "__main__":
    unittest.main()
