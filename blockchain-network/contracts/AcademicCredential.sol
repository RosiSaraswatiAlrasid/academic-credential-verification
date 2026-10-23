
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract AcademicCredential {
    address public owner;

    struct Credential {
        bytes32 credentialHash;
        address issuer;
        uint256 issuedAt;
        uint256 revokedAt;
        bool exists;
    }

    mapping(string => Credential) private credentials;

    event CredentialIssued(
        string credentialId,
        bytes32 credentialHash,
        address indexed issuer
    );

    event CredentialRevoked(
        string credentialId,
        address indexed revoker
    );

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    function issueCredential(
        string calldata credentialId,
        bytes32 credentialHash
    ) external onlyOwner {
        require(bytes(credentialId).length > 0, "Credential ID is required");
        require(credentialHash != bytes32(0), "Hash is required");
        require(!credentials[credentialId].exists, "Credential already exists");

        credentials[credentialId] = Credential({
            credentialHash: credentialHash,
            issuer: msg.sender,
            issuedAt: block.timestamp,
            revokedAt: 0,
            exists: true
        });

        emit CredentialIssued(credentialId, credentialHash, msg.sender);
    }

    function verifyCredential(
        string calldata credentialId,
        bytes32 submittedHash
    ) external view returns (bool) {
        Credential storage credential = credentials[credentialId];

        return (
            credential.exists &&
            credential.revokedAt == 0 &&
            credential.credentialHash == submittedHash
        );
    }

    function revokeCredential(
        string calldata credentialId
    ) external onlyOwner {
        Credential storage credential = credentials[credentialId];

        require(credential.exists, "Credential not found");
        require(credential.revokedAt == 0, "Credential already revoked");

        credential.revokedAt = block.timestamp;

        emit CredentialRevoked(credentialId, msg.sender);
    }

    function getCredential(
        string calldata credentialId
    )
        external
        view
        returns (
            bytes32 credentialHash,
            address issuer,
            uint256 issuedAt,
            uint256 revokedAt,
            bool exists
        )
    {
        Credential storage credential = credentials[credentialId];

        return (
            credential.credentialHash,
            credential.issuer,
            credential.issuedAt,
            credential.revokedAt,
            credential.exists
        );
    }
}
