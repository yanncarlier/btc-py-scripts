

https://iancoleman.io/bip39/  

https://bitinfocharts.com/top-100-richest-bitcoin-addresses.html  

https://mempool.space/  

https://bitinfocharts.com/bitcoin/address/  



bc1q8tet66yh0jf7eauv7k22sd7jx0qa9wq36acdev

bc1qxuy8c9t8anc33wya6lxzk29dkctud6sxqr88ud




```
python create_transaction.py \
  --private-key e284129cc0922579a535bbf4d1a3b25773090d28c909bc0fed73b5e0222cc372 \
  --source 1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA \
  --destination 1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA


python create_transaction.py \
  --private-key YOUR_WIF_OR_64_HEX_PRIVATE_KEY \
  --source YOUR_FUNDED_P2PKH_OR_P2WPKH_ADDRESS \
  --destination RECIPIENT_ADDRESS
```






```
# Auto-fetch UTXO from mempool.space (uses largest UTXO)
python create_transaction.py --private-key <key> --source <addr> --destination <dest> --amount-sats 1000 --fee-sats 250 --network testnet

# Auto-fetch but use 2nd largest UTXO
python create_transaction.py ... --utxo-index 1

# Manual UTXO specification (old behavior still works)
python create_transaction.py ... --txid <txid> --vout 0 --input-sats 5000 ...
```

