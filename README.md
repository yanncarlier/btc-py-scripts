# btc-py-scripts

Educational Python scripts for working with Bitcoin addresses, transactions, and blockchain data. 

## Account 1, Bitcoin donation addresses:

```
# Send BTC directly to:
"address": "bc1qmr2sm7fmejfaqcd0l067m75c8c8h46kq5uw70g"  
"address": "bc1qa3tjj9fc7n0j3lnfuc56tqdhlqrt0uw0czrkm6"
"address": "bc1qyu3zy7nasur5ju8hghs3kc3480h5rccs3fthfh"
```

---

## Setup

### Prerequisites & Installation

- Python 3.10 or newer
- `uv` (recommended) or `pip`

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## Examples

### Generate a New Mnemonic

```bash
python gen/generate_mnemonic.py
# Or to generate a 24-word mnemonic (256-bit strength):
python gen/generate_mnemonic.py -s 256
```

Outputs an English BIP39 mnemonic, seed, and BIP32 root key. The default is a 12-word mnemonic (128-bit strength).

### Derive Addresses from a Mnemonic

All individual derivation scripts accept a BIP39 mnemonic and an optional count as command-line arguments.

```bash
# Generate 5 BIP84 native SegWit addresses
python gen/BIP84_addresses.py "word1 word2 ... word12" 5

# Generate 3 addresses with default test mnemonic
python gen/BIP49_addresses.py 3

# Use the -n flag
python gen/BIP49_addresses.py -n 2

# Generate addresses for all supported schemes at once
python gen/all_address_types.py "word1 word2 ... word12"
```

| Script | Derivation Path | Address Type |
| --- | --- | --- |
| `P2PKH_addresses.py` | `m` | Legacy P2PKH |
| `Electrum_addresses.py` | `m/0'/n` | Legacy P2PKH |
| `BitcoinCoreHD_addresses.py` | `m/0'/0'/0'` | Legacy P2PKH |
| `MultiBitClassic_addresses.py` | `m/0'/0/0` | Legacy P2PKH |
| `MultiBitHD_addresses.py` | `m/0'/0/0'` | Legacy P2PKH |
| `BIP44_addresses.py` | `m/44'/0'/0'/0/n` | Legacy P2PKH |
| `BIP44_external_chain_addresses.py` | `m/44'/0'/0'/0` | Chain-level P2PKH |
| `BIP49_addresses.py` | `m/49'/0'/0'/0/n` | Wrapped SegWit (P2SH-P2WPKH) |
| `BIP84_addresses.py` | `m/84'/0'/0'/0/n` | Native SegWit (P2WPKH) |
| `BIP86_addresses.py` | `m/86'/0'/0'/0/n` | Taproot (P2TR) |

> **Note:** `all_address_types.py` prints one address per scheme but does **not** print private keys.

### Brain Wallet (Educational Only)

```bash
python gen/brain_wallet.py "your secure passphrase here"
```

> **Warning:** Brain wallets are **insecure** and vulnerable to brute-force attacks. Educational purposes only.

### Query Blockchain Data

```bash
python net/blockchain.info.py ADDRESS
python net/blockcypher.com.py ADDRESS
python net/blockstream.info.py ADDRESS
python net/mempool.space.py ADDRESS
```

Each script prints the total balance in satoshis (confirmed + unconfirmed where reported).

## Security Best Practices

1. **Never use the bundled test mnemonic** for real funds — it is public
2. **Never share or commit** real mnemonics, seeds, private keys, or WIFs
3. **Verify before use** — confirm derivation paths, address types, and network match your wallet
4. **Prefer established wallets** with hardware signer support for real funds
5. **Test first** — use testnet or small amounts when experimenting
6. **Keep backups secure** — store mnemonics offline in secure locations

