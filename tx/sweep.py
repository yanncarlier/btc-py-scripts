#!/usr/bin/env python3
"""
sweep.py: Programmatically transfer all bitcoin from a private key to a destination address.
"""

import sys
from bit import PrivateKeyTestnet, PrivateKey


def sweep_funds(wif_key: str, destination_address: str, testnet: bool = False):
    """Sweeps all funds from a private key to a destination address."""
    try:
        # Select network type
        key_class = PrivateKeyTestnet if testnet else PrivateKey
        my_key = key_class(wif_key)

        print(f"Source Address: {my_key.address}")
        print(f"Destination Address: {destination_address}")

        # Check balance before sweeping
        balance_satoshis = my_key.get_balance()
        print(f"Current Balance: {balance_satoshis} satoshis")

        if int(balance_satoshis) <= 0:
            print("Error: The address has a zero or negative balance.")
            sys.exit(1)

        # Send all funds (subtracting fee automatically)
        # send() takes a list of tuples: (destination_address, amount, currency_unit)
        # Using 'satoshi' and 'all' ensures the entire balance minus fee is sent.
        tx_hash = my_key.send([(destination_address, "all", "satoshi")])

        print("Transaction successfully broadcasted!")
        print(f"Transaction Hash: {tx_hash}")

    except Exception as e:
        print(f"An error occurred during the sweep: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Configuration parameters
    # Replace these with your actual WIF private key and destination address
    PRIVATE_KEY_WIF = "YOUR_PRIVATE_KEY_IN_WIF_FORMAT"
    DEST_ADDRESS = "DESTINATION_BITCOIN_ADDRESS"
    IS_TESTNET = (
        False  # Set to True if you are using testnet coins/keys
    )

    sweep_funds(PRIVATE_KEY_WIF, DEST_ADDRESS, testnet=IS_TESTNET)