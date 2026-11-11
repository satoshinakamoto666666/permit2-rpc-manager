#!/usr/bin/env python3
"""
Solana Mainnet-Beta SPL USDC End-to-End Payment Automation & Verifier
Task ID: cmmb1pfk7000iju041ts0528g ($5 USDC — "Solana USDC automation: Need a small Solana automation/check that verifies payments end-to-end.")
"""

from __future__ import annotations
import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

SOLANA_MAINNET_USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SPL_TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SPL_ASSOCIATED_TOKEN_PROGRAM_ID = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
OUR_SOLANA_WALLET = "Aw2hhJvjewAcxssyWMzKmFge6jWxEzN6GiFQgyZNKakt"

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_MAP = {c: i for i, c in enumerate(_B58_ALPHABET)}


def b58decode(s: str) -> bytes:
    num = 0
    for ch in s:
        num = num * 58 + _B58_MAP[ch]
    raw = num.to_bytes((num.bit_length() + 7) // 8, "big") if num > 0 else b""
    leading_zeros = len(s) - len(s.lstrip("1"))
    return (b"\x00" * leading_zeros) + raw


def b58encode(b: bytes) -> str:
    num = int.from_bytes(b, "big")
    chars: List[str] = []
    while num > 0:
        num, rem = divmod(num, 58)
        chars.append(_B58_ALPHABET[rem])
    leading_zeros = len(b) - len(b.lstrip(b"\x00"))
    return ("1" * leading_zeros) + "".join(reversed(chars))


# Ed25519 field arithmetic to check whether a 32-byte point lies on the Ed25519 curve
_ED25519_P = 2**255 - 19
_ED25519_D = (-121665 * pow(121666, _ED25519_P - 2, _ED25519_P)) % _ED25519_P


def is_on_ed25519_curve(point_bytes: bytes) -> bool:
    if len(point_bytes) != 32:
        return False
    y = int.from_bytes(point_bytes, "little") & ((1 << 255) - 1)
    if y >= _ED25519_P:
        return False
    y2 = (y * y) % _ED25519_P
    u = (y2 - 1) % _ED25519_P
    v = (_ED25519_D * y2 + 1) % _ED25519_P
    x2 = (u * pow(v, _ED25519_P - 2, _ED25519_P)) % _ED25519_P
    if x2 == 0:
        return True
    euler = pow(x2, (_ED25519_P - 1) // 2, _ED25519_P)
    return euler == 1


def derive_associated_token_address(
    owner_address: str,
    mint_address: str = SOLANA_MAINNET_USDC_MINT,
    token_program_id: str = SPL_TOKEN_PROGRAM_ID,
    ata_program_id: str = SPL_ASSOCIATED_TOKEN_PROGRAM_ID,
) -> Tuple[str, int]:
    """
    Deterministically derive the canonical Solana Associated Token Account (ATA) PDA
    and bump seed (`255` down to `0`) without external Solana SDK dependencies.
    """
    owner_bytes = b58decode(owner_address)
    token_prog_bytes = b58decode(token_program_id)
    mint_bytes = b58decode(mint_address)
    ata_prog_bytes = b58decode(ata_program_id)

    for bump in range(255, -1, -1):
        h = hashlib.sha256()
        h.update(owner_bytes)
        h.update(token_prog_bytes)
        h.update(mint_bytes)
        h.update(bytes([bump]))
        h.update(ata_prog_bytes)
        h.update(b"ProgramDerivedAddress")
        candidate = h.digest()
        if not is_on_ed25519_curve(candidate):
            return b58encode(candidate), bump
    raise RuntimeError("Failed to find valid off-curve PDA bump for ATA")


@dataclass
class PaymentVerificationResult:
    verified: bool
    signature: str
    recipient_wallet: str
    recipient_ata: str
    mint: str
    expected_amount_usdc: str
    actual_received_usdc: str
    sender_wallets: List[str]
    memo: Optional[str]
    slot: Optional[int]
    block_time: Optional[int]
    reason: str


def verify_parsed_solana_usdc_tx(
    tx_response: Dict[str, Any],
    recipient_wallet: str,
    expected_amount_usdc: Decimal | float | str,
    expected_memo: Optional[str] = None,
    mint: str = SOLANA_MAINNET_USDC_MINT,
) -> PaymentVerificationResult:
    """
    Verify a `getTransaction(encoding='jsonParsed')` Solana RPC payload end-to-end:
    1. Transaction exists and `meta.err` is None.
    2. Computes exact atomic SPL balance delta for `recipient_wallet` on `mint` across `preTokenBalances` and `postTokenBalances`.
    3. Confirms `actual_received_usdc >= expected_amount_usdc`.
    4. Optionally verifies SPL Memo (`MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`) content.
    """
    expected_dec = Decimal(str(expected_amount_usdc))
    ata_addr, _ = derive_associated_token_address(recipient_wallet, mint)
    sig = ""
    tx_inner = tx_response.get("transaction", {})
    sigs = tx_inner.get("signatures", [])
    if sigs:
        sig = sigs[0]

    meta = tx_response.get("meta")
    if not meta:
        return PaymentVerificationResult(
            False, sig, recipient_wallet, ata_addr, mint, str(expected_dec), "0", [], None, None, None, "Missing transaction meta"
        )
    if meta.get("err") is not None:
        return PaymentVerificationResult(
            False, sig, recipient_wallet, ata_addr, mint, str(expected_dec), "0", [], None, tx_response.get("slot"), tx_response.get("blockTime"), f"On-chain transaction failed: {meta.get('err')}"
        )

    pre_bals = meta.get("preTokenBalances", [])
    post_bals = meta.get("postTokenBalances", [])

    pre_by_owner: Dict[str, int] = {}
    post_by_owner: Dict[str, int] = {}

    for entry in pre_bals:
        if entry.get("mint") == mint:
            owner = entry.get("owner", "")
            amt = int(entry.get("uiTokenAmount", {}).get("amount", "0"))
            pre_by_owner[owner] = pre_by_owner.get(owner, 0) + amt

    for entry in post_bals:
        if entry.get("mint") == mint:
            owner = entry.get("owner", "")
            amt = int(entry.get("uiTokenAmount", {}).get("amount", "0"))
            post_by_owner[owner] = post_by_owner.get(owner, 0) + amt

    pre_recipient = pre_by_owner.get(recipient_wallet, 0)
    post_recipient = post_by_owner.get(recipient_wallet, 0)
    delta_atomic = post_recipient - pre_recipient
    actual_dec = Decimal(delta_atomic) / Decimal(1_000_000)

    senders = [
        owner
        for owner, pre_amt in pre_by_owner.items()
        if post_by_owner.get(owner, 0) < pre_amt and owner != recipient_wallet
    ]

    extracted_memo: Optional[str] = None
    instructions = tx_inner.get("message", {}).get("instructions", [])
    for ix in instructions:
        if ix.get("program") == "spl-memo" or ix.get("programId") == "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr":
            parsed_val = ix.get("parsed")
            if isinstance(parsed_val, str):
                extracted_memo = parsed_val

    if expected_memo is not None and extracted_memo != expected_memo:
        return PaymentVerificationResult(
            False,
            sig,
            recipient_wallet,
            ata_addr,
            mint,
            str(expected_dec),
            str(actual_dec),
            senders,
            extracted_memo,
            tx_response.get("slot"),
            tx_response.get("blockTime"),
            f"Memo mismatch: expected '{expected_memo}', got '{extracted_memo}'",
        )

    if actual_dec < expected_dec:
        return PaymentVerificationResult(
            False,
            sig,
            recipient_wallet,
            ata_addr,
            mint,
            str(expected_dec),
            str(actual_dec),
            senders,
            extracted_memo,
            tx_response.get("slot"),
            tx_response.get("blockTime"),
            f"Insufficient USDC received: expected {expected_dec} USDC, got {actual_dec} USDC",
        )

    return PaymentVerificationResult(
        True,
        sig,
        recipient_wallet,
        ata_addr,
        mint,
        str(expected_dec),
        str(actual_dec),
        senders,
        extracted_memo,
        tx_response.get("slot"),
        tx_response.get("blockTime"),
        "Verified SPL USDC payment end-to-end",
    )


def check_live_solana_usdc_account(
    wallet_address: str = OUR_SOLANA_WALLET,
    rpc_url: str = "https://api.mainnet-beta.solana.com",
) -> Dict[str, Any]:
    """Query live Solana Mainnet-Beta RPC to verify wallet ATA and current SPL USDC balance."""
    ata, bump = derive_associated_token_address(wallet_address, SOLANA_MAINNET_USDC_MINT)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
            {"mint": SOLANA_MAINNET_USDC_MINT},
            {"encoding": "jsonParsed", "commitment": "confirmed"},
        ],
    }
    req = urllib.request.Request(
        rpc_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "ZeroCapitalAgent/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        rpc_data = json.loads(resp.read().decode("utf-8"))

    accounts = rpc_data.get("result", {}).get("value", [])
    ui_balance = 0.0
    for acc in accounts:
        amt_info = acc.get("account", {}).get("data", {}).get("parsed", {}).get("info", {}).get("tokenAmount", {})
        ui_balance += float(amt_info.get("uiAmount") or 0.0)

    return {
        "wallet_address": wallet_address,
        "usdc_mint": SOLANA_MAINNET_USDC_MINT,
        "derived_usdc_ata": ata,
        "pda_bump": bump,
        "live_rpc_url": rpc_url,
        "token_accounts_found": len(accounts),
        "usdc_balance": ui_balance,
    }


if __name__ == "__main__":
    live_info = check_live_solana_usdc_account()
    print(json.dumps(live_info, indent=2))
