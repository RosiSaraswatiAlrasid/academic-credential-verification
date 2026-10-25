import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash

from blockchain import Blockchain
from evm_blockchain.web3_client import (
    w3,
    check_connection,
    contract,
    send_contract_transaction,
    get_onchain_credential,
    verify_onchain_credential
)


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

Path(app.instance_path).mkdir(parents=True, exist_ok=True)
DATABASE_PATH = Path(app.instance_path) / "academic.db"


def connect_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                credential_id TEXT PRIMARY KEY,
                credential_data TEXT NOT NULL
            )
        """)


initialize_database()
blockchain = Blockchain(DATABASE_PATH)


def load_credentials():
    with connect_db() as connection:
        rows = connection.execute("""
            SELECT credential_id, credential_data
            FROM credentials
        """).fetchall()

    return {
        row["credential_id"]: json.loads(row["credential_data"])
        for row in rows
    }


credentials = load_credentials()


def save_credential(credential):
    with connect_db() as connection:
        connection.execute("""
            INSERT INTO credentials (
                credential_id,
                credential_data
            )
            VALUES (?, ?)
            ON CONFLICT(credential_id)
            DO UPDATE SET credential_data = excluded.credential_data
        """, (
            credential["credential_id"],
            json.dumps(credential, ensure_ascii=False)
        ))


def hash_credential(data):
    encoded_data = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

    return hashlib.sha256(encoded_data).hexdigest()


def get_credential_data(credential):
    data = {
        "credential_id": credential["credential_id"],
        "student_name": credential["student_name"],
        "student_id": credential["student_id"],
        "credential_type": credential["credential_type"],
        "institution": credential["institution"],
        "graduation_year": credential["graduation_year"]
    }

    # Salt acak 32 byte (S-02). Disimpan hanya di SQLite, tidak pernah
    # dikirim ke blockchain. Kredensial lama tanpa salt tetap dapat
    # diverifikasi (kompatibilitas mundur).
    if credential.get("salt"):
        data["salt"] = credential["salt"]

    return data


def get_onchain_status(credential_id, credential_hash):
    data = get_onchain_credential(credential_id)

    onchain_hash, issuer, issued_at, revoked_at, exists = data

    stored_hash = (
        onchain_hash.hex().lower()
        if isinstance(onchain_hash, bytes)
        else str(onchain_hash).removeprefix("0x").lower()
    )

    hash_matches = (
        exists
        and stored_hash == credential_hash.lower()
    )

    revoked = exists and revoked_at != 0

    valid = (
        exists
        and hash_matches
        and not revoked
    )

    return {
        "exists": exists,
        "hash_matches": hash_matches,
        "revoked": revoked,
        "valid": valid,
        "issuer": issuer,
        "issued_at": issued_at,
        "revoked_at": revoked_at
    }

def verify_credential(credential_id):
    credential = credentials.get(credential_id)
    chain_valid = blockchain.is_chain_valid()

    if credential is None:
        return {
            "not_found": True,
            "valid": False,
            "chain_valid": chain_valid,
            "reason": "not_found",
            "message": "Kredensial tidak ditemukan."
        }

    credential_data = get_credential_data(credential)
    calculated_hash = hash_credential(credential_data)

    local_hash_matches = (
        calculated_hash == credential.get("credential_hash")
    )

    issuance_recorded = blockchain.contains_transaction(
        transaction_type="ISSUE_CREDENTIAL",
        credential_id=credential_id,
        credential_hash=credential.get("credential_hash")
    )

    revocation_recorded = blockchain.contains_transaction(
        transaction_type="REVOKE_CREDENTIAL",
        credential_id=credential_id,
        credential_hash=credential.get("credential_hash")
    )

    try:
        onchain = get_onchain_status(
            credential_id,
            credential.get("credential_hash", "")
        )
        onchain_error = None
    except Exception:
        app.logger.exception(
            "Gagal memverifikasi kredensial on-chain"
        )
        onchain = {
            "exists": False,
            "hash_matches": False,
            "revoked": False,
            "valid": False,
            "issuer": None,
            "issued_at": 0,
            "revoked_at": 0
        }
        onchain_error = "Blockchain tidak dapat diverifikasi."

    local_status_valid = (
        credential.get("status") == "Aktif"
        and not revocation_recorded
    )

    valid = (
        chain_valid
        and issuance_recorded
        and local_hash_matches
        and local_status_valid
        and onchain["valid"]
    )


    if onchain_error:
        reason = "blockchain_unavailable"
        message = onchain_error
    elif not chain_valid:
        reason = "chain_invalid"
        message = "Integritas rantai blok lokal tidak valid."
    elif not onchain["exists"]:
        reason = "onchain_missing"
        message = "Kredensial tidak ditemukan pada smart contract yang sedang digunakan."
    elif not local_hash_matches or not onchain["hash_matches"]:
        reason = "hash_mismatch"
        message = "Hash kredensial tidak cocok. Data mungkin telah berubah."
    elif not issuance_recorded:
        reason = "issuance_missing"
        message = "Transaksi penerbitan tidak ditemukan pada rantai lokal."
    elif credential.get("status") == "Dicabut" or onchain["revoked"]:
        reason = "revoked"
        message = "Kredensial sudah dicabut."
    elif not valid:
        reason = "invalid"
        message = "Kredensial tidak memenuhi pemeriksaan validitas."
    else:
        reason = "valid"
        message = "Kredensial aktif dan seluruh pemeriksaan berhasil."


    return {
        "credential": credential,
        "valid": valid,
        "chain_valid": chain_valid,
        "issuance_recorded": issuance_recorded,
        "hash_matches": local_hash_matches,
        "revocation_recorded": revocation_recorded,
        "onchain": onchain,
        "onchain_error": onchain_error,
        "reason": reason,
        "message": message
    }


@app.route("/")
def index():
    search_id = request.args.get("credential_id", "").strip()
    verification = None

    if search_id:
        verification = verify_credential(search_id)

    credential_list = list(reversed(list(credentials.values())))

    try:
        evm_connected = check_connection()
    except Exception:
        app.logger.exception("Gagal memeriksa koneksi blockchain")
        evm_connected = False

    return render_template(
        "index.html",
        credentials=credential_list,
        chain=list(reversed(blockchain.chain)),
        total_credentials=len(credentials),
        active_credentials=sum(
            1 for item in credentials.values()
            if item["status"] == "Aktif"
        ),
        total_blocks=len(blockchain.chain),
        chain_valid=blockchain.is_chain_valid(),
        verification=verification,
        evm_connected=evm_connected
    )


@app.route("/issue", methods=["POST"])
def issue_credential():
    student_name = request.form.get("student_name", "").strip()
    student_id = request.form.get("student_id", "").strip()
    credential_type = request.form.get("credential_type", "").strip()
    institution = request.form.get("institution", "").strip()
    graduation_year = request.form.get("graduation_year", "").strip()

    if not all([
        student_name,
        student_id,
        credential_type,
        institution,
        graduation_year
    ]):
        flash("Semua kolom wajib diisi.", "error")
        return redirect(url_for("index"))

    if (
        not graduation_year.isdigit()
        or len(graduation_year) != 4
        or not 1900 <= int(graduation_year) <= 2100
    ):
        flash("Tahun kelulusan harus empat digit antara 1900 dan 2100.", "error")
        return redirect(url_for("index"))

    if any(
        item["student_id"] == student_id
        and item["status"] == "Aktif"
        for item in credentials.values()
    ):
        flash(
            "NIM/NPM tersebut sudah memiliki kredensial aktif.",
            "error"
        )
        return redirect(url_for("index"))

    try:
        if not check_connection():
            flash("Jaringan blockchain lokal tidak tersedia.", "error")
            return redirect(url_for("index"))

        credential_id = "CRD-" + secrets.token_hex(4).upper()

        while (
            credential_id in credentials
            or contract.functions.getCredential(credential_id).call()[4]
        ):
            credential_id = "CRD-" + secrets.token_hex(4).upper()

        credential_data = {
            "credential_id": credential_id,
            "student_name": student_name,
            "student_id": student_id,
            "credential_type": credential_type,
            "institution": institution,
            "graduation_year": graduation_year,
            "salt": secrets.token_hex(32)
        }

        credential_hash = hash_credential(credential_data)
        timestamp = datetime.now(timezone.utc).isoformat()

        credential = {
            **credential_data,
            "credential_hash": credential_hash,
            "issued_at": timestamp,
            "status": "Aktif"
        }

        receipt = send_contract_transaction(
            contract.functions.issueCredential(
                credential_id,
                bytes.fromhex(credential_hash)
            )
        )

        credential["blockchain_tx_hash"] = receipt.transactionHash.hex()

        transaction = {
            "type": "ISSUE_CREDENTIAL",
            "credential_id": credential_id,
            "credential_hash": credential_hash,
            "institution": institution,
            "timestamp": timestamp,
            "blockchain_tx_hash": credential["blockchain_tx_hash"]
        }

        blockchain.add_transaction(transaction)
        block = blockchain.mine_block()

        if block is None:
            app.logger.error(
                "Transaksi EVM berhasil tetapi blok lokal gagal dibuat: %s",
                credential_id
            )
            flash(
                "Transaksi tercatat di blockchain, tetapi pencatatan "
                "lokal gagal. Periksa terminal sebelum mencoba ulang.",
                "error"
            )
            return redirect(url_for("index"))

        credential["block_index"] = block["index"]

        save_credential(credential)
        credentials[credential_id] = credential

    except Exception:
        app.logger.exception("Gagal menerbitkan kredensial")
        flash(
            "Penerbitan gagal atau belum lengkap. Periksa terminal "
            "dan status transaksi sebelum mencoba ulang.",
            "error"
        )
        return redirect(url_for("index"))

    flash(
        f"Kredensial berhasil diterbitkan. ID: {credential_id}",
        "success"
    )

    return redirect(url_for("index"))


@app.route("/revoke/<credential_id>", methods=["POST"])
def revoke_credential(credential_id):
    credential = credentials.get(credential_id)

    if not credential:
        flash("Kredensial tidak ditemukan.", "error")
        return redirect(url_for("index"))

    if credential["status"] == "Dicabut":
        flash("Kredensial ini sudah dicabut.", "error")
        return redirect(url_for("index"))

    try:
        if not check_connection():
            flash("Jaringan blockchain lokal tidak tersedia.", "error")
            return redirect(url_for("index"))

        onchain = get_onchain_status(
            credential_id,
            credential["credential_hash"]
        )

        if not onchain["exists"] or not onchain["hash_matches"]:
            flash(
                "Kredensial tidak ditemukan atau hash on-chain berbeda.",
                "error"
            )
            return redirect(url_for("index"))

        if onchain["revoked"]:
            flash(
                "Kredensial sudah dicabut di blockchain. "
                "Periksa sinkronisasi database lokal.",
                "error"
            )
            return redirect(url_for("index"))

        timestamp = datetime.now(timezone.utc).isoformat()

        receipt = send_contract_transaction(
            contract.functions.revokeCredential(credential_id)
        )

        revocation_tx_hash = receipt.transactionHash.hex()

        transaction = {
            "type": "REVOKE_CREDENTIAL",
            "credential_id": credential_id,
            "credential_hash": credential["credential_hash"],
            "timestamp": timestamp,
            "blockchain_tx_hash": revocation_tx_hash
        }

        blockchain.add_transaction(transaction)
        block = blockchain.mine_block()

        credential["status"] = "Dicabut"
        credential["revoked_at"] = timestamp
        credential["revocation_tx_hash"] = revocation_tx_hash

        if block is not None:
            credential["revocation_block_index"] = block["index"]

        save_credential(credential)
        credentials[credential_id] = credential

    except Exception:
        app.logger.exception("Gagal mencabut kredensial")
        flash(
            "Pencabutan gagal atau belum lengkap. Periksa status "
            "transaksi di blockchain dan database sebelum mencoba ulang.",
            "error"
        )
        return redirect(url_for("index"))

    flash("Kredensial berhasil dicabut.", "success")
    return redirect(url_for("index"))


@app.route("/chain")
def view_chain():
    return {
        "chain_valid": blockchain.is_chain_valid(),
        "total_blocks": len(blockchain.chain),
        "chain": blockchain.chain
    }


@app.route("/blockchain-status")
def blockchain_status():
    try:
        connected = check_connection()

        if not connected:
            return {
                "connected": False,
                "message": "Jaringan blockchain tidak tersedia."
            }, 503

        return {
            "connected": True,
            "network": "Hardhat Local",
            "chain_id": w3.eth.chain_id,
            "contract_address": contract.address,
            "owner": contract.functions.owner().call()
        }
    except Exception:
        app.logger.exception("Gagal membaca status blockchain")
        return {
            "connected": False,
            "message": "Gagal membaca status blockchain."
        }, 503


if __name__ == "__main__":
    app.run(debug=True)