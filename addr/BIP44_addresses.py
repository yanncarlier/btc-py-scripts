'''
Generates Native SegWit (P2WPKH) Addresses.
BIP44 (Legacy P2PKH, among others) uses 44'.
'''
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicValidator
from bip_utils.utils.mnemonic import MnemonicChecksumError
from derivation_cli import parse_derivation_arguments

# Example BIP39 mnemonic seed phrase
mnemonic, num_addresses = parse_derivation_arguments("Generate BIP44 P2PKH addresses from a BIP39 mnemonic.")
passphrase = ""  # Optional passphrase (default is empty string; can be changed by user)

try:
    # Initialize Mnemonic object for English wordlist
    # mnemo = Mnemonic("english")

    # Validate the mnemonic phrase
    if not Bip39MnemonicValidator().IsValid(mnemonic):
        raise ValueError("Invalid mnemonic phrase provided. Please check the words and try again.")
    
    print("Mnemonic Phrase:", mnemonic)
    print("Passphrase:", passphrase if passphrase else "<empty>")

    # Generate seed from mnemonic with passphrase
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase=passphrase)

    # Display the generated seed (in hex)
    print("Seed (hex):", seed_bytes.hex())

    # Initialize BIP44 for Bitcoin mainnet and derive the default account (m/44'/0'/0')
    print("Generating Native SegWit (P2WPKH) Addresses:")

    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)

    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)

    # Print the Account Extended Public Key (xpub)
    account_xpub = bip44_acc_ctx.PublicKey().ToExtended()
    print("Account Extended Public Key (xpub):", account_xpub)

    # Generate a set number of addresses
    for i in range(num_addresses):
        # Derive the external chain and address at index i
        bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
        bip44_addr_ctx = bip44_chg_ctx.AddressIndex(i)

        # Construct the derivation path manually (m/44'/0'/0'/0/i)
        derivation_path = f"m/44'/0'/0'/0/{i}"

        # Print the BIP32 Extended Public Key (xpub) when i == 0
        # if i == 0:
        #     bip32_xpub = bip44_chg_ctx.PublicKey().ToExtended()
        #     print("BIP32 Extended Public Key (xpub):", bip32_xpub)

        # Extract required information
        address = bip44_addr_ctx.PublicKey().ToAddress()  # Bitcoin address
        public_key = bip44_addr_ctx.PublicKey().RawCompressed().ToHex()  # Public key in hex
        private_key = bip44_addr_ctx.PrivateKey().Raw().ToHex()
        wif = bip44_addr_ctx.PrivateKey().ToWif()  # Private key in WIF format

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
