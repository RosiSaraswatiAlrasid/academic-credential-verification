import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { network } from "hardhat";
import {
  ZeroHash,
  concat,
  keccak256,
  randomBytes,
  toUtf8Bytes,
} from "ethers";

describe("Security regression tests", async function () {
  const { ethers } = await network.connect();

  async function deployContract() {
    const contract = await ethers.deployContract("AcademicCredential");
    await contract.waitForDeployment();
    return contract;
  }

  function hash(data: string) {
    return keccak256(toUtf8Bytes(data));
  }

  it("[SEC] attacker cannot issue, revoke, or transfer ownership", async function () {
    const contract = await deployContract();
    const [, attacker, newOwner] = await ethers.getSigners();
    const credentialId = "SEC-AUTH-001";

    await (await contract.issueCredential(credentialId, hash("credential"))).wait();

    await assert.rejects(
      contract.connect(attacker).issueCredential("SEC-ATTACK-001", hash("attack"))
    );
    await assert.rejects(
      contract.connect(attacker).revokeCredential(credentialId)
    );
    await assert.rejects(
      contract.connect(attacker).transferOwnership(newOwner.address)
    );
  });

  it("[SEC] attacker cannot accept ownership without being pending owner", async function () {
    const contract = await deployContract();
    const [, attacker, pendingOwner] = await ethers.getSigners();

    await (await contract.transferOwnership(pendingOwner.address)).wait();

    await assert.rejects(
      contract.connect(attacker).acceptOwnership()
    );
    assert.equal(await contract.owner(), (await ethers.getSigners())[0].address);
  });

  it("[SEC] attacker cannot squat on an ID that the owner intends to use", async function () {
    const contract = await deployContract();
    const [, attacker] = await ethers.getSigners();
    const intendedId = "SEC-INTENDED-CREDENTIAL";
    const credentialHash = hash("intended credential");

    await assert.rejects(
      contract.connect(attacker).issueCredential(intendedId, credentialHash)
    );
    await (await contract.issueCredential(intendedId, credentialHash)).wait();

    assert.equal(await contract.verifyCredential(intendedId, credentialHash), true);
  });

  it("[SEC] revoked IDs cannot be reissued and remain unverifiable", async function () {
    const contract = await deployContract();
    const credentialId = "SEC-REVOKED-001";
    const credentialHash = hash("revoked credential");

    await (await contract.issueCredential(credentialId, credentialHash)).wait();
    await (await contract.revokeCredential(credentialId)).wait();

    await assert.rejects(
      contract.issueCredential(credentialId, hash("replacement credential")),
      /Credential already exists/
    );
    assert.equal(await contract.verifyCredential(credentialId, credentialHash), false);
  });

  it("[SEC] empty ID, zero hash, duplicate ID, and repeated revocation revert", async function () {
    const contract = await deployContract();
    const credentialId = "SEC-VALIDATION-001";
    const credentialHash = hash("valid credential");

    await assert.rejects(
      contract.issueCredential("", credentialHash),
      /Credential ID is required/
    );
    await assert.rejects(
      contract.issueCredential("SEC-ZERO-HASH", ZeroHash),
      /Hash is required/
    );

    await (await contract.issueCredential(credentialId, credentialHash)).wait();
    await assert.rejects(
      contract.issueCredential(credentialId, hash("duplicate")),
      /Credential already exists/
    );

    await (await contract.revokeCredential(credentialId)).wait();
    await assert.rejects(
      contract.revokeCredential(credentialId),
      /Credential already revoked/
    );
  });

  it("[SEC] previous owner cannot issue or revoke after two-step transfer", async function () {
    const contract = await deployContract();
    const [oldOwner, newOwner] = await ethers.getSigners();
    const existingId = "SEC-OLD-OWNER-CREDENTIAL";

    await (await contract.issueCredential(existingId, hash("existing"))).wait();
    await (await contract.transferOwnership(newOwner.address)).wait();
    await (await contract.connect(newOwner).acceptOwnership()).wait();

    await assert.rejects(
      contract.connect(oldOwner).issueCredential("SEC-OLD-OWNER-NEW", hash("new"))
    );
    await assert.rejects(
      contract.connect(oldOwner).revokeCredential(existingId)
    );
    await (await contract.connect(newOwner).issueCredential("SEC-NEW-OWNER", hash("new owner"))).wait();
    await (await contract.connect(newOwner).revokeCredential("SEC-NEW-OWNER")).wait();
  });

  it("[SEC] credential events can be filtered by credentialIdHash", async function () {
    const contract = await deployContract();
    const targetId = "SEC-FILTER-TARGET";
    const otherId = "SEC-FILTER-OTHER";
    const targetIdHash = hash(targetId);

    await (await contract.issueCredential(targetId, hash("target"))).wait();
    await (await contract.issueCredential(otherId, hash("other"))).wait();
    await (await contract.revokeCredential(targetId)).wait();
    await (await contract.revokeCredential(otherId)).wait();

    const issued = await contract.queryFilter(
      contract.filters.CredentialIssued(undefined, targetIdHash)
    );
    const revoked = await contract.queryFilter(
      contract.filters.CredentialRevoked(undefined, targetIdHash)
    );

    assert.equal(issued.length, 1);
    assert.equal(issued[0].args.credentialId, targetId);
    assert.equal(issued[0].args.credentialIdHash, targetIdHash);
    assert.equal(revoked.length, 1);
    assert.equal(revoked[0].args.credentialId, targetId);
    assert.equal(revoked[0].args.credentialIdHash, targetIdHash);
  });

  it("[SEC] unsalted hashes are recoverable while random 32-byte salt blocks the same search", async function () {
    const name = "Synthetic Test Person";
    const gpa = "3.75";
    const targetNim = "000000000731";
    const unsaltedTarget = hash(`${targetNim}|${name}|${gpa}`);
    const salt = randomBytes(32);
    const saltedTarget = keccak256(
      concat([salt, toUtf8Bytes(`${targetNim}|${name}|${gpa}`)])
    );
    let recoveredNim: string | undefined;
    let recoveredSaltedNim: string | undefined;

    for (let index = 0; index < 1000; index += 1) {
      const nim = index.toString().padStart(12, "0");
      const candidate = hash(`${nim}|${name}|${gpa}`);

      if (candidate === unsaltedTarget) {
        recoveredNim = nim;
      }

      if (candidate === saltedTarget) {
        recoveredSaltedNim = nim;
      }
    }

    assert.equal(recoveredNim, targetNim);
    assert.equal(recoveredSaltedNim, undefined);
  });
});
