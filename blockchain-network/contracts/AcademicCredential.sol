
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract AcademicCredential {
    /// @notice The address currently authorized to manage credentials.
    address public owner;

    /// @notice The address proposed to become the owner.
    address public pendingOwner;

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

    /// @notice Emitted when the current owner proposes a new owner.
    /// @param previousOwner The current owner who initiated the transfer.
    /// @param newOwner The proposed owner who must accept the transfer.
    event OwnershipTransferStarted(
        address indexed previousOwner,
        address indexed newOwner
    );

    /// @notice Emitted when ownership changes.
    /// @param previousOwner The address that previously owned the contract.
    /// @param newOwner The address that now owns the contract.
    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );

    /// @notice Sets the deployer as the initial owner.
    /// @dev The initial owner cannot be the zero address.
    constructor() {
        require(msg.sender != address(0), "Owner cannot be zero address");
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    /// @notice Proposes a new owner; the proposed address must accept.
    /// @param newOwner The address proposed to take ownership.
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "New owner cannot be zero address");
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    /// @notice Accepts ownership as the pending owner.
    function acceptOwnership() external {
        require(msg.sender == pendingOwner, "Caller is not the pending owner");

        address previousOwner = owner;
        owner = msg.sender;
        pendingOwner = address(0);

        emit OwnershipTransferred(previousOwner, msg.sender);
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
