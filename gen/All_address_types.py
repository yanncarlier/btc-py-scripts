import argparse
import json

from bip_utils import (
    Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes,
    Bip49, Bip49Coins,
    Bip84, Bip84Coins,
    Bip86, Bip86Coins,
    Bip32Secp256k1,
    Bip39MnemonicValidator,
    Hash160,
    Base58Encoder,
    WifEncoder,
)
from bip_utils.utils.mnemonic import MnemonicChecksumError

DEFAULT_MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"


def compute_p2pkh_address(pub_key_bytes: bytes) -> str:
    """Compute a P2PKH address from a compressed public key."""
    h160 = Hash160.QuickDigest(pub_key_bytes)
    return Base58Encoder.CheckEncode(b"\x00" + h160)


def make_address_entry(
    index: int | None,
    derivation_path: str,
    address: str,
    pub_key_bytes: bytes,
    priv_key_bytes: bytes,
) -> dict:
    """Build a single address child dict."""
    return {
        "index": index,
        "derivation_path": derivation_path,
        "address": address,
        "public_key": pub_key_bytes.hex(),
        "private_key": priv_key_bytes.hex(),
        "wif": WifEncoder.Encode(priv_key_bytes),
    }


def make_scheme(description: str, base_path: str, addresses: list[dict]) -> dict:
    """Build a derivation-scheme group dict."""
    return {
        "description": description,
        "base_path": base_path,
        "addresses": addresses,
    }


def main() -> None:
    """Generate Bitcoin addresses of all derivation types from a BIP39 mnemonic."""
    parser = argparse.ArgumentParser(description="Generate Bitcoin addresses from a BIP39 mnemonic.")
    parser.add_argument(
        "mnemonic",
        nargs="?",
        default=DEFAULT_MNEMONIC,
        help="BIP39 mnemonic phrase (12 or 24 words). If omitted, uses a default test phrase.",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=1,
        metavar="COUNT",
        help="Number of sequential addresses to generate per address type (default: 1).",
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be a positive integer.")

    mnemonic = args.mnemonic.strip()
    count: int = args.count

    try:
        Bip39MnemonicValidator().Validate(mnemonic)
    except MnemonicChecksumError as err:
        raise ValueError(
            "Invalid mnemonic phrase. Please provide a valid BIP39 mnemonic (12 or 24 words)."
        ) from err

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)

    output: list[dict] = []

    # ── Illustrative: pre-HD era P2PKH (master key only, no index) ──
    output.append(make_scheme(
        description="Illustrative: pre-HD era P2PKH (Bitcoin Core 2009 had no mnemonic/HD; shown here as m \u2192 P2PKH)",
        base_path="m",
        addresses=[make_address_entry(
            index=None,
            derivation_path="m",
            address=compute_p2pkh_address(bip32_mst.PublicKey().RawCompressed().ToBytes()),
            pub_key_bytes=bip32_mst.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=bip32_mst.PrivateKey().Raw().ToBytes(),
        )],
    ))

    # ── Electrum-style: m/0'/i ──
    electrum_base = bip32_mst.ChildKey(0x80000000)
    electrum_addrs = []
    for i in range(count):
        node = electrum_base.ChildKey(i)
        electrum_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/0'/{i}",
            address=compute_p2pkh_address(node.PublicKey().RawCompressed().ToBytes()),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="Electrum-style derivation",
        base_path="m/0'",
        addresses=electrum_addrs,
    ))

    # ── Bitcoin Core HD-style: m/0'/0'/i' ──
    bitcoin_core_base = bip32_mst.ChildKey(0x80000000).ChildKey(0x80000000)
    bitcoin_core_addrs = []
    for i in range(count):
        node = bitcoin_core_base.ChildKey(0x80000000 + i)
        bitcoin_core_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/0'/0'/{i}'",
            address=compute_p2pkh_address(node.PublicKey().RawCompressed().ToBytes()),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="Bitcoin Core-style HD derivation",
        base_path="m/0'/0'",
        addresses=bitcoin_core_addrs,
    ))

    # ── BIP44 Legacy P2PKH: m/44'/0'/0'/0/i ──
    bip44_chain = (
        Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    )
    bip44_addrs = []
    for i in range(count):
        node = bip44_chain.AddressIndex(i)
        bip44_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/44'/0'/0'/0/{i}",
            address=node.PublicKey().ToAddress(),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="BIP44 Legacy P2PKH",
        base_path="m/44'/0'/0'/0",
        addresses=bip44_addrs,
    ))

    # ── MultiBit Classic: m/0'/0/i ──
    multibit_base = bip32_mst.ChildKey(0x80000000).ChildKey(0)
    multibit_addrs = []
    for i in range(count):
        node = multibit_base.ChildKey(i)
        multibit_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/0'/0/{i}",
            address=compute_p2pkh_address(node.PublicKey().RawCompressed().ToBytes()),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="MultiBit Classic-style derivation (approximate; MultiBit Classic used its own seed format, not BIP39)",
        base_path="m/0'/0",
        addresses=multibit_addrs,
    ))

    # ── BIP44 external-chain via raw BIP32: m/44'/0'/0'/0/i ──
    bip44_variant_base = (
        bip32_mst
        .ChildKey(0x8000002C)
        .ChildKey(0x80000000)
        .ChildKey(0x80000000)
        .ChildKey(0)
    )
    bip44_variant_addrs = []
    for i in range(count):
        node = bip44_variant_base.ChildKey(i)
        bip44_variant_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/44'/0'/0'/0/{i}",
            address=compute_p2pkh_address(node.PublicKey().RawCompressed().ToBytes()),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="BIP44 external-chain derivation via raw BIP32 (chain-level access)",
        base_path="m/44'/0'/0'/0",
        addresses=bip44_variant_addrs,
    ))

    # ── MultiBit HD: m/0'/0/i' ──
    multibit_hd_base = bip32_mst.ChildKey(0x80000000).ChildKey(0)
    multibit_hd_addrs = []
    for i in range(count):
        node = multibit_hd_base.ChildKey(0x80000000 + i)
        multibit_hd_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/0'/0/{i}'",
            address=compute_p2pkh_address(node.PublicKey().RawCompressed().ToBytes()),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="MultiBit HD-style derivation",
        base_path="m/0'/0",
        addresses=multibit_hd_addrs,
    ))

    # ── BIP49 Nested SegWit P2SH-P2WPKH: m/49'/0'/0'/0/i ──
    bip49_chain = (
        Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN)
        .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    )
    bip49_addrs = []
    for i in range(count):
        node = bip49_chain.AddressIndex(i)
        bip49_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/49'/0'/0'/0/{i}",
            address=node.PublicKey().ToAddress(),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="BIP49 Nested SegWit P2SH-P2WPKH",
        base_path="m/49'/0'/0'/0",
        addresses=bip49_addrs,
    ))

    # ── BIP84 Native SegWit P2WPKH: m/84'/0'/0'/0/i ──
    bip84_chain = (
        Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
        .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    )
    bip84_addrs = []
    for i in range(count):
        node = bip84_chain.AddressIndex(i)
        bip84_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/84'/0'/0'/0/{i}",
            address=node.PublicKey().ToAddress(),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="BIP84 Native SegWit P2WPKH",
        base_path="m/84'/0'/0'/0",
        addresses=bip84_addrs,
    ))

    # ── BIP86 Taproot P2TR: m/86'/0'/0'/0/i ──
    bip86_chain = (
        Bip86.FromSeed(seed_bytes, Bip86Coins.BITCOIN)
        .Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    )
    bip86_addrs = []
    for i in range(count):
        node = bip86_chain.AddressIndex(i)
        bip86_addrs.append(make_address_entry(
            index=i,
            derivation_path=f"m/86'/0'/0'/0/{i}",
            address=node.PublicKey().ToAddress(),
            pub_key_bytes=node.PublicKey().RawCompressed().ToBytes(),
            priv_key_bytes=node.PrivateKey().Raw().ToBytes(),
        ))
    output.append(make_scheme(
        description="BIP86 Taproot P2TR",
        base_path="m/86'/0'/0'/0",
        addresses=bip86_addrs,
    ))

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
