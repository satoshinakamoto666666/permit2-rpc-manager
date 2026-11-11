from decimal import Decimal
from solana_usdc_verifier import (
    OUR_SOLANA_WALLET,
    SOLANA_MAINNET_USDC_MINT,
    derive_associated_token_address,
    verify_parsed_solana_usdc_tx,
)


def test_derive_ata_deterministic():
    ata, bump = derive_associated_token_address(OUR_SOLANA_WALLET, SOLANA_MAINNET_USDC_MINT)
    assert len(ata) >= 32
    assert 0 <= bump <= 255


def test_end_to_end_usdc_payment_verification():
    sample_tx = {
        "slot": 467868350,
        "blockTime": 1794345000,
        "transaction": {
            "signatures": ["5xYzSampleSolanaSignature111111111111111111111111111111111111111111111"],
            "message": {
                "instructions": [
                    {
                        "program": "spl-memo",
                        "programId": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
                        "parsed": "INV-2026-001",
                    }
                ]
            },
        },
        "meta": {
            "err": None,
            "preTokenBalances": [
                {
                    "mint": SOLANA_MAINNET_USDC_MINT,
                    "owner": "SenderWallet1111111111111111111111111111111",
                    "uiTokenAmount": {"amount": "100000000", "decimals": 6},
                },
                {
                    "mint": SOLANA_MAINNET_USDC_MINT,
                    "owner": OUR_SOLANA_WALLET,
                    "uiTokenAmount": {"amount": "2500000", "decimals": 6},
                },
            ],
            "postTokenBalances": [
                {
                    "mint": SOLANA_MAINNET_USDC_MINT,
                    "owner": "SenderWallet1111111111111111111111111111111",
                    "uiTokenAmount": {"amount": "95000000", "decimals": 6},
                },
                {
                    "mint": SOLANA_MAINNET_USDC_MINT,
                    "owner": OUR_SOLANA_WALLET,
                    "uiTokenAmount": {"amount": "7500000", "decimals": 6},
                },
            ],
        },
    }

    res = verify_parsed_solana_usdc_tx(
        sample_tx,
        recipient_wallet=OUR_SOLANA_WALLET,
        expected_amount_usdc=Decimal("5.00"),
        expected_memo="INV-2026-001",
    )
    assert res.verified is True
    assert res.actual_received_usdc == "5"
    assert res.sender_wallets == ["SenderWallet1111111111111111111111111111111"]
    assert res.memo == "INV-2026-001"

    # Underpayment check fails cleanly
    under = verify_parsed_solana_usdc_tx(
        sample_tx,
        recipient_wallet=OUR_SOLANA_WALLET,
        expected_amount_usdc=Decimal("10.00"),
    )
    assert under.verified is False
    assert "Insufficient USDC" in under.reason
