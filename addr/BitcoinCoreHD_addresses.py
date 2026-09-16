'''
Generates Bitcoin Core-style HD P2PKH (Pay-to-Public-Key-Hash) Bitcoin addresses.
Bitcoin Core (pre-BIP44, ~2012) uses hardened derivation: m/0'/0'/0'
This represents an early HD wallet implementation before BIP44 standardization.
'''
from bip_utils import (
    Bip39SeedGenerator,
    Bip39MnemonicValidator,
    Bip32Secp256k1,
    Hash160,
    Base58Encoder,
)
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

# Example BIP39 mnemonic seed phrase
mnemonic, num_addresses = parse_derivation_arguments("Generate Bitcoin Core-style HD P2PKH addresses from a BIP39 mnemonic.")
passphrase = ""  # Optional passphrase (default is empty string; can be changed by user)


def compute_p2pkh_address(pub_key_bytes):
    """Compute P2PKH address from public key bytes."""
    h160 = Hash160.QuickDigest(pub_key_bytes)
    return Base58Encoder.CheckEncode(b"\x00" + h160)


def compute_wif(private_key_bytes):
    """Encode a compressed mainnet private key in Wallet Import Format."""
    return Base58Encoder.CheckEncode(b"\x80" + private_key_bytes + b"\x01")


try:
    # Validate the mnemonic phrase
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase provided. Please check the words and try again.")

    print("Mnemonic Phrase:", mnemonic)
    print("Passphrase:", passphrase if passphrase else "<empty>")

    # Generate seed from mnemonic with passphrase
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)

    # Display the generated seed (in hex)
    print("Seed (hex):", seed_bytes.hex())

    # Generate BIP32 master key from seed
    bip32_mst = Bip32Secp256k1.FromSeed(seed_bytes)

    print("Generating Bitcoin Core-style HD P2PKH Addresses (m/0'/0'/0'):")

    # Generate a set number of addresses
    for i in range(num_addresses):
        # Derive using Bitcoin Core HD path: m/0'/0'/0'
        address_key = bip32_mst.ChildKey(0x80000000).ChildKey(0x80000000).ChildKey(0x80000000)

        # Print the BIP32 Extended Public Key for the first address
        if i == 0:
            account_xpub = address_key.PublicKey().ToExtended()
            print("BIP32 Extended Public Key (xpub):", account_xpub)

        # Construct derivation path
        derivation_path = f"m/0'/0'/0'"

        # Compute P2PKH address
        address = compute_p2pkh_address(address_key.PublicKey().RawCompressed().ToBytes())
        public_key = address_key.PublicKey().RawCompressed().ToHex()
        private_key = address_key.PrivateKey().Raw().ToHex()
        wif = compute_wif(address_key.PrivateKey().Raw().ToBytes())

        # Print the output in the specified order
        print("{")
        print(f"derivation_path: {derivation_path}")
        print(f"address: {address}")
        print(f"public_key: {public_key}")
        print(f"private_key: {private_key}")
        print(f"wif: {wif}")
        print("},")

except MnemonicChecksumError as e:
    print(f"Error: Invalid mnemonic checksum. Details: {e}")
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
