import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
ABI_PATH = BASE_DIR / "AcademicCredential_abi.json"

RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
)

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open(ABI_PATH, "r", encoding="utf-8") as file:
    contract_abi = json.load(file)

contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=contract_abi
)

def check_connection():
    return w3.is_connected()


def send_contract_transaction(function):
    if not w3.is_connected():
        raise ConnectionError("Tidak terhubung ke jaringan blockchain.")

    private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")

    if not private_key:
        raise RuntimeError(
            "Variabel BLOCKCHAIN_PRIVATE_KEY belum diatur."
        )

    account = w3.eth.account.from_key(private_key)

    owner = contract.functions.owner().call()

    if account.address.lower() != owner.lower():
        raise PermissionError(
            "Akun transaksi bukan pemilik smart contract."
        )

    transaction = function.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price
    })

    signed_transaction = w3.eth.account.sign_transaction(
        transaction,
        private_key=private_key
    )

    tx_hash = w3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise RuntimeError("Transaksi smart contract gagal.")

    return receipt

def get_onchain_credential(credential_id):
    if not check_connection():
        raise ConnectionError("Tidak terhubung ke jaringan blockchain.")

    return contract.functions.getCredential(credential_id).call()


def verify_onchain_credential(credential_id, credential_hash):
    if not check_connection():
        raise ConnectionError("Tidak terhubung ke jaringan blockchain.")

    submitted_hash = Web3.to_bytes(hexstr="0x" + credential_hash)

    return contract.functions.verifyCredential(
        credential_id,
        submitted_hash
    ).call()