# WIP dont' use



```
python tx/sweep.py -h
usage: sweep.py [-h] [--testnet] wif_key dest_address

Programmatically transfer all bitcoin from a private key to a destination address.

positional arguments:
  wif_key       The WIF format private key of the source address
  dest_address  The destination Bitcoin address

options:
  -h, --help    show this help message and exit
  --testnet     Use testnet instead of mainnet

```





### Create a Transaction (No Broadcast)

```bash
# Send all funds minus fee (default: 1000 sats fee)
python net/create_transaction.py \
  --private-key YOUR_WIF_OR_64_HEX_PRIVATE_KEY \
  --source YOUR_FUNDED_ADDRESS \
  --destination RECIPIENT_ADDRESS

# Send a specific amount
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

| Flag               | Description                                   | Default            |
| ------------------ | --------------------------------------------- | ------------------ |
| `--private-key`    | Required. WIF or 32-byte hex private key      | —                  |
| `--source`         | Required. Funded P2PKH or P2WPKH address      | —                  |
| `--destination`    | Required. Recipient address                   | —                  |
| `--txid`           | UTXO transaction ID (auto-fetched if omitted) | auto               |
| `--vout`           | UTXO output index                             | auto               |
| `--input-sats`     | UTXO value in satoshis                        | auto               |
| `--utxo-index`     | Index of UTXO when auto-fetching              | 0                  |
| `--amount-sats`    | Amount to send                                | all available      |
| `--fee-sats`       | Miner fee                                     | 1000               |
| `--change-address` | Change address                                | same as `--source` |
| `--network`        | `mainnet` or `testnet`                        | `testnet`          |

> **Security Note:** Always verify the signed transaction in a wallet or block explorer before broadcasting. Never share your private key. Use `--network mainnet` for mainnet addresses.

---

## 