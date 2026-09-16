import argparse

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


def compute_p2pkh_address(pub_key_bytes):
    # Use compressed public key for address generation (standard for modern Bitcoin)
    h160 = Hash160.QuickDigest(pub_key_bytes)
    return Base58Encoder.CheckEncode(b"\x00" + h160)


def print_address_info(path, address, pub_key_bytes, priv_key_bytes, description):
    wif = WifEncoder.Encode(priv_key_bytes)
    print("{")
    print(f"description: {description}")
    print(f"derivation_path: {path}")
    print(f"address: {address}")
    print(f"public_key: {pub_key_bytes.hex()}")
    print(f"private_key: {priv_key_bytes.hex()}")
    print(f"wif: {wif}")
    print("},")


def main():
    parser = argparse.ArgumentParser(description="Generate Bitcoin addresses from a BIP39 mnemonic.")
    parser.add_argument("mnemonic", nargs="?", default=DEFAULT_MNEMONIC,
                        help="BIP39 mnemonic phrase (12 or 24 words). If omitted, uses a default test phrase.")
    args = parser.parse_args()

    mnemonic = args.mnemonic.strip()

    try:
        Bip39MnemonicValidator().Validate(mnemonic)
    except MnemonicChecksumError:
        raise ValueError("Invalid mnemonic phrase. Please provide a valid BIP39 mnemonic (12 or 24 words).")

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)

    original_p2pkh = compute_p2pkh_address(bip32_mst.PublicKey().RawCompressed().ToBytes())
    print_address_info(
        "m", original_p2pkh, bip32_mst.PublicKey().RawCompressed().ToBytes(), bip32_mst.PrivateKey().Raw().ToBytes(),
        "Illustrative: pre-HD era P2PKH (Bitcoin Core 2009 had no mnemonic/HD; shown here as m → P2PKH)"
    )

    # Electrum uses m/0'/n
    electrum_ext = bip32_mst.ChildKey(0x80000000).ChildKey(0)
    electrum_addr = compute_p2pkh_address(electrum_ext.PublicKey().RawCompressed().ToBytes())
    print_address_info(
        "m/0'/0", electrum_addr, electrum_ext.PublicKey().RawCompressed().ToBytes(), electrum_ext.PrivateKey().Raw().ToBytes(),
        "Electrum-style derivation — m/0'/0"
    )

    # Bitcoin Core (pre-BIP32, ~2012) - using hardened derivation for all levels
    bitcoin_core_ext = bip32_mst.ChildKey(0x80000000).ChildKey(0x80000000).ChildKey(0x80000000)
    bitcoin_core_addr = compute_p2pkh_address(bitcoin_core_ext.PublicKey().RawCompressed().ToBytes())
    print_address_info(
        "m/0'/0'/0'", bitcoin_core_addr, bitcoin_core_ext.PublicKey().RawCompressed().ToBytes(), bitcoin_core_ext.PrivateKey().Raw().ToBytes(),
        "Bitcoin Core-style HD derivation — m/0'/0'/0'"
    )

    # BIP44 addresses
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    bip44_addr = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    print_address_info(
        "m/44'/0'/0'/0/0", bip44_addr.PublicKey().ToAddress(), bip44_addr.PublicKey().RawCompressed().ToBytes(), bip44_addr.PrivateKey().Raw().ToBytes(),
        "BIP44 Legacy P2PKH — m/44'/0'/0'/0/0"
    )

    # Multibit Classic used m/0'/0/n
    multibit_ext = bip32_mst.ChildKey(0x80000000).ChildKey(0).ChildKey(0)
    multibit_addr = compute_p2pkh_address(multibit_ext.PublicKey().RawCompressed().ToBytes())
    print_address_info(
        "m/0'/0/0", multibit_addr, multibit_ext.PublicKey().RawCompressed().ToBytes(), multibit_ext.PrivateKey().Raw().ToBytes(),
        "MultiBit Classic-style derivation — m/0'/0/0 (approximate; MultiBit Classic used its own seed format, not BIP39)"
    )

    # Coinomi, Ledger, and Blockchain.info use m/44'/0'/0' as base path
    bip44_variant_ext = bip32_mst.ChildKey(0x8000002C).ChildKey(0x80000000).ChildKey(0x80000000).ChildKey(0)
    bip44_variant_addr = compute_p2pkh_address(bip44_variant_ext.PublicKey().RawCompressed().ToBytes())
    print_address_info(
        "m/44'/0'/0'/0", bip44_variant_addr, bip44_variant_ext.PublicKey().RawCompressed().ToBytes(), bip44_variant_ext.PrivateKey().Raw().ToBytes(),
        "BIP44 external-chain derivation — m/44'/0'/0'/0 (chain-level; first address normally /0)"
    )

    # MultiBit HD used m/0'/0/0' (modified BIP32/44 style path)
    multibit_hd_ext = bip32_mst.ChildKey(0x80000000).ChildKey(0).ChildKey(0x80000000)
    multibit_hd_addr = compute_p2pkh_address(multibit_hd_ext.PublicKey().RawCompressed().ToBytes())
    print_address_info(
        "m/0'/0/0'", multibit_hd_addr, multibit_hd_ext.PublicKey().RawCompressed().ToBytes(), multibit_hd_ext.PrivateKey().Raw().ToBytes(),
        "MultiBit HD-style derivation — m/0'/0/0'"
    )

    bip49_mst = Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN)
    bip49_addr = bip49_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    print_address_info(
        "m/49'/0'/0'/0/0", bip49_addr.PublicKey().ToAddress(), bip49_addr.PublicKey().RawCompressed().ToBytes(), bip49_addr.PrivateKey().Raw().ToBytes(),
        "BIP49 Nested SegWit P2SH-P2WPKH — m/49'/0'/0'/0/0"
    )

    bip84_mst = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
    bip84_addr = bip84_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    print_address_info(
        "m/84'/0'/0'/0/0", bip84_addr.PublicKey().ToAddress(), bip84_addr.PublicKey().RawCompressed().ToBytes(), bip84_addr.PrivateKey().Raw().ToBytes(),
        "BIP84 Native SegWit P2WPKH — m/84'/0'/0'/0/0"
    )

    bip86_mst = Bip86.FromSeed(seed_bytes, Bip86Coins.BITCOIN)
    bip86_addr = bip86_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    print_address_info(
        "m/86'/0'/0'/0/0", bip86_addr.PublicKey().ToAddress(), bip86_addr.PublicKey().RawCompressed().ToBytes(), bip86_addr.PrivateKey().Raw().ToBytes(),
        "BIP86 Taproot P2TR — m/86'/0'/0'/0/0"
    )


if __name__ == "__main__":
    main()
