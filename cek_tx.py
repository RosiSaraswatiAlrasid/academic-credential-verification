
import json
import sqlite3

db = sqlite3.connect("instance/academic.db")

cursor = db.execute(
    "SELECT credential_id, credential_data FROM credentials"
)

found = False

for credential_id, credential_data in cursor.fetchall():
    if credential_id == "CRD-A5A3EB21":
        data = json.loads(credential_data)

        print("Credential ID:", credential_id)
        print("Transaction hash:", data.get("blockchain_tx_hash"))

        found = True
        break

if not found:
    print("Kredensial tidak ditemukan.")

db.close()
