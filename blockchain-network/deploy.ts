
import { network } from "hardhat";
import { writeFile } from "node:fs/promises";
import path from "node:path";

async function main() {
  const { ethers } = await network.connect();

  console.log("Memulai deployment AcademicCredential...");

  const contract = await ethers.deployContract("AcademicCredential");
  const deploymentTx = contract.deploymentTransaction();

  if (!deploymentTx) {
    throw new Error("Transaksi deployment tidak ditemukan.");
  }

  const receipt = await deploymentTx.wait();

  if (!receipt || receipt.status !== 1) {
    throw new Error("Transaksi deployment gagal.");
  }

  const address = await contract.getAddress();
  const net = await ethers.provider.getNetwork();

  const record = `# Deployment Record

## Informasi Jaringan

- Network: Hardhat Local Network
- RPC URL: http://127.0.0.1:8545
- Chain ID: ${net.chainId.toString()}

## Informasi Smart Contract

- Nama kontrak: AcademicCredential
- Contract Address: ${address}

## Informasi Transaksi Deployment

- Transaction Hash: ${deploymentTx.hash}
- Block Number: ${receipt.blockNumber}
- Transaction Status: Success

## Catatan

Deployment dilakukan pada jaringan Hardhat lokal untuk pengujian.
Alamat kontrak dan transaction hash berlaku untuk jaringan saat deployment dilakukan.
Jika node Hardhat di-reset, lakukan deployment ulang dan perbarui konfigurasi alamat kontrak aplikasi.
`;

  const recordPath = path.resolve(
    process.cwd(),
    "..",
    "deployment-record.md"
  );

  await writeFile(recordPath, record, "utf8");

  console.log("\nDeployment berhasil!");
  console.log("Contract address:", address);
  console.log("Transaction hash:", deploymentTx.hash);
  console.log("Block number:", receipt.blockNumber);
  console.log("Status: Success");
  console.log("Deployment record diperbarui:", recordPath);
}

main().catch((error) => {
  console.error("Deployment gagal:", error);
  process.exitCode = 1;
});
