from web3 import Web3

from evm_blockchain.web3_client import (
    w3,
    contract,
    send_contract_transaction
)

credential_id = "CRD-BLOCKCHAIN-002"
credential_data = "Kredensial dummy untuk uji transaksi Python"
credential_hash = Web3.keccak(text=credential_data)

print("=== UJI TRANSAKSI PYTHON ===")
print("Owner:", contract.functions.owner().call())

existing = contract.functions.getCredential(credential_id).call()

if existing[4]:
    print("ID sudah digunakan. Ganti credential_id dengan ID baru.")
else:
    receipt = send_contract_transaction(
        contract.functions.issueCredential(
            credential_id,
            credential_hash
        )
    )

    print("Penerbitan berhasil.")
    print("Transaction hash:", receipt.transactionHash.hex())

    valid = contract.functions.verifyCredential(
        credential_id,
        credential_hash
    ).call()

    print("Verifikasi hash benar:", valid)

    wrong_hash = Web3.keccak(text="Hash yang salah")

    invalid = contract.functions.verifyCredential(
        credential_id,
        wrong_hash
    ).call()

    print("Verifikasi hash salah:", invalid)