
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { network } from "hardhat";
import { keccak256, toUtf8Bytes } from "ethers";

describe("AcademicCredential", async function () {
  const { ethers } = await network.connect();

  async function deployContract() {
    const contract = await ethers.deployContract("AcademicCredential");
    await contract.waitForDeployment();
    return contract;
  }

  function createHash(data: string) {
    return keccak256(toUtf8Bytes(data));
  }

  // 1. Skenario positif: penerbitan dan verifikasi berhasil
  it("menerbitkan dan memverifikasi kredensial valid", async function () {
    const contract = await deployContract();
    const credentialId = "CRD-TEST001";
    const credentialHash = createHash("data-kredensial-dummy");

    await (await contract.issueCredential(
      credentialId,
      credentialHash
    )).wait();

    assert.equal(
      await contract.verifyCredential(credentialId, credentialHash),
      true
    );

    const credential = await contract.getCredential(credentialId);
    assert.equal(credential.exists, true);
    assert.equal(credential.credentialHash, credentialHash);
  });

  // 2. Skenario negatif: hash tidak cocok
  it("menolak hash yang salah", async function () {
    const contract = await deployContract();
    const credentialId = "CRD-TEST002";

    const originalHash = createHash("data-asli");
    const wrongHash = createHash("data-berbeda");

    await (await contract.issueCredential(
      credentialId,
      originalHash
    )).wait();

    assert.equal(
      await contract.verifyCredential(credentialId, wrongHash),
      false
    );
  });

  // 3. Skenario negatif: kredensial telah dicabut
  it("menolak kredensial yang sudah dicabut", async function () {
    const contract = await deployContract();
    const credentialId = "CRD-TEST003";
    const credentialHash = createHash("data-kredensial");

    await (await contract.issueCredential(
      credentialId,
      credentialHash
    )).wait();

    await (await contract.revokeCredential(credentialId)).wait();

    assert.equal(
      await contract.verifyCredential(credentialId, credentialHash),
      false
    );

    const credential = await contract.getCredential(credentialId);
    assert.ok(credential.revokedAt > 0n);
  });

  // 4. Skenario batas: ID kosong
  it("menolak penerbitan dengan ID kosong", async function () {
    const contract = await deployContract();
    const credentialHash = createHash("data-kredensial");

    await assert.rejects(
      contract.issueCredential("", credentialHash)
    );
  });

  // 5. Skenario batas: hash kosong
  it("menolak penerbitan dengan hash kosong", async function () {
    const contract = await deployContract();
    const zeroHash = "0x" + "00".repeat(32);

    await assert.rejects(
      contract.issueCredential("CRD-TEST005", zeroHash)
    );
  });

  // 6. Mencegah ID kredensial duplikat
  it("menolak penerbitan dengan ID yang sudah digunakan", async function () {
    const contract = await deployContract();
    const credentialId = "CRD-TEST006";
    const credentialHash = createHash("data-asli");

    await (await contract.issueCredential(
      credentialId,
      credentialHash
    )).wait();

    await assert.rejects(
      contract.issueCredential(
        credentialId,
        createHash("data-lain")
      )
    );
  });

  // 7. Kontrol akses: hanya pemilik yang dapat menerbitkan
  it("menolak penerbitan oleh akun selain pemilik", async function () {
    const contract = await deployContract();
    const [, otherAccount] = await ethers.getSigners();

    await assert.rejects(
      contract.connect(otherAccount).issueCredential(
        "CRD-TEST007",
        createHash("data-kredensial")
      )
    );
  });

  // 8. Kontrol akses: hanya pemilik yang dapat mencabut
  it("menolak pencabutan oleh akun selain pemilik", async function () {
    const contract = await deployContract();
    const [, otherAccount] = await ethers.getSigners();
    const credentialId = "CRD-TEST008";
    const credentialHash = createHash("data-kredensial");

    await (await contract.issueCredential(
      credentialId,
      credentialHash
    )).wait();

    await assert.rejects(
      contract.connect(otherAccount).revokeCredential(credentialId)
    );

    assert.equal(
      await contract.verifyCredential(credentialId, credentialHash),
      true
    );
  });

  // 9. Menolak pencabutan ID yang tidak terdaftar
  it("menolak pencabutan kredensial yang tidak ditemukan", async function () {
    const contract = await deployContract();

    await assert.rejects(
      contract.revokeCredential("CRD-TIDAK-ADA")
    );
  });

  // 10. Menolak pencabutan berulang
  it("menolak pencabutan kredensial untuk kedua kalinya", async function () {
    const contract = await deployContract();
    const credentialId = "CRD-TEST010";

    await (await contract.issueCredential(
      credentialId,
      createHash("data-kredensial")
    )).wait();

    await (await contract.revokeCredential(credentialId)).wait();

    await assert.rejects(
      contract.revokeCredential(credentialId)
    );
  });

  it("menolak transfer kepemilikan oleh non-owner", async function () {
    const contract = await deployContract();
    const [, otherAccount, newOwner] = await ethers.getSigners();

    await assert.rejects(
      contract.connect(otherAccount).transferOwnership(newOwner.address)
    );
  });

  it("hanya pendingOwner yang dapat menerima kepemilikan", async function () {
    const contract = await deployContract();
    const [currentOwner, pendingOwner, otherAccount] = await ethers.getSigners();

    await (await contract.transferOwnership(pendingOwner.address)).wait();

    await assert.rejects(
      contract.connect(otherAccount).acceptOwnership()
    );
    assert.equal(await contract.owner(), currentOwner.address);

    await (await contract.connect(pendingOwner).acceptOwnership()).wait();
    assert.equal(await contract.owner(), pendingOwner.address);
    assert.equal(await contract.pendingOwner(), "0x0000000000000000000000000000000000000000");
  });

  it("owner lama kehilangan akses dan owner baru dapat mengelola kredensial", async function () {
    const contract = await deployContract();
    const [oldOwner, newOwner] = await ethers.getSigners();
    const oldCredentialId = "CRD-OLD-OWNER";
    const credentialId = "CRD-NEW-OWNER";
    const credentialHash = createHash("data-kredensial-owner-baru");

    await (await contract.issueCredential(
      oldCredentialId,
      credentialHash
    )).wait();
    await (await contract.transferOwnership(newOwner.address)).wait();
    await (await contract.connect(newOwner).acceptOwnership()).wait();

    await assert.rejects(
      contract.connect(oldOwner).issueCredential(
        "CRD-OLD-OWNER-2",
        credentialHash
      )
    );
    await assert.rejects(
      contract.connect(oldOwner).revokeCredential(oldCredentialId)
    );

    await (await contract.connect(newOwner).issueCredential(
      credentialId,
      credentialHash
    )).wait();
    await (await contract.connect(newOwner).revokeCredential(credentialId)).wait();

    assert.equal(await contract.owner(), newOwner.address);
    assert.ok((await contract.getCredential(credentialId)).revokedAt > 0n);
    assert.equal((await contract.getCredential(oldCredentialId)).revokedAt, 0n);
  });

  it("menolak address(0) sebagai owner baru", async function () {
    const contract = await deployContract();

    await assert.rejects(
      contract.transferOwnership(
        "0x0000000000000000000000000000000000000000"
      )
    );
    assert.notEqual(
      await contract.owner(),
      "0x0000000000000000000000000000000000000000"
    );
  });

  it("mengemit event ownership saat constructor, transfer, dan accept", async function () {
    const contract = await deployContract();
    const [currentOwner, newOwner] = await ethers.getSigners();
    const deploymentReceipt = await contract.deploymentTransaction()?.wait();
    assert.ok(deploymentReceipt);

    const constructorEvents = await contract.queryFilter(
      contract.filters.OwnershipTransferred(),
      deploymentReceipt.blockNumber,
      deploymentReceipt.blockNumber
    );
    assert.equal(constructorEvents.length, 1);
    assert.equal(
      constructorEvents[0].args.previousOwner,
      "0x0000000000000000000000000000000000000000"
    );
    assert.equal(constructorEvents[0].args.newOwner, currentOwner.address);

    const transferReceipt = await (
      await contract.transferOwnership(newOwner.address)
    ).wait();
    assert.ok(transferReceipt);
    const startedEvents = await contract.queryFilter(
      contract.filters.OwnershipTransferStarted(),
      transferReceipt.blockNumber,
      transferReceipt.blockNumber
    );
    assert.equal(startedEvents.length, 1);
    assert.equal(startedEvents[0].args.previousOwner, currentOwner.address);
    assert.equal(startedEvents[0].args.newOwner, newOwner.address);

    const acceptReceipt = await (
      await contract.connect(newOwner).acceptOwnership()
    ).wait();
    assert.ok(acceptReceipt);
    const transferredEvents = await contract.queryFilter(
      contract.filters.OwnershipTransferred(),
      acceptReceipt.blockNumber,
      acceptReceipt.blockNumber
    );
    assert.equal(transferredEvents.length, 1);
    assert.equal(transferredEvents[0].args.previousOwner, currentOwner.address);
    assert.equal(transferredEvents[0].args.newOwner, newOwner.address);
  });
});
