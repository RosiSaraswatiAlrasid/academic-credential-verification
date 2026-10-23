
import hashlib
import json
import sqlite3
from datetime import datetime, timezone


class Blockchain:
    def __init__(self, database_path):
        self.database_path = str(database_path)
        self.chain = []
        self.pending_transactions = []
        self.load_chain()

        if not self.chain:
            self.create_block(
                previous_hash="0",
                transactions=[],
                proof=100
            )

    def connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def calculate_hash(self, data):
        encoded_data = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")

        return hashlib.sha256(encoded_data).hexdigest()

    def load_chain(self):
        with self.connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    block_index INTEGER PRIMARY KEY,
                    block_data TEXT NOT NULL,
                    block_hash TEXT NOT NULL UNIQUE
                )
            """)

            rows = connection.execute("""
                SELECT block_index, block_data, block_hash
                FROM blocks
                ORDER BY block_index ASC
            """).fetchall()

        loaded_chain = []

        for row in rows:
            block_index, block_data, stored_hash = row

            try:
                block = json.loads(block_data)

                if not isinstance(block, dict):
                    raise ValueError("Format blok tidak valid.")

                if block.get("index") != block_index:
                    raise ValueError("Indeks blok tidak cocok.")

                if block.get("hash") != stored_hash:
                    raise ValueError("Hash blok di database tidak cocok.")

                loaded_chain.append(block)

            except (json.JSONDecodeError, TypeError, ValueError) as error:
                raise ValueError(
                    f"Data blok ke-{block_index} rusak: {error}"
                ) from error

        self.chain = loaded_chain

    def create_block(self, previous_hash, transactions, proof):
        if not isinstance(transactions, list):
            raise TypeError("Transaksi harus berupa list.")

        block = {
            "index": len(self.chain) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transactions": transactions,
            "proof": proof,
            "previous_hash": previous_hash
        }

        block["hash"] = self.calculate_hash(block)

        serialized_block = json.dumps(
            block,
            sort_keys=True,
            ensure_ascii=False
        )

        with self.connect() as connection:
            connection.execute("""
                INSERT INTO blocks (
                    block_index,
                    block_data,
                    block_hash
                )
                VALUES (?, ?, ?)
            """, (
                block["index"],
                serialized_block,
                block["hash"]
            ))

        self.chain.append(block)
        return block

    def add_transaction(self, transaction):
        if not isinstance(transaction, dict):
            raise TypeError("Transaksi harus berupa dictionary.")

        required_fields = {"type", "credential_id"}

        if not required_fields.issubset(transaction):
            raise ValueError("Data transaksi belum lengkap.")

        self.pending_transactions.append(
            transaction.copy()
        )

    def mine_block(self):
        if not self.pending_transactions:
            return None

        if not self.is_chain_valid():
            raise ValueError(
                "Blok tidak dapat ditambahkan karena rantai tidak valid."
            )

        previous_hash = self.chain[-1]["hash"]
        transactions = [
            transaction.copy()
            for transaction in self.pending_transactions
        ]

        block = self.create_block(
            previous_hash=previous_hash,
            transactions=transactions,
            proof=100
        )

        del self.pending_transactions[:len(transactions)]

        return block

    def is_chain_valid(self):
        if not self.chain:
            return False

        expected_index = 1

        for index, block in enumerate(self.chain):
            if not isinstance(block, dict):
                return False

            required_fields = {
                "index",
                "timestamp",
                "transactions",
                "proof",
                "previous_hash",
                "hash"
            }

            if not required_fields.issubset(block):
                return False

            if block["index"] != expected_index:
                return False

            if not isinstance(block["transactions"], list):
                return False

            block_data = block.copy()
            stored_hash = block_data.pop("hash")

            if not isinstance(stored_hash, str):
                return False

            if stored_hash != self.calculate_hash(block_data):
                return False

            if index == 0:
                if block["previous_hash"] != "0":
                    return False
            else:
                previous_block = self.chain[index - 1]

                if block["previous_hash"] != previous_block["hash"]:
                    return False

            expected_index += 1

        try:
            with self.connect() as connection:
                rows = connection.execute("""
                    SELECT block_index, block_data, block_hash
                    FROM blocks
                    ORDER BY block_index ASC
                """).fetchall()

            if len(rows) != len(self.chain):
                return False

            for row, block in zip(rows, self.chain):
                db_index, db_data, db_hash = row

                if db_index != block["index"]:
                    return False

                if db_hash != block["hash"]:
                    return False

                if json.loads(db_data) != block:
                    return False

        except (sqlite3.Error, json.JSONDecodeError, TypeError):
            return False

        return True

    def contains_transaction(
        self,
        transaction_type,
        credential_id,
        credential_hash=None
    ):
        for block in self.chain:
            for transaction in block.get("transactions", []):
                if not isinstance(transaction, dict):
                    continue

                if (
                    transaction.get("type") == transaction_type
                    and transaction.get("credential_id") == credential_id
                    and (
                        credential_hash is None
                        or transaction.get("credential_hash")
                        == credential_hash
                    )
                ):
                    return True

        return False
