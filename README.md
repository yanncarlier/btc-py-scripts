# btc-py-scripts

Educational Python scripts for working with Bitcoin addresses, transactions, and blockchain data. These scripts demonstrate key Bitcoin concepts including BIP39 mnemonic generation, hierarchical deterministic (HD) wallet derivation, and transaction creation.

> **Warning:** Several scripts print mnemonics, seeds, private keys, or WIFs to standard output. Treat that output as secret. The bundled test mnemonic (`abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about`) is a public test vector and must **never** receive funds. All derivation scripts target Bitcoin mainnet by default.

## Quick Start

### Prerequisites

- Python 3.10 or newer
- `uv` (recommended) or `pip`

### Setup

With `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

With `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Scripts Overview

### Address Derivation Scripts

All individual derivation scripts now support command-line arguments for the BIP39 mnemonic and the number of addresses to generate.

#### Individual Derivation Schemes

Each script derives addresses from a BIP39 mnemonic using a specific BIP or wallet-style derivation path. They print sensitive material (seed, private keys, WIF) to standard output.

| Script | Derivation Path | Address Type | Usage |
| --- | --- | --- | --- |
| `P2PKH_addresses.py` | `m` | Legacy P2PKH | `python P2PKH_addresses.py [MNEMONIC] [COUNT]` |
| `Electrum_addresses.py` | `m/0'/n` | Legacy P2PKH | `python Electrum_addresses.py [MNEMONIC] [COUNT]` |
| `BitcoinCoreHD_addresses.py` | `m/0'/0'/0'` | Legacy P2PKH | `python BitcoinCoreHD_addresses.py [MNEMONIC] [COUNT]` |
| `MultiBitClassic_addresses.py` | `m/0'/0/0` | Legacy P2PKH | `python MultiBitClassic_addresses.py [MNEMONIC] [COUNT]` |
| `MultiBitHD_addresses.py` | `m/0'/0/0'` | Legacy P2PKH | `python MultiBitHD_addresses.py [MNEMONIC] [COUNT]` |
| `BIP44_addresses.py` | `m/44'/0'/0'/0/n` | Legacy P2PKH | `python BIP44_addresses.py [MNEMONIC] [COUNT]` |
| `BIP44_external_chain_addresses.py` | `m/44'/0'/0'/0` | Chain-level P2PKH | `python BIP44_external_chain_addresses.py [MNEMONIC] [COUNT]` |
| `BIP49_addresses.py` | `m/49'/0'/0'/0/n` | Wrapped SegWit (P2SH-P2WPKH) | `python BIP49_addresses.py [MNEMONIC] [COUNT]` |
| `BIP84_addresses.py` | `m/84'/0'/0'/0/n` | Native SegWit (P2WPKH) | `python BIP84_addresses.py [MNEMONIC] [COUNT]` |
| `BIP86_addresses.py` | `m/86'/0'/0'/0/n` | Taproot (P2TR) | `python BIP86_addresses.py [MNEMONIC] [COUNT]` |

**Command-line arguments:**
- Positional: `COUNT` - number of addresses to generate (default: 1)
- Positional: `MNEMONIC` - quoted 12- or 24-word BIP39 mnemonic (default: public test mnemonic)
- Flag: `-n COUNT` or `--count COUNT` - number of addresses to generate

**Example:**
```bash
# Generate 5 BIP84 native SegWit addresses with custom mnemonic
python BIP84_addresses.py "word1 word2 ... word12" 5

# Generate 3 addresses with default mnemonic
python BIP49_addresses.py 3

# Generate 2 addresses using the -n flag
python BIP49_addresses.py -n 2

# Generate addresses from custom mnemonic with -n flag
python BIP49_addresses.py "word1 word2 ... word12" -n 4
```

#### All Address Types

`all_address_types.py` generates one address per supported derivation scheme from a single mnemonic:

```bash
# Print addresses for all supported schemes
python all_address_types.py [MNEMONIC]

# With a specific mnemonic
python all_address_types.py "word1 word2 ... word12"
```

This script does **not** print private keys.

### Mnemonic Generation

Generate a new BIP39 mnemonic:

```bash
python generate_mnemonic.py
```

This outputs a 12-word English BIP39 mnemonic (128-bit strength), seed, and BIP32 root key. To generate a 24-word mnemonic, modify `strength=128` to `strength=256` in the source.

### Brain Wallet (Educational)

```bash
python brain_wallet.py
```

> **Warning:** Brain wallets are **insecure** and vulnerable to guessing/brute-force attacks. This is for educational purposes only. Never use this for securing real funds.

The script hashes a hard-coded passphrase with SHA-256 and prints an uncompressed mainnet WIF and P2PKH address.

### Blockchain API Lookups

Query address balances and UTXOs from public blockchain explorers:

| Script | API Provider | Usage |
| --- | --- | --- |
| `net/blockchain.info.py` | Blockchain.com | `python net/blockchain.info.py ADDRESS` |
| `net/blockcypher.com.py` | BlockCypher | `python net/blockcypher.com.py ADDRESS` |
| `net/blockstream.info.py` | Blockstream Esplora | `python net/blockstream.info.py ADDRESS` |
| `net/mempool.space.py` | Mempool Space | `python net/mempool.space.py ADDRESS` |

Each script takes a single `ADDRESS` argument and prints the total balance in satoshis (confirmed + unconfirmed where reported).

**Example:**
```bash
python net/mempool.space.py bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr
```

### Transaction Creation

`net/create_transaction.py` creates and signs a single-input Bitcoin transaction **without broadcasting it**. It supports legacy P2PKH (`1...`) and native SegWit P2WPKH (`bc1q...`) inputs.

#### Features

- Auto-fetch UTXOs from mempool.space (or specify manually)
- Automatic change calculation
- Send all funds or a specific amount
- Dust limit checking (546 sats minimum for change)
- Support for both P2PKH and P2WPKH addresses

#### Usage Examples

```bash
# Auto-fetch UTXO and send all funds minus fee (default: 1000 sats)
python net/create_transaction.py \
  --private-key YOUR_WIF_OR_64_HEX_PRIVATE_KEY \
  --source YOUR_FUNDED_ADDRESS \
  --destination RECIPIENT_ADDRESS

# Auto-fetch UTXO and send specific amount
python net/create_transaction.py \
  --private-key YOUR_WIF_OR_64_HEX_PRIVATE_KEY \
  --source YOUR_FUNDED_ADDRESS \
  --destination RECIPIENT_ADDRESS \
  --amount-sats 50000 \
  --fee-sats 2000

# Manually specify UTXO details
python net/create_transaction.py \
  --private-key YOUR_WIF_OR_64_HEX_PRIVATE_KEY \
  --source YOUR_FUNDED_ADDRESS \
  --txid PREVIOUS_TRANSACTION_ID \
  --vout 0 \
  --input-sats 100000 \
  --destination RECIPIENT_ADDRESS \
  --amount-sats 90000 \
  --fee-sats 1000 \
  --change-address YOUR_CHANGE_ADDRESS
```

**Options:**
- `--private-key`: Required. 32-byte hex private key or network-appropriate WIF
- `--source`: Required. Funded P2PKH or P2WPKH address belonging to the private key
- `--destination`: Required. Recipient P2PKH or P2WPKH address
- `--txid`: UTXO transaction ID (auto-fetched if not provided)
- `--vout`: UTXO output index (auto-fetched if not provided)
- `--input-sats`: UTXO value in satoshis (auto-fetched if not provided)
- `--utxo-index`: Index of UTXO to use when auto-fetching (default: 0)
- `--amount-sats`: Amount to send (default: all available funds minus fee)
- `--fee-sats`: Miner fee in satoshis (default: 1000)
- `--change-address`: Change address (default: same as `--source`)
- `--network`: `mainnet` or `testnet` (default: `testnet`)

> **Security Note:** Always verify the signed transaction in a wallet or block explorer before broadcasting. Never share your private key. Use `--network mainnet` for mainnet addresses.

## Derivation Path Reference

| BIP/Style | Purpose | Coin Type | Account | Change | Index |
| --- | --- | --- | --- | --- | --- |
| Pre-HD | N/A | N/A | N/A | N/A | N/A |
| Electrum | N/A | 0' | 0 | N/A | n |
| Bitcoin Core HD | N/A | 0' | 0' | 0' | N/A |
| MultiBit Classic | N/A | 0' | 0 | N/A | n |
| MultiBit HD | N/A | 0' | 0 | 0' | N/A |
| BIP44 | 44' | 0' | 0' | 0 | n |
| BIP49 | 49' | 0' | 0' | 0 | n |
| BIP84 | 84' | 0' | 0' | 0 | n |
| BIP86 | 86' | 0' | 0' | 0 | n |

## Security Best Practices

1. **Never use the bundled test mnemonic** for real funds - it is public
2. **Never share or commit** real mnemonics, seeds, private keys, or WIFs
3. **Verify before use** - confirm derivation paths, address types, and network match your wallet
4. **Prefer established wallets** with hardware signer support for real funds
5. **Test first** - use testnet or small amounts when experimenting
6. **Keep backups secure** - store mnemonics offline in secure locations

## Dependencies

Core dependencies (see `requirements.in`):
- `base58` - Base58 encoding/decoding
- `bip32utils` - BIP32 hierarchical deterministic wallet utilities
- `bitcoinlib` - Bitcoin library (partial usage)
- `cryptography` - Cryptographic primitives (ECDSA, secp256k1)
- `mnemonic` - BIP39 mnemonic generation and validation

Full dependency list with pinned versions (see `requirements.txt`).

## License

This repository contains educational demonstration code. Refer to individual library licenses for dependencies.

## Contributing

These scripts are provided for educational purposes. Contributions that improve clarity, add documentation, or fix bugs are welcome.
