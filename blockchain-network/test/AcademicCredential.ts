
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
});
