import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const contract = await ethers.deployContract("AcademicCredential");
  await contract.waitForDeployment();

  console.log("Smart contract berhasil di-deploy!");
  console.log("Contract address:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});