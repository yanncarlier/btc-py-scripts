#!/usr/bin/env python3
"""Create and sign a one-input Bitcoin transaction without broadcasting it.

This educational tool supports spending a P2PKH (``1...``/``m...``) or native
SegWit P2WPKH (``bc1q...``/``tb1q...``) UTXO.  It can automatically fetch
UTXOs from mempool.space, or you can provide them manually. Inspect the
resulting unsigned/signed transaction in a wallet or explorer before using
it with real funds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature


SIGHASH_ALL = 1
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DUST_LIMIT_SATOSHIS = 546


class TransactionError(ValueError):
    """Raised when transaction arguments are invalid or unsupported."""


def fetch_utxos(address: str, network: str) -> list[dict]:
    """Fetch UTXOs for an address from mempool.space API."""
    base_url = "https://mempool.space" if network == "mainnet" else "https://mempool.space/testnet"
    url = f"{base_url}/api/address/{address}/utxo"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        raise TransactionError(f"mempool.space API error: HTTP {e.code} - {e.reason}") from e
    except urllib.error.URLError as e:
        raise TransactionError(f"Failed to connect to mempool.space: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise TransactionError(f"Invalid response from mempool.space: {e}") from e


@dataclass(frozen=True)
class Address:
    """Decoded Bitcoin address data needed to construct a scriptPubKey."""

    kind: str
    payload: bytes

    def script_pubkey(self) -> bytes:
        if self.kind == "p2pkh":
            return b"\x76\xa9\x14" + self.payload + b"\x88\xac"
        return b"\x00\x14" + self.payload


def hash160(data: bytes) -> bytes:
    """Return RIPEMD160(SHA256(data))."""
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).digest()


def double_sha256(data: bytes) -> bytes:
    """Return SHA256(SHA256(data))."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def compact_size(value: int) -> bytes:
    """Encode a Bitcoin CompactSize unsigned integer."""
    if value < 0:
        raise TransactionError("length cannot be negative")
    if value < 253:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    if value <= 0xFFFFFFFF:
        return b"\xfe" + value.to_bytes(4, "little")
    return b"\xff" + value.to_bytes(8, "little")


def push_data(data: bytes) -> bytes:
    """Encode a small script data push."""
    if len(data) > 75:
        raise TransactionError("only pushes up to 75 bytes are supported")
    return bytes([len(data)]) + data


def base58_decode(value: str) -> bytes:
    """Decode a Base58 string without external dependencies."""
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    number = 0
    for character in value:
        try:
            number = number * 58 + alphabet.index(character)
        except ValueError as error:
            raise TransactionError(f"invalid Base58 character: {character!r}") from error
    body = number.to_bytes((number.bit_length() + 7) // 8, "big")
    return b"\x00" * (len(value) - len(value.lstrip("1"))) + body


def base58_check_decode(value: str) -> bytes:
    """Decode and checksum-verify a Base58Check string."""
    decoded = base58_decode(value)
    if len(decoded) < 5:
        raise TransactionError("Base58Check value is too short")
    payload, checksum = decoded[:-4], decoded[-4:]
    if double_sha256(payload)[:4] != checksum:
        raise TransactionError("invalid Base58Check checksum")
    return payload


def polymod(values: list[int]) -> int:
    """Return the Bech32 checksum polymod."""
    checksum = 1
    for value in values:
        top = checksum >> 25
        checksum = (checksum & 0x1FFFFFF) << 5 ^ value
        for index, generator in enumerate((0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)):
            if (top >> index) & 1:
                checksum ^= generator
    return checksum


def bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(character) >> 5 for character in hrp] + [0] + [ord(character) & 31 for character in hrp]


def convertbits(data: list[int], from_bits: int, to_bits: int, pad: bool) -> list[int]:
    """Convert between bit group sizes as specified by BIP 173."""
    accumulator = 0
    bits = 0
    result: list[int] = []
    max_value = (1 << to_bits) - 1
    for value in data:
        if value < 0 or value >> from_bits:
            raise TransactionError("invalid Bech32 data value")
        accumulator = (accumulator << from_bits) | value
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            result.append((accumulator >> bits) & max_value)
    if pad and bits:
        result.append((accumulator << (to_bits - bits)) & max_value)
    elif not pad and (bits >= from_bits or ((accumulator << (to_bits - bits)) & max_value)):
        raise TransactionError("invalid padding in Bech32 address")
    return result


def decode_address(value: str, network: str) -> Address:
    """Decode a supported network address into its script type and hash."""
    expected_version = 0x00 if network == "mainnet" else 0x6F
    expected_hrp = "bc" if network == "mainnet" else "tb"
    if value.lower().startswith(("bc1", "tb1")):
        if value.lower() != value and value.upper() != value:
            raise TransactionError("Bech32 address cannot mix upper- and lowercase")
        normalized = value.lower()
        separator = normalized.rfind("1")
        if separator < 1 or separator + 7 > len(normalized):
            raise TransactionError("invalid Bech32 address")
        hrp, encoded = normalized[:separator], normalized[separator + 1 :]
        alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
        try:
            data = [alphabet.index(character) for character in encoded]
        except ValueError as error:
            raise TransactionError("invalid Bech32 character") from error
        if hrp != expected_hrp or polymod(bech32_hrp_expand(hrp) + data) != 1:
            raise TransactionError("invalid Bech32 checksum or wrong network")
        if data[0] != 0:
            raise TransactionError("only Bech32 v0 P2WPKH addresses are supported")
        program = bytes(convertbits(data[1:-6], 5, 8, False))
        if len(program) != 20:
            raise TransactionError("only 20-byte P2WPKH witness programs are supported")
        return Address("p2wpkh", program)

    payload = base58_check_decode(value)
    if len(payload) != 21 or payload[0] != expected_version:
        raise TransactionError("expected a P2PKH address for the selected network")
    return Address("p2pkh", payload[1:])


def private_key_from_text(value: str, network: str) -> tuple[ec.EllipticCurvePrivateKey, bool]:
    """Parse a 32-byte hexadecimal private key or WIF; return key and WIF compression."""
    try:
        raw = bytes.fromhex(value)
    except ValueError:
        raw = b""
    compressed = True
    if len(raw) != 32:
        payload = base58_check_decode(value)
        expected_prefix = 0x80 if network == "mainnet" else 0xEF
        if payload[0] != expected_prefix or len(payload) not in (33, 34):
            raise TransactionError("WIF is invalid or belongs to another network")
        raw = payload[1:33]
        compressed = len(payload) == 34
        if compressed and payload[33] != 1:
            raise TransactionError("invalid compressed WIF suffix")
    secret = int.from_bytes(raw, "big")
    if not 0 < secret < SECP256K1_ORDER:
        raise TransactionError("private key is outside the secp256k1 range")
    return ec.derive_private_key(secret, ec.SECP256K1()), compressed


def compressed_public_key(private_key: ec.EllipticCurvePrivateKey) -> bytes:
    """Serialize a secp256k1 public key in compressed SEC format."""
    numbers = private_key.public_key().public_numbers()
    return bytes([2 + (numbers.y & 1)]) + numbers.x.to_bytes(32, "big")


def serialize_input(txid: bytes, vout: int, script_sig: bytes, sequence: int) -> bytes:
    return txid[::-1] + vout.to_bytes(4, "little") + compact_size(len(script_sig)) + script_sig + sequence.to_bytes(4, "little")


def serialize_output(amount: int, script_pubkey: bytes) -> bytes:
    return amount.to_bytes(8, "little") + compact_size(len(script_pubkey)) + script_pubkey


def sign_transaction_digest(private_key: ec.EllipticCurvePrivateKey, digest: bytes) -> bytes:
    """Sign a 32-byte transaction digest, normalizing the ECDSA S value."""
    from cryptography.hazmat.primitives.asymmetric.utils import Prehashed

    der = private_key.sign(digest, ec.ECDSA(Prehashed(hashes.SHA256())))
    r_value, s_value = decode_dss_signature(der)
    if s_value > SECP256K1_ORDER // 2:
        s_value = SECP256K1_ORDER - s_value
    return encode_dss_signature(r_value, s_value)


def build_transaction(arguments: argparse.Namespace) -> str:
    """Validate arguments, build, sign, and return a serialized transaction."""
    txid_str = arguments.txid
    vout = arguments.vout
    input_sats = arguments.input_sats

    # Auto-fetch UTXO from mempool.space if txid/vout/input_sats not provided
    if txid_str is None or vout is None or input_sats is None:
        if txid_str is not None or vout is not None or input_sats is not None:
            raise TransactionError("Either provide all of --txid, --vout, and --input-sats, or none of them (for auto-fetch from mempool.space)")

        utxos = fetch_utxos(arguments.source, arguments.network)
        if not utxos:
            raise TransactionError(f"No UTXOs found for address {arguments.source} on {arguments.network}")

        # Sort by value descending (use largest UTXO by default)
        sorted_utxos = sorted(utxos, key=lambda u: u['value'], reverse=True)
        if arguments.utxo_index >= len(sorted_utxos):
            raise TransactionError(f"UTXO index {arguments.utxo_index} out of range (found {len(sorted_utxos)} UTXOs)")

        selected_utxo = sorted_utxos[arguments.utxo_index]
        txid_str = selected_utxo['txid']
        vout = selected_utxo['vout']
        input_sats = selected_utxo['value']
        print(f"Auto-selected UTXO: txid={txid_str}, vout={vout}, value={input_sats} sats", file=sys.stderr)

    try:
        txid = bytes.fromhex(txid_str)
    except ValueError as error:
        raise TransactionError("--txid must be hexadecimal") from error
    if len(txid) != 32:
        raise TransactionError("--txid must be exactly 32 bytes (64 hex characters)")
    if vout < 0 or input_sats <= 0 or arguments.fee_sats < 0:
        raise TransactionError("vout, amounts, and fee must be non-negative; amounts must be positive")
    
    # Auto-calculate amount_sats if not provided (send all available funds minus fee)
    if arguments.amount_sats is None:
        arguments.amount_sats = input_sats - arguments.fee_sats
    
    if arguments.amount_sats <= 0:
        raise TransactionError("amount must be positive")
    if input_sats < arguments.amount_sats + arguments.fee_sats:
        raise TransactionError("input value is smaller than amount plus fee")

    private_key, compressed_wif = private_key_from_text(arguments.private_key, arguments.network)
    if not compressed_wif:
        raise TransactionError("uncompressed WIF keys are not supported; use a compressed WIF or hex key")
    public_key = compressed_public_key(private_key)
    source = decode_address(arguments.source, arguments.network)
    if source.payload != hash160(public_key):
        raise TransactionError("--source does not correspond to the supplied private key")
    destination = decode_address(arguments.destination, arguments.network)
    change = input_sats - arguments.amount_sats - arguments.fee_sats
    outputs = [serialize_output(arguments.amount_sats, destination.script_pubkey())]
    if change:
        if change < DUST_LIMIT_SATOSHIS:
            raise TransactionError(f"change of {change} sats is dust; increase --fee-sats or use a different amount")
        change_address = decode_address(arguments.change_address or arguments.source, arguments.network)
        outputs.append(serialize_output(change, change_address.script_pubkey()))

    version = (2).to_bytes(4, "little")
    sequence = 0xFFFFFFFF
    locktime = (0).to_bytes(4, "little")
    previous_script = source.script_pubkey()
    if source.kind == "p2pkh":
        signing_input = serialize_input(txid, vout, previous_script, sequence)
        preimage = version + b"\x01" + signing_input + compact_size(len(outputs)) + b"".join(outputs) + locktime + SIGHASH_ALL.to_bytes(4, "little")
        signature = sign_transaction_digest(private_key, double_sha256(preimage)) + bytes([SIGHASH_ALL])
        script_sig = push_data(signature) + push_data(public_key)
        transaction = version + b"\x01" + serialize_input(txid, vout, script_sig, sequence) + compact_size(len(outputs)) + b"".join(outputs) + locktime
    else:
        hash_prevouts = double_sha256(txid[::-1] + vout.to_bytes(4, "little"))
        hash_sequence = double_sha256(sequence.to_bytes(4, "little"))
        hash_outputs = double_sha256(b"".join(outputs))
        script_code = b"\x19\x76\xa9\x14" + source.payload + b"\x88\xac"
        preimage = version + hash_prevouts + hash_sequence + txid[::-1] + vout.to_bytes(4, "little") + script_code + input_sats.to_bytes(8, "little") + sequence.to_bytes(4, "little") + hash_outputs + locktime + SIGHASH_ALL.to_bytes(4, "little")
        signature = sign_transaction_digest(private_key, double_sha256(preimage)) + bytes([SIGHASH_ALL])
        marker_and_flag = b"\x00\x01"
        unsigned_input = serialize_input(txid, vout, b"", sequence)
        witness = b"\x02" + push_data(signature) + push_data(public_key)
        transaction = version + marker_and_flag + b"\x01" + unsigned_input + compact_size(len(outputs)) + b"".join(outputs) + witness + locktime
    return transaction.hex()


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-key", required=True, help="32-byte hex private key or network-appropriate WIF")
    parser.add_argument("--source", required=True, help="Funded P2PKH or P2WPKH address belonging to --private-key")
    parser.add_argument("--txid", help="Transaction ID containing the UTXO (display-order hex). Auto-fetched from mempool.space if not provided")
    parser.add_argument("--vout", type=int, help="Output index of the UTXO. Auto-fetched from mempool.space if not provided")
    parser.add_argument("--input-sats", type=int, help="UTXO value in satoshis. Auto-fetched from mempool.space if not provided")
    parser.add_argument("--utxo-index", type=int, default=0, help="Index of UTXO to use when auto-fetching (default: 0, largest value UTXO)")
    parser.add_argument("--destination", required=True, help="Recipient P2PKH or P2WPKH address")
    parser.add_argument("--amount-sats", type=int, default=None, help="Amount to recipient in satoshis (default: all available funds minus fee)")
    parser.add_argument("--fee-sats", type=int, default=1000, help="Miner fee in satoshis (default: 1000)")
    parser.add_argument("--change-address", help="P2PKH/P2WPKH change address; defaults to --source")
    parser.add_argument("--network", choices=("mainnet", "testnet"), default="testnet")
    return parser


def main() -> int:
    """Run the command-line interface."""
    arguments = build_parser().parse_args()
    try:
        transaction_hex = build_transaction(arguments)
    except TransactionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(transaction_hex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
